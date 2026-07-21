#!/usr/bin/env python3
"""Stream a prepared gesture trajectory (w1_prepare_traj.py output) to the real
CASBOT W1 over ROS2. Designed to run on the robot / lab PC with ROS2 sourced --
needs only rclpy + numpy, no mujoco, no conda env.

The command topic and the feedback-enable service are documented in the vendor's
"CASBOT W1 二次开发文档 V2.0" (p.13 and p.11-12); see OPERATING_GUIDE.md, which is
the step-by-step procedure this script is meant to be driven from.

    python stream_ros2.py --traj w1_traj.npz --dry-run          # rung 0, no commands
    python stream_ros2.py --traj w1_traj.npz --enable-feedback --test-nudge left_joint6
    python stream_ros2.py --traj w1_traj.npz --arms left --speed 0.25 --movej-first
    python stream_ros2.py --traj w1_traj.npz --speed 0.5 --movej-first
    python stream_ros2.py --traj w1_traj.npz --movej-first      # both arms, full speed
    python stream_ros2.py --discover                            # re-check topic names

Safety model (all checks run every tick):
  * ramp-in : cubic ease from the MEASURED pose to the first trajectory frame
  * ramp-out: cubic ease back to the initial measured pose at the end
  * watchdog: joint-state feedback older than --feedback-timeout -> abort
  * tracking: any joint further than --track-tol from its command -> abort
              (that is what a jam/collision/E-stop looks like from software)
  * abort   = stop publishing immediately (position servos hold last target);
    Ctrl-C does the same. The hardware E-stop always wins over software.
"""
import argparse
import sys
import time

import numpy as np

FEEDBACK_TOPIC = "/motion_unified/get/joint_state"
# Vendor dev doc V2.0 p.13: high-rate arm command channel, sensor_msgs/JointState,
# supported 50-200 Hz, positions must be continuous frame to frame.
COMMAND_TOPIC = "/motion_unified/control/Movej_transparent"
# Vendor dev doc V2.0 p.10-12, p.14: every one-shot request goes through this one
# service, dispatched by the `func_name` field.
CONTROL_SERVICE = "/motion_unified/control"
ALL_JOINTS = [f"{s}_joint{i}" for s in ("left", "right") for i in range(1, 8)]


def cubic(x):
    x = np.clip(x, 0.0, 1.0)
    return 3 * x * x - 2 * x * x * x


def ramp(q0, q1, n):
    s = cubic(np.linspace(0.0, 1.0, n))[:, None]
    return q0[None, :] * (1 - s) + q1[None, :] * s


def resample_speed(q, source_rate, command_rate, speed):
    """Traverse the same joint path at `speed`, sampled at fixed command Hz."""
    assert source_rate > 0.0
    assert 50.0 <= command_rate <= 200.0
    assert speed > 0.0
    source_t = np.arange(len(q)) / source_rate
    duration = source_t[-1] / speed
    # ceil guarantees that the final path pose is commanded. round could end
    # one command tick early when the duration lay below a half-tick boundary.
    target_t = np.arange(int(np.ceil(duration * command_rate)) + 1) / command_rate
    path_t = np.minimum(target_t * speed, source_t[-1])
    return np.stack([
        np.interp(path_t, source_t, q[:, joint])
        for joint in range(q.shape[1])
    ], axis=1)


# --------------------------------------------------------------------------
# Vendor service helpers.
#
# crb_ros_msg lives on the robot only (its sources are behind CASBOT's internal
# 10.11.0.5, doc p.10/p.18), so every import here is lazy: --dry-run must keep
# working on a laptop with no ROS and no vendor packages.
#
# NOTE: these are written from the YAML examples in the vendor doc and have NOT
# been run against hardware. A failed import, missing service, timeout, or
# non-zero vendor return is an assertion failure: research bring-up must expose
# the exact fault and stop before any trajectory command is sent.
# --------------------------------------------------------------------------
def _call_control(node, fields, joint_state=None, timeout=5.0):
    """One successful request to CONTROL_SERVICE; assert on any failure."""
    import rclpy
    from crb_ros_msg.srv import MotionUnifiedControl

    cli = node.create_client(MotionUnifiedControl, CONTROL_SERVICE)
    assert cli.wait_for_service(timeout_sec=timeout), (
        f"{CONTROL_SERVICE} not available after {timeout:.0f}s")

    req = MotionUnifiedControl.Request()
    for key, val in fields.items():
        setattr(req.motion_unified, key, val)
    if joint_state is not None:
        names, positions = joint_state
        req.motion_unified.joint_state.name = list(names)
        req.motion_unified.joint_state.position = [float(v) for v in positions]

    fut = cli.call_async(req)
    rclpy.spin_until_future_complete(node, fut, timeout_sec=timeout)
    assert fut.done(), f"{CONTROL_SERVICE} did not finish within {timeout:.0f}s"
    assert fut.result() is not None, f"{CONTROL_SERVICE} returned no response"
    res = fut.result()
    ret = int(getattr(res, "ret", -1))
    msg = str(getattr(res, "message", ""))
    assert ret == 0, f"{CONTROL_SERVICE}: ret={ret} {msg}".strip()
    return f"ret={ret} {msg}".strip()


def enable_feedback(node, hz=50):
    """Switch on active joint reporting (doc p.11-12).

    Off by default, and the vendor lists the symptom in their own FAQ as
    'arm does not actively report joint angles' (doc p.22). Without this the
    robot looks dead: no JointState, and this script times out after 10 s.

    'all' is listed before 'hz' because the vendor says to set all first, then
    override per device. Note their p.12 example shows 'hz' and 'all' as two
    separate int_name/int_val pairs in one request, which cannot work -- the
    second pair replaces the first. Merged single lists are the working form.
    """
    return _call_control(node, {
        "func_name": "Set_realtimePush_enable",
        "int_name": ["all", "hz"],
        "int_val": [1, int(hz)],
    })


def movej(node, names, positions, vel_scale=0.05):
    """Move to one pose via the slow one-shot interface (doc p.14).

    The vendor's explicit guidance (doc p.12, note ii) is to Movej to the first
    frame of a continuous trajectory BEFORE opening the high-rate channel. Park
    pose to gesture start is a ~3 rad move on some joints; doing it here at 5%
    speed is far safer than ramping it over the 50 Hz stream.
    """
    return _call_control(node, {
        "func_name": "Movej",
        "double_name": ["vel_scale"],
        "double_val": [float(vel_scale)],
    }, joint_state=(names, positions), timeout=60.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--traj", default="w1_traj.npz")
    ap.add_argument("--topic", default=COMMAND_TOPIC,
                    help=f"command topic (sensor_msgs/JointState). Default {COMMAND_TOPIC} "
                         "per vendor dev doc V2.0 p.13. Use --discover to double-check.")
    ap.add_argument("--state-topic", default=FEEDBACK_TOPIC)
    ap.add_argument("--enable-feedback", action="store_true",
                    help="call Set_realtimePush_enable first (doc p.11-12). Joint reporting "
                         "is OFF by default; without it the robot looks dead.")
    ap.add_argument("--movej-first", action="store_true",
                    help="use the Movej service to reach the trajectory's first frame before "
                         "streaming, at --movej-vel (doc p.12 note ii). Recommended.")
    ap.add_argument("--movej-vel", type=float, default=0.05,
                    help="speed fraction for --movej-first (0-1). Default 0.05 = 5%%.")
    ap.add_argument("--arms", choices=["both", "left", "right"], default="both",
                    help="stream only one arm's joints for early tests")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="path speed multiplier; 0.25=quarter speed, 1.25=25%% faster")
    ap.add_argument("--command-rate", type=float, default=100.0,
                    help="fixed command frequency in the vendor's 50-200 Hz band")
    ap.add_argument("--ramp", type=float, default=5.0, help="ramp-in/out seconds")
    ap.add_argument("--track-tol", type=float, default=0.35,
                    help="rad; measured-vs-commanded error that triggers abort")
    ap.add_argument("--feedback-timeout", type=float, default=0.6,
                    help="s; feedback silence that triggers abort")
    ap.add_argument("--dry-run", action="store_true",
                    help="full flow, no publishing (safe anywhere)")
    ap.add_argument("--discover", action="store_true",
                    help="list plausible command topics and exit")
    ap.add_argument("--test-nudge", default="",
                    help="joint name: move ONLY this joint by --nudge-delta and back "
                         "(minimal command-interface test)")
    ap.add_argument("--nudge-delta", type=float, default=0.05)
    ap.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    a = ap.parse_args()

    if a.discover:
        import rclpy
        from rclpy.node import Node
        rclpy.init()
        node = Node("w1_gesture_streamer")
        time.sleep(1.0)
        rclpy.spin_once(node, timeout_sec=1.0)
        print("topics that look like command/state channels:")
        for name, types in sorted(node.get_topic_names_and_types()):
            low = name.lower()
            if any(k in low for k in ("joint", "motion", "arm", "cmd", "upper")):
                print(f"  {name}  [{', '.join(types)}]")
        print("\npick the SET/command topic (JointState type), then rerun with --topic. "
              "Check direction with: ros2 topic info -v <topic>")
        node.destroy_node()
        rclpy.shutdown()
        return

    # Load and audit before importing ROS. This makes --dry-run a real laptop
    # test and ensures a malformed trajectory fails before touching the robot.
    d = np.load(a.traj, allow_pickle=True)
    names_all = [str(n) for n in d["names"]]
    q_all = np.asarray(d["q"], float)
    file_rate = float(d["rate"])
    assert names_all == ALL_JOINTS, names_all
    assert q_all.ndim == 2 and q_all.shape[1] == len(ALL_JOINTS), q_all.shape
    assert len(q_all) >= 2
    assert np.isfinite(q_all).all()
    assert file_rate > 0.0, file_rate
    assert 0.0 < a.speed <= 1.0, "robot playback --speed must be in (0, 1]"
    assert 50.0 <= a.command_rate <= 200.0, a.command_rate
    assert 0.0 < a.movej_vel <= 0.05, "first-day Movej speed must be in (0, 0.05]"

    keep = [i for i, n in enumerate(names_all)
            if a.arms == "both" or n.startswith(a.arms)]
    names = [names_all[i] for i in keep]
    q_traj = resample_speed(q_all[:, keep], file_rate, a.command_rate, a.speed)
    rate = a.command_rate
    dt = 1.0 / rate

    if a.dry_run:
        peak_velocity = np.abs(np.diff(q_traj, axis=0)).max() * rate
        print(f"validated {a.traj}")
        print(f"source: {q_all.shape[0]} frames x {q_all.shape[1]} joints "
              f"@ {file_rate:.3f} Hz")
        print(f"plan  : {(q_traj.shape[0]-1)/rate:.3f}s at {a.speed:.2f}x, "
              f"{len(names)} joints ({a.arms}), fixed {rate:.1f} Hz")
        print(f"peak gesture velocity: {peak_velocity:.3f} rad/s")
        print("DRY RUN complete: ROS was not imported and no command was sent.")
        return

    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import JointState

    rclpy.init()
    node = Node("w1_gesture_streamer")

    # ---- wait for feedback ---------------------------------------------
    meas = {"q": None, "t": 0.0}

    def on_state(msg):
        pos = dict(zip(msg.name, msg.position))
        if all(n in pos for n in names):
            meas["q"] = np.array([pos[n] for n in names])
            meas["t"] = time.monotonic()

    if a.enable_feedback:
        detail = enable_feedback(node, hz=50)
        print(f"[feedback] Set_realtimePush_enable: OK ({detail})")

    node.create_subscription(JointState, a.state_topic, on_state, 10)
    print(f"waiting for feedback on {a.state_topic} ...")
    t0 = time.monotonic()
    while meas["q"] is None:
        rclpy.spin_once(node, timeout_sec=0.2)
        if time.monotonic() - t0 > 10.0:
            sys.exit(f"no usable JointState on {a.state_topic} within 10 s "
                     f"(need joints: {names}). Is the robot up? Try --discover.")
    q_init = meas["q"].copy()      # also the pose we ramp back to at the end
    print("current pose: " + "  ".join(f"{n}={v:+.2f}" for n, v in zip(names, q_init)))

    # ---- build the full command timeline --------------------------------
    n_ramp = max(2, int(a.ramp * rate))
    if a.test_nudge:
        if a.test_nudge not in names:
            sys.exit(f"--test-nudge joint must be one of {names}")
        j = names.index(a.test_nudge)
        q_up = q_init.copy(); q_up[j] += a.nudge_delta
        n2 = max(2, int(2.0 * rate))
        timeline = np.vstack([ramp(q_init, q_up, n2),
                              np.repeat(q_up[None, :], int(1.0 * rate), 0),
                              ramp(q_up, q_init, n2)])
        desc = f"NUDGE {a.test_nudge} by {a.nudge_delta:+.3f} rad and back"
    else:
        timeline = np.vstack([ramp(q_init, q_traj[0], n_ramp),
                              q_traj,
                              ramp(q_traj[-1], q_init, n_ramp)])
        desc = (f"{(q_traj.shape[0]-1)/rate:.1f}s of gesture at {a.speed:.2f}x + "
                f"{a.ramp:.0f}s ramps, {len(names)} joints ({a.arms}), "
                f"fixed {rate:.1f} Hz")

    pv = np.abs(np.diff(timeline, axis=0)).max() * rate
    print(f"\nplan : {desc}\n"
          f"topic: {a.topic or '(DRY RUN - no topic)'}\n"
          f"peak commanded velocity: {pv:.2f} rad/s\n"
          f"abort: Ctrl-C anytime; hardware E-stop always wins")
    if not a.topic:
        sys.exit("need --topic (find it with --discover) or --dry-run")
    if not a.yes:
        if input("type 'go' to start: ").strip() != "go":
            sys.exit("aborted by user")

    # ---- optional: reach the first frame with the slow one-shot service -----
    # Vendor doc p.12 note ii. Park pose -> gesture start is the single largest
    # motion of a session; Movej at 5% is much safer than ramping it over the
    # 50 Hz channel. Afterwards the ramp-in is rebuilt from where we actually
    # ended up, while the tail still returns to the original pose.
    if a.movej_first and not a.test_nudge:
        print(f"[movej-first] Movej to first frame at {a.movej_vel*100:.0f}% speed ...")
        detail = movej(node, names, q_traj[0], a.movej_vel)
        print(f"[movej-first] {detail}")
        t_settle = time.monotonic()
        while time.monotonic() - t_settle < 2.0:
            rclpy.spin_once(node, timeout_sec=0.1)
        q_now = meas["q"].copy()
        err = np.abs(q_now - q_traj[0]).max()
        print(f"[movej-first] max error vs first frame: {err:.3f} rad")
        assert err <= a.track_tol, (
            f"[movej-first] did not arrive ({err:.2f} > {a.track_tol} rad)")
        timeline = np.vstack([ramp(q_now, q_traj[0], max(2, int(1.0 * rate))),
                              q_traj,
                              ramp(q_traj[-1], q_init, n_ramp)])

    pub = node.create_publisher(JointState, a.topic, 10)

    # ---- stream ----------------------------------------------------------
    i = 0
    aborted = [None]

    def tick():
        nonlocal i
        if aborted[0]:
            return
        age = time.monotonic() - meas["t"]
        if age > a.feedback_timeout:
            aborted[0] = f"feedback silent for {age:.2f}s"
        elif i > 0 and meas["q"] is not None:
            err = np.abs(meas["q"] - timeline[min(i - 1, len(timeline) - 1)]).max()
            if err > a.track_tol:
                aborted[0] = f"tracking error {err:.2f} rad > {a.track_tol}"
        if aborted[0]:
            node.get_logger().error(f"ABORT: {aborted[0]} - stopped publishing")
            return
        if i >= len(timeline):
            aborted[0] = "done"
            return
        msg = JointState()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.name = names
        msg.position = [float(v) for v in timeline[i]]
        pub.publish(msg)
        if i % int(5 * rate) == 0:
            node.get_logger().info(f"t={i/rate:6.1f}s / {len(timeline)/rate:.1f}s "
                                   f"(fb age {age*1000:.0f} ms)")
        i += 1

    node.create_timer(dt, tick)
    try:
        while rclpy.ok() and not aborted[0]:
            rclpy.spin_once(node, timeout_sec=0.2)
    except KeyboardInterrupt:
        print("\nCtrl-C: stopped publishing (servos hold last target).")
    if aborted[0] == "done":
        print("finished cleanly, robot returned to its initial pose.")
    elif aborted[0]:
        print(f"stopped: {aborted[0]}")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

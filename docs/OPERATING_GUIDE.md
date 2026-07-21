# CASBOT W1: operating checklist

> **Package note (21 July 2026):** use `../TOMORROW_CHECKLIST.md` for the names
> of the new short motion files and their escalation commands. This guide
> remains authoritative for physical setup, vendor interfaces, the 14-joint
> direction gate, troubleshooting, and voice playback. The packaged
> `stream_ros2.py --dry-run` is now a true laptop-only validation and therefore
> prints trajectory metrics without waiting for robot feedback.

**This is the document you follow standing next to the robot.** It assumes you have read
`CONCEPTS.md`, which defines every term used here. If a word is unfamiliar, it is in the
glossary at the end of that file.

Page references like `(doc p.13)` point to
`CASBOTW1 二次开发文档V2.0--外部小伙伴-2026.3.17.pdf`, the vendor's development document.
Every command below is one of their own documented calls. Nothing here is improvised.

Format of each step:

> **Do:** the command
> **Expect:** what a good result looks like
> **Stop if:** what means something is wrong

**The overriding rule: if you are unsure, stop. There is no penalty for a false alarm.**

---

## Before you travel

These four things must be done at home. Doing them at the vendor's lab wastes their time.

- [ ] **Keep the command rate fixed and legal.** The vendor supports 50-200 Hz (doc p.12).
      Use `stream_ros2.py --command-rate 100`; it interpolates every trajectory onto a steady
      100 Hz stream. Change motion duration with `--speed 0.25`, `0.5`, or `1.0`—never by
      lowering the command frequency. The legacy file's stored 40.09 Hz is an input sampling
      rate, not the rate sent to the robot.
- [ ] **Watch `videos/w1_traj_check.mp4` end to end.** This is the exact motion the robot will
      play. If anything in it looks wrong, it will look wrong on a 274 kg machine too.
- [ ] **Pack the USB-C to Gigabit Ethernet adapter.** A MacBook Pro has no Ethernet socket and
      the entire access path is wired (doc p.8). Without this you cannot connect at all.
      Also pack: an Ethernet cable, the Logitech F710 gamepad and its USB receiver, charger.
- [ ] **Copy two files to a folder you can find:** `data/w1_traj.npz` and `stream_ros2.py`.

---

## Step 1 - Safety, before anything is powered

**Locate, physically touch, and test these before the robot is enabled:**

- [ ] The **hardware emergency stop** 【急停按键】 on the robot body (doc p.4). Know where it is
      without looking.
- [ ] The **wireless emergency stop** 【无线急停】 (doc p.4). **One person holds this and does
      nothing else for the entire session.** Not the person typing.
- [ ] The **F710 gamepad**. Enable it with **LB + RB held together**. Soft emergency stop is
      **LT held + A double-tapped**; release is **LT held + B double-tapped** (doc p.27-28).
      Confirm the gamepad is paired before you need it.
- [ ] Clear space: **1.5 m around each arm**, nothing on the floor, no cables in the sweep, no
      one standing between the robot and a wall.

**Two vendor rules that damage hardware if broken:**

- [ ] **If the robot has been transported since it was last used, press "zero pose"**
      【零位姿态】 **on BOTH arm web pages first** (doc p.20, section 3.2.1.2). This straightens
      both arms out horizontally and re-establishes their position sense. The vendor states
      plainly that skipping this risks a collision that can damage the equipment. Ask the
      engineers whether it has been moved; if in any doubt, do it.
- [ ] **Never force a gripper open or closed by hand while it is powered** (doc p.22,
      section 3.3). Even light force can break it.

**Say out loud, before every single motion in this document, what is about to happen.** The
person on the E-stop cannot tell an intended move from a fault otherwise.

---

## Step 2 - Connect the MacBook

### 2a. Set a static IP

System Settings > Network > your USB Ethernet adapter > Details > TCP/IP:

- Configure IPv4: **Manually**
- IP Address: **`172.16.0.50`**
- Subnet Mask: **`255.255.255.0`**
- Router: leave blank

Apply. Plug the Ethernet cable directly between the Mac and the robot, or into the same router
as the robot (doc p.8).

### 2b. Log in

> **Do:**
> ```bash
> ssh casbot@172.16.0.10
> ```
> **Expect:** a password prompt (nothing appears as you type - that is normal), then a prompt
> on the robot's own computer (doc p.8).
> **Stop if:** "no route to host" or a timeout. Your IP is wrong, or the cable is in the wrong
> port. Check with `ping 172.16.0.10`.

### 2c. Check the motion system is alive

> **Do:**
> ```bash
> tail -50 /tmp/launcher/last_run_w1_crb_motion.bash.log
> ```
> **Expect:** recent log lines, no repeating errors (doc p.8).
> **Stop if:** the file does not exist or the log is full of errors. Show it to the engineers
> before going further.

### 2d. Copy our files across

In a **second** Terminal window on the Mac (Cmd-N), **not** inside the SSH session:

```bash
scp w1_traj.npz stream_ros2.py casbot@172.16.0.10:~/
```

### 2e. Confirm Python can run our streamer

Back in the SSH window:

> **Do:**
> ```bash
> python3 -c "import rclpy, numpy; print('ok')"
> ```
> **Expect:** `ok`.
> **Stop if:** an import fails. Ask the engineers - question 3 in `VENDOR_BRIEF_CN.md` covers
> exactly this.

---

## Step 3 - Turn on joint reporting (nothing moves)

**Do not skip this. Without it the robot looks completely dead.** The robot does not report
joint positions by default, and the vendor lists this in their own troubleshooting as "arm does
not actively report joint angles" 【机械臂不主动上报关节角度】 (doc p.22).

> **Do:** (in the SSH session)
> ```bash
> ros2 service call /motion_unified/control crb_ros_msg/srv/MotionUnifiedControl "
>     motion_unified: {
>         func_name: Set_realtimePush_enable,
>         int_name: ['all', 'hz'],
>         int_val:  [    1,   50],
>     }
> "
> ```
> **Expect:** a response containing `ret: 0`. Anything else is an error code (doc p.11).
> **Stop if:** `ret` is non-zero, or the call hangs. The service name or the motion system is
> not up.

> **Note on the vendor's own example.** Doc p.12 shows `hz` and `all` as two separate
> `int_name:` / `int_val:` pairs inside one request. That is not valid - the second pair
> silently replaces the first, so only `all` would be applied. The merged single-list form
> above is what actually works, and matches the pattern they use elsewhere on the same page.
> The vendor also notes to set `all` first and then any per-device overrides, which is why
> `all` is first in the list.

Now read the robot's actual joint positions:

> **Do:**
> ```bash
> ros2 topic echo --once /motion_unified/get/joint_state
> ```
> **Expect:** a list of joint names including `left_joint1` ... `right_joint7`, each with a
> position in radians (doc p.18).
> **Stop if:** it hangs with no output. Reporting did not turn on. Repeat the service call.

**Write down these numbers.** This is where the arms are right now, and it is your reference
for everything that follows.

---

## Step 4 - First motion: the vendor's own standing pose

Everything so far was read-only. This is the first time the robot moves.

**Announce it. Confirm the E-stop holder is watching. Confirm nobody is within reach.**

Speed is set to `0.05`, meaning **5 percent** of full speed (doc p.14). Do not raise it.

> **Do:**
> ```bash
> ros2 service call /motion_unified/control crb_ros_msg/srv/MotionUnifiedControl "
>     motion_unified: {
>         func_name: Movej,
>         joint_state: {
>             name: [ 'left_joint1', 'left_joint2', 'left_joint3', 'left_joint4',
>                     'left_joint5', 'left_joint6', 'left_joint7', 'left_gripper',
>                     'right_joint1', 'right_joint2', 'right_joint3', 'right_joint4',
>                     'right_joint5', 'right_joint6', 'right_joint7', 'right_gripper',
>                     'head_yaw_joint', 'head_pitch_joint',
>                     'waist_pitch_joint', 'waist_updown_joint' ],
>             position: [ -0.17455, -1.48349, 1.5708, 1.74533e-05, 0, -1.74533e-05, -1.74533e-05, 0,
>                          0.174585, 1.48348, -1.57081, 1.74533e-05, 0, 1.74533e-05, -1.74533e-05, 0,
>                          0, 0, 0, 0.0 ]
>         },
>         double_name: ['vel_scale'],
>         double_val:  [      0.05  ],
>     }
> "
> ```
> **Expect:** slow motion, then `ret: 0`. **Both arms end up hanging straight down at the
> sides, angled very slightly forward.** Head straight, torso upright, lifting column all the
> way down.
> **Stop if:** the arms go anywhere else at all. See the box below - this is the most
> informative failure in the whole procedure.

**What this command is.** It is the vendor's own "restore standing" 【恢复站立】 example from
doc p.15, with two deliberate changes:

1. **`vel_scale` set to `0.05`.** Their example leaves it commented out, which would use the
   configuration file's default. We set it explicitly so speed is never a surprise.
2. **The last number is `0.0`, not their `0.6`.** That is `waist_updown_joint`, the lifting
   column height in metres. Their example raises it to 0.6 m. We use 0.0 because **every
   collision check we ran offline was done with the column fully down**, so that is the only
   configuration our validated trajectory is actually valid for.

> ### If the arms do not hang at their sides
>
> **Stop and do not send another motion command.**
>
> This pose is 14 known-good numbers from the vendor's own document. If the robot's arms end up
> somewhere else, then the meaning of those numbers on the real controller differs from their
> meaning in our model. Everything downstream - our whole trajectory - is built in our model's
> convention, so it would be equally wrong, and possibly mirrored into the robot's own body.
>
> Show the engineers doc p.15 and question 2 in `VENDOR_BRIEF_CN.md`. This is exactly the
> question that page asks.

There is also a shorter version, which moves to whatever pose the configuration file has saved
under the name `init` (doc p.17). Useful once you trust it, but the explicit vector above is
better the first time because you know exactly what you asked for:

```bash
ros2 service call /motion_unified/control crb_ros_msg/srv/MotionUnifiedControl "
    motion_unified: {
        func_name: Movej_to_namedPose,
        str_name: ['pose_name'],
        str_val:  [   'init'   ],
    }
"
```

---

## Step 5 - Prove the direction convention (the gate)

**Nothing plays a gesture until this table is complete.**

Section 3 of `CONCEPTS.md` explains why: "+0.5 rad" is meaningless until you know which way is
positive, and we have never checked that our model agrees with the real controller.

The test: from the standing pose you just reached, move **one joint at a time** by +0.2 rad
(about 11 degrees), watch which way it goes, and compare against the table below. The table was
computed from our model at exactly this pose, so a match means the conventions agree.

> **Do:** for each joint in turn,
> ```bash
> python3 stream_ros2.py --traj w1_traj.npz \
>     --topic /motion_unified/control/Movej_transparent \
>     --test-nudge left_joint1 --nudge-delta 0.2
> ```
> This moves that one joint by +0.2 rad, holds one second, and returns it. Everything else
> stays still.
> **Expect:** the motion described in the table.
> **Stop if:** it moves the opposite way, or a different joint moves, or nothing moves.

### The reference table

Directions are from the robot's own point of view. **Forward** is the way it faces.
**Outward** means away from the body; **inward** means across the front of the body.

| Joint | What +0.2 rad should do | How far | Observed | Match? |
|---|---|---|---|---|
| `left_joint1` | left hand swings **backward** | 122 mm | | |
| `left_joint2` | left hand swings **outward**, to the robot's left | 123 mm | | |
| `left_joint3` | hand stays put; **left forearm twists**, clockwise seen from above | - | | |
| `left_joint4` | left hand swings **forward**, slightly up | 72 mm | | |
| `left_joint5` | hand stays put; **twists**, clockwise seen from above | - | | |
| `left_joint6` | left hand swings **forward**, slightly up | 30 mm | | |
| `left_joint7` | hand stays put; **wrist twists**, clockwise seen from above | - | | |
| `right_joint1` | right hand swings **forward** | 122 mm | | |
| `right_joint2` | right hand swings **inward**, across the body | 123 mm | | |
| `right_joint3` | hand stays put; **right forearm twists**, clockwise seen from above | - | | |
| `right_joint4` | right hand swings **backward** | 72 mm | | |
| `right_joint5` | hand stays put; **twists**, clockwise seen from above | - | | |
| `right_joint6` | right hand swings **backward** | 30 mm | | |
| `right_joint7` | hand stays put; **wrist twists**, clockwise seen from above | - | | |

**Three things in that table are worth knowing in advance, because they look like bugs:**

1. **Joints 3, 5 and 7 barely move the hand.** At this pose they rotate the arm about its own
   length, like turning a screwdriver. Watch the forearm or the gripper rotate, not the hand
   travel. If you cannot see it, stick a small piece of tape on the gripper as a marker.
2. **The two arms are not mirror images on joint 2.** `left_joint2` sends the left hand
   outward; `right_joint2` sends the right hand *inward*. Both hands move toward the robot's
   left. That is correct and expected, not a fault.
3. **Joint 1 and joint 4 oppose each other.** On the left arm, joint1 swings the hand backward
   and joint4 swings it forward. Same axis, opposite directions.

**If every row matches, the conventions agree and you may proceed.** If any row is opposite,
stop, record which joints, and raise question 2 with the engineers. Do not "fix it by negating
in software" on the day; that guess is how arms get driven into torsos.

---

## Step 6 - Play a gesture

### 6a. Pre-flight, physically

- [ ] Lifting column fully down, waist at 0 (Step 4 did this)
- [ ] Wheels braked or the base disabled
- [ ] 1.5 m clear each side, floor clear, no cables in the sweep
- [ ] Grippers empty and closed
- [ ] Nobody inside the reach envelope
- [ ] The E-stop holder is watching and knows playback is starting
- [ ] Step 5's table is complete and every row matched

### 6b. Move to the first frame of the trajectory, slowly

The trajectory does not start from the standing pose. Getting there is a large single motion,
and it is the most dangerous moment of the session. The vendor's guidance is to make that move
first, with the slow one-off interface, and only then start streaming (doc p.12, note ii).

> **Do:**
> ```bash
> python3 stream_ros2.py --traj w1_traj.npz \
>     --topic /motion_unified/control/Movej_transparent --movej-first --dry-run
> ```
> This validates and resamples the file offline, without importing ROS or sending anything.
> **Expect:** source dimensions, planned duration, and a peak-velocity figure.
> **Stop if:** any assertion fails. Compare the exact-path preview with the intended opening
> pose before the real run.

Then run it for real without `--dry-run`, at `vel_scale 0.05`, and **watch the whole move.**

### 6c. The escalation ladder

**Never skip a rung.** Watch each one completely before starting the next.

```bash
# rung 0 - full flow, publishes nothing at all. Safe anywhere.
python3 stream_ros2.py --traj w1_traj.npz --dry-run

# rung 1 - one joint, tiny move (this is Step 5)
python3 stream_ros2.py --traj w1_traj.npz \
    --topic /motion_unified/control/Movej_transparent --test-nudge left_joint6

# rung 2 - LEFT ARM ONLY, quarter speed
python3 stream_ros2.py --traj w1_traj.npz \
    --topic /motion_unified/control/Movej_transparent --arms left --speed 0.25 --command-rate 100

# rung 3 - both arms, half speed
python3 stream_ros2.py --traj w1_traj.npz \
    --topic /motion_unified/control/Movej_transparent --speed 0.5 --command-rate 100

# rung 4 - both arms, full speed
python3 stream_ros2.py --traj w1_traj.npz \
    --topic /motion_unified/control/Movej_transparent --speed 1.0 --command-rate 100
```

Each run asks you to type `go` before it starts. That pause is deliberate: use it to check the
printed plan, the peak velocity, and that everyone is clear.

### 6d. What is protecting you while it runs

Built into `stream_ros2.py`, checked every single tick:

- **Ramp in and out.** Smooth eased motion from the measured pose to the trajectory start, and
  back at the end. No jumps.
- **Feedback watchdog.** If the robot stops reporting its joints for more than 0.6 s, stop
  publishing.
- **Tracking guard.** If any joint is more than 0.35 rad (about 20 degrees) away from what it
  was told, stop publishing. That gap is what a jam or a collision looks like from software.
- **Ctrl-C** stops publishing instantly.

**Remember what "stop publishing" means:** the arms freeze holding their last position. They do
not go limp and they are still powered. To make the robot safe to approach, use the E-stop.

---

## Step 7 - Speech alongside the gesture

The robot can play a wav file through its own speakers (doc p.5-6). Our exported audio is
already at 16 kHz, which is the rate that interface requires.

Put the wav in the robot's resource folder (doc p.6):

```
/workspace/prod_hru/share/crb_resources/resources
```

Then, from a **second SSH window**, fire it right after you start the stream:

```bash
ros2 action send_goal /action_voice_play crb_ros_msg/action/VoicePlay \
    '{"wav_path":"myclip", "continue_last":"false", "language":"en"}'
```

**Be honest about what this is: two commands started by hand, a fraction of a second apart.**
It is good enough to see that gesture and speech belong together. It is not frame-accurate
synchronisation, and it should not be presented as such. Proper synchronisation needs a single
program driving both, which does not exist yet - see `MOTIONS.md`.

---

## Step 8 - When something goes wrong

Straight from the vendor's own troubleshooting section.

**The arms do not move at all** (doc p.21)
1. Simplest fix: restart.
2. If you are debugging with the engineers: log into the arm's web page
   (`172.16.0.89` left, `172.16.0.88` right, user `admin`, password `123`, doc p.20). Click the
   red trash-bin icon to clear faults - you may need to click several times. Then per joint,
   **clear error** 【清除错误】 and **re-enable** 【上使能】. Then restart the `crb_motion`
   service.

**A gripper has no power / fails to initialise** (doc p.22)
Log into the arm's web page as `admin` or `root`. Go to Extensions > End Control > Voltage
【扩展 - 末端控制 - 电压】. Set it to 0 V, then back to the correct voltage for the model
(e.g. 24 V). Restart the arm. The vendor notes this switch has to happen at least once after
the arm leaves the factory before the connector supplies power at all.

**Motion is stuttering or laggy** (doc p.22)
Change the connection from WiFi to wired. This is the vendor's own answer, and it is why the
Ethernet adapter is on the packing list.

**No joint positions are being reported** (doc p.22)
Go back to Step 3. Reporting is off by default and switches off on restart.

**Cannot log into an arm's web page** (doc p.20)
Clear the browser's cache and history, then retry. The vendor documents this specifically.

---

## Appendix A - What is on each page of the vendor document

| Pages | Contents |
|---|---|
| 1 | Title; URDF download link; overall structure |
| 2 | Dimensions (910x615x1348 mm), weight (274 kg), chassis wheels |
| 3 | Turning radius, base speed; **joint limits**: head, waist, lifting column, arm joints 1-3 |
| 4 | **Arm joint limits 4-7**; payload, reach, joint speeds; **electrical interfaces incl. E-stops**; sensor coverage |
| 5 | Sensing range; slope limits; preset skills (empty); **voice playback interface** |
| 6 | **Voice playback spec and example**; power commands (empty); **arm and gripper joint names** |
| 7 | Five-finger hand joints; head joints; waist pitch |
| 8 | Lifting column; chassis motion; **topic vs service explanation**; **SSH login**; log file location |
| 9 | Config file: arm enable, default speed, hands, grippers |
| 10 | Gripper force; `Set_arm_realtimePush` spec |
| 11 | `Set_arm_realtimePush` example; **`Set_realtimePush_enable` spec** |
| 12 | **`Set_realtimePush_enable` example**; **high-rate streaming rules (50-200 Hz, continuity)** |
| 13 | **`Movej_transparent` topic - our command channel** |
| 14 | **`Movej` service spec and example** |
| 15 | **`Movej` "restore standing" pose vector**; `Move_cartesian` spec |
| 16-17 | `Move_cartesian` examples; **`Movej_to_namedPose`** |
| 18 | **`/motion_unified/get/joint_state` topic - our feedback channel**; `Get_jointState` service |
| 19-20 | `Get_cartesian`; **arm web login, IPs, passwords**; **critical cautions: zero pose after transport, green drag button**; version matching |
| 21 | **Troubleshooting: arms do not move** |
| 22 | **Troubleshooting: gripper power, WiFi stutter, no joint reports**; **gripper handling warning** |
| 23-26 | Chassis navigation: charging, waypoints, relative moves, maps (not used) |
| 26-28 | **F710 gamepad: message format and full button map incl. soft E-stop** |
| 29 | Soft emergency stop JSON; start of sensor data section |
| 30 | **Camera topics**; `/joint_states`; laser data |
| 31-32 | Laser data format |
| 33-34 | Device status; configuration: volume, microphone sensitivity, navigation speed |

## Appendix B - Joint reference, and where our model disagrees

### Joints we drive

| Joint | Limits (doc p.3-4) | Limits in our model | Note |
|---|---|---|---|
| `joint1` | -3.105 to +3.105 | -3.1 to +3.1 | model marginally tighter, fine |
| `joint2` | -2.267 to +2.267 | -2.268 to +2.268 | model marginally looser |
| `joint3` | -3.105 to +3.105 | -3.1 to +3.1 | model marginally tighter, fine |
| `joint4` | -2.35 to +2.35 | -2.355 to +2.355 | **model marginally looser** |
| `joint5` | -3.105 to +3.105 | -3.1 to +3.1 | model marginally tighter, fine |
| `joint6` | -2.232 to +2.232 | -2.233 to +2.233 | model marginally looser |
| `joint7` | -6.28 to +6.28 | -6.28 to +6.28 | matches; we hold this at 0 anyway |

All in radians, both arms, prefix `left_` or `right_`. Our trajectory keeps a 0.05 rad margin
inside whichever limit is tighter, so the "model looser" rows are not a hazard in practice. The
one to watch is `joint4`: our motion reaches -2.305, which is 0.045 rad from the vendor's real
limit.

### Joints we do not drive, where the documents disagree

Recorded because they are unresolved, not because they block us.

| Joint | Doc p.3 | Doc p.7-8 | Our model | Status |
|---|---|---|---|---|
| `head_pitch_joint` | -0.2618 to +0.331 | -0.34 to +0.33 | -0.36 to +0.51 | **the vendor document contradicts itself**; question 4 |
| `head_yaw_joint` | -0.785 to +0.785 | -0.78 to +0.78 | -0.78 to +0.78 | agrees |
| `waist_pitch_joint` | 0 to 1.5708 | 0 to 1.52 | 0 to 0.34 | model far more conservative |
| `waist_updown_joint` | 0 to 0.98 | 0 to 1.0 m | two stages, 0 to 0.48 each | **different structure**; question 5 |

### The two channels we use

| Purpose | Name | Type | Rate |
|---|---|---|---|
| Send arm positions | `/motion_unified/control/Movej_transparent` | `sensor_msgs/msg/JointState` | 50-200 Hz (doc p.13) |
| Read arm positions | `/motion_unified/get/joint_state` | `sensor_msgs/msg/JointState` | as set in Step 3 (doc p.18) |

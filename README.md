# CASBOT W1: tomorrow-ready ICRA motion package

This repository contains **27 robot-ready arm trajectories**: five short
same-audio trios and four genuine continuous long trios, each with Presentation,
Tabletop, and Casual behavior. Start with
`motions/01_showcase`; it is the three-motion paper-figure set already approved
visually. `motions/02_neerja_forward` is the requested Neerja version. Sonia,
Ava, and an alternate Neerja delivery are whole-trio voice-search results.

After the short hardware ladder passes, use `motions_long`: the videos and
robot paths now last **12.5–18.0 seconds**. The exact Figure 3 source contains
only five seconds, so it remains short rather than being visibly looped.

Read [TOMORROW_CHECKLIST.md](TOMORROW_CHECKLIST.md) at the robot. The absolute
gate is Step 5 of [docs/OPERATING_GUIDE.md](docs/OPERATING_GUIDE.md): verify all
14 real joint directions before playing any gesture.

## What is ready

- Short NPZs have 247 poses; long NPZs have 627–747 continuous poses for
  `left_joint1..7,right_joint1..7`.
- Every NPZ passed joint-limit, 1.5 rad/s velocity, 40 rad/s² acceleration,
  and frame-by-frame MuJoCo self-penetration checks.
- `stream_ros2.py` always publishes at 100 Hz; `--speed` changes path duration,
  not command frequency.
- Every trio uses one identical waveform across all three conditions.
- Each audio file is mono 16-bit PCM at 16 kHz, as required by the vendor voice
  action.
- `audio/safe_sync` and `package_manifest.json` provide a common duration and a
  safe `--speed <= 1.0` for every condition in a trio.
- `previews/exact_robot_paths` shows the exact prepared path stored in each NPZ.
- `previews/original_126d_skeleton` shows the original generated 43-joint
  skeletons before W1 retargeting, with articulated fingers and the matching
  waveform.
- `previews_long/safe_robot_timing` shows the long exact paths resampled to a
  shared safe duration with the matching same-audio WAV.

Run the complete offline test with:

```bash
python3 validate_package.py
python3 stream_ros2.py --traj motions/01_showcase/presentation.npz --dry-run
```

The dry run imports no ROS package and sends no command. Hardware mode requires
the robot's `rclpy`, `sensor_msgs`, and `crb_ros_msg` packages and live joint
feedback. Failed vendor calls assert and stop; the code does not hide errors.

## Which set means what

| Directory | Use | Selection honesty |
|---|---|---|
| `01_showcase` | Play first; approved paper-figure motions | Best visual diffusion sample was selected separately per condition. This is a best-case demonstration, not strict code-only causal evidence. |
| `02_neerja_forward` | Requested Neerja demo | One same-audio generated trio; forward shoulder bias and palm-aware wrist retargeting. |
| `03_sonia` | Strongest new voice result | Seed 0; the whole trio ranked first. No per-condition sample picking. |
| `04_ava` | Strong alternate silhouette | Seed 0; the whole trio ranked second. No per-condition sample picking. |
| `05_neerja_expressive` | Alternate Neerja delivery | Seed 0; one complete trio. No per-condition sample picking. |

The 12-voice ranking is in `audits/voice_seed0_scores.csv`. These scores are a
demo-search aid, not a paper evaluation result.

An additional exact-training-speaker search was run on BEAT speaker 1 with six
excerpts and two seeds. Its best human-motion candidates either collided after
W1 retargeting or required the visually rejected straight-up forearm pose.
Nothing from that search was silently mixed into the deployable set; the full
ranking and rejection evidence are in `audits/TRAINING_SET_SEARCH.md`.

## Long versions

| Directory | Safe shared duration | Note |
|---|---:|---|
| `motions_long/02_neerja_forward` | 18.04 s | Longest option; recommended first long take. |
| `motions_long/03_sonia` | 12.54 s | All three use the same 0.8 amplitude safety transform. |
| `motions_long/04_ava` | 15.23 s | Full continuous Ava excerpt. |
| `motions_long/05_neerja_expressive` | 17.88 s | Full continuous expressive Neerja excerpt. |

Use `long_manifest.json` for exact speeds. First watch
`previews_long/safe_robot_timing/02_neerja_forward.mp4`; unlike the
original-timing preview, it shows the timing the prepared robot files will use.

## Wrist and hand orientation

The W1 has a long double-wrist/gripper chain. These files do not treat the
gripper as a point: retargeting used the available forearm direction plus a
palm-plane orientation proxy, with the gripper plane interpreted like the human
thumb-index plane. Wrist joints 5-7 therefore participate in keeping the end
effector natural. The chosen mapping biases the upper arm forward instead of
opening it laterally into the "about to hug" pose.

This remains an approximation because the gesture representation has no full
finger pose. Grippers stay empty and are not actuated.

## Audio and timing

`audio/reference_5s` is the un-stretched five-second waveform used by the
original-timing overview videos. Safety preparation slowed some joint paths.
To preserve one shared waveform and remain inside the audited speed, use the
slower `audio/safe_sync/<set>.wav` plus the exact speeds in
`package_manifest.json` or [MOTION_MANIFEST.md](MOTION_MANIFEST.md).

The vendor voice action and motion script are still launched from two terminal
windows, so their start is only manually synchronized. Do not describe a real
robot recording as frame-accurate synchronization. The overview videos *are*
audio-aligned at the original five-second timing; the exact-path videos are
silent and show what the robot file contains.

## Repository map

```text
motions/                 deployable NPZ files only
motions_long/            continuous 12.5–18 s deployable NPZ files
audio/reference_5s/      original five-second 16 kHz WAV per trio
audio/safe_sync/         safety-matched shared 16 kHz WAV per trio
audio_long/              reference and safe-sync WAVs for long trios
previews/original_timing three-panel videos with the same audio
previews/original_126d_skeleton/ source 126-D skeleton trios with audio
previews/exact_robot_paths/ exact prepared trajectory previews
previews_long/           original, exact, and safe robot timing videos
original_126d_sources/   selected generated 126-D streams and canonical mean
audits/                  collision provenance, metrics, hashes, voice ranking
docs/                    full operating/background/vendor documentation
render_126d_skeleton.py  fail-fast source-skeleton renderer
stream_ros2.py           laptop dry-run + ROS2 hardware streamer
validate_package.py      standalone assertion-based package test
```

Re-render all five source-skeleton comparisons at the five-second recording
duration with:

```bash
python3 render_126d_skeleton.py --all --seconds 5
```

The native generations are 15 fps. The renderer linearly interpolates them to
30 fps for viewing; it does not change the generated poses or condition labels.

The copied `docs/MOTIONS.md` is an earlier planning record and says the
setting-conditioned files did not yet exist. That historical statement is now
superseded by this README and the manifest.

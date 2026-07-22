# Tomorrow: minimum successful CASBOT session

The first goal is **one correct, slow playback**, not a recording. The paper
demo comes only after the real controller convention is proven.

## Before leaving

```bash
python3 validate_package.py
python3 stream_ros2.py --traj motions/01_showcase/presentation.npz --dry-run
```

Watch these two files:

1. `previews/original_timing/01_showcase_same_audio.mp4` — the approved trio.
2. `previews/exact_robot_paths/01_showcase/presentation.mp4` — the exact first
   trajectory to send.

Pack the Ethernet adapter/cable, charger, F710 receiver/controller, camera,
tripod, and a second person dedicated to the hardware E-stop.

Copy this repository to the lab computer. Copy only the first NPZ initially:

```bash
scp stream_ros2.py motions/01_showcase/presentation.npz \
  casbot@172.16.0.10:~/
```

## At the robot: do not skip this gate

Follow `docs/OPERATING_GUIDE.md` Steps 1-5 with the CASBOT engineer present:

1. Test hardware and wireless E-stops; clear 1.5 m around both arms.
2. If transported, perform the vendor's two-arm zero-pose procedure.
3. Put the lift column fully down, waist at zero, base braked, grippers empty.
4. Enable and inspect `/motion_unified/get/joint_state` feedback.
5. Move to the vendor standing pose at 5% and verify **all 14 positive joint
   directions** one at a time.

If any joint number or direction differs, stop. Do not negate it by guesswork.
Ask the engineer to resolve the model/controller convention.

Also confirm whether `Movej_transparent` accepts a partial 14-joint list. The
vendor example sends 20 joints; this remains an open hardware-side question.

## Escalation ladder for the first approved path

The laptop dry run sends nothing and requires no ROS:

```bash
python3 stream_ros2.py --traj presentation.npz --dry-run
```

Then, on the robot, one rung at a time. Keep the E-stop holder watching:

```bash
python3 stream_ros2.py --traj presentation.npz --enable-feedback \
  --test-nudge left_joint6 --nudge-delta 0.05

python3 stream_ros2.py --traj presentation.npz --enable-feedback \
  --arms left --speed 0.25 --command-rate 100 --movej-first

python3 stream_ros2.py --traj presentation.npz --enable-feedback \
  --speed 0.25 --command-rate 100 --movej-first

python3 stream_ros2.py --traj presentation.npz --enable-feedback \
  --speed 0.5 --command-rate 100 --movej-first

python3 stream_ros2.py --traj presentation.npz --enable-feedback \
  --speed 0.907777346153 --command-rate 100 --movej-first
```

Every hardware run asks for `go`. Inspect the plan and clear the space before
typing it. Do not use `--yes` during first-day bring-up. Do not use a speed over
`1.0`; the script asserts and stops if asked.

If the approved Presentation path succeeds, repeat the ladder for Tabletop and
Casual using their speeds in `MOTION_MANIFEST.md`. Then test
`02_neerja_forward`. Sonia and Ava are backups, not prerequisites.

Once one short Neerja path has passed at full audited speed, copy and play the
long version. Do not use the long file for the first hardware command:

```bash
python3 stream_ros2.py \
  --traj motions_long/02_neerja_forward/presentation.npz \
  --speed 0.999781496133 --command-rate 100 --movej-first --enable-feedback
```

Its matching WAV is `audio_long/safe_sync/02_neerja_forward.wav`, and its
safe-timing preview is
`previews_long/safe_robot_timing/02_neerja_forward.mp4`.

## Audio only after motion is proven

Use `audio/safe_sync/01_showcase.wav`, not the five-second reference file. Its
duration matches the safe-speed paths in the manifest. The robot needs the WAV
in:

```text
/workspace/prod_hru/share/crb_resources/resources
```

Start the vendor `/action_voice_play` command from a second SSH terminal just
after typing `go`; the exact command is in `docs/OPERATING_GUIDE.md` Step 7.
This is manual synchronization. Record a clap or spoken marker if you need to
align camera footage later.

## Minimum footage before experimenting

Record, with one fixed camera and framing:

1. approved Presentation, Tabletop, Casual with the same showcase WAV;
2. Neerja Presentation, Tabletop, Casual with the same Neerja WAV;
3. one clean standing/home shot and one clear E-stop/bring-up shot.

Only after these are secured should you try Sonia, Ava, faster video playback,
or extra takes.

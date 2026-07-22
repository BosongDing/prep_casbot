# Motion manifest

All paths below are collision-audited and use a fixed 100 Hz command stream.
The `--speed` values make the three paths in a set finish with the same shared
`audio/safe_sync` WAV, while never running a path faster than its audit speed.

| Set | Presentation | Tabletop | Casual | Shared audio duration |
|---|---:|---:|---:|---:|
| `01_showcase` | 0.907777346153 | 0.985943114740 | 0.999777476296 | 5.84 s |
| `02_neerja_forward` | 0.881540056375 | 0.998367781790 | 0.858434279604 | 6.10 s |
| `03_sonia` | 0.897055893191 | 0.890987837657 | 0.998895052379 | 6.01 s |
| `04_ava` | 0.999575684209 | 0.985690261177 | 0.992108348338 | 5.65 s |
| `05_neerja_expressive` | 0.963843407597 | 0.998468399128 | 0.884842975662 | 5.98 s |

Example for the approved showcase Presentation path:

```bash
python3 stream_ros2.py \
  --traj motions/01_showcase/presentation.npz \
  --speed 0.907777346153 --command-rate 100 --movej-first --enable-feedback
```

The matching WAV is `audio/safe_sync/01_showcase.wav`. Copy it into the robot
resource folder and launch it from a second terminal as documented in
`docs/OPERATING_GUIDE.md` Step 7.

## Stored trajectory metrics

The stored rate differs across files because the safety audit slows the clock
until velocity and acceleration pass. It is *not* the ROS command rate.
`stream_ros2.py` interpolates every file to 100 Hz.

Run `python3 validate_package.py` to regenerate
`audits/validation_report.json`, which records stored rate, duration, safe-sync
speed, peak velocity, peak acceleration, collision provenance, and SHA-256
hashes for all files.

## Long continuous paths

Use the short paths for the escalation ladder, then switch to these. The values
below match `audio_long/safe_sync/<set>.wav` and never exceed the audited path
speed.

| Set | Presentation | Tabletop | Casual | Shared duration |
|---|---:|---:|---:|---:|
| `02_neerja_forward` | 0.999781496133 | 0.955274224842 | 0.880246028012 | 18.04 s |
| `03_sonia` | 0.998405103668 | 0.998405103668 | 0.998405103668 | 12.54 s |
| `04_ava` | 0.999407602204 | 0.925425844528 | 0.991941521990 | 15.23 s |
| `05_neerja_expressive` | 0.999565941829 | 0.864495963335 | 0.873376275890 | 17.88 s |

Example long Neerja Presentation run:

```bash
python3 stream_ros2.py \
  --traj motions_long/02_neerja_forward/presentation.npz \
  --speed 0.999781496133 --command-rate 100 --movej-first --enable-feedback
```

The matching audio is `audio_long/safe_sync/02_neerja_forward.wav`.

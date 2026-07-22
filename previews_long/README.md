# Long video guide

- `safe_robot_timing/` — watch these before hardware. Each panel is the exact
  prepared NPZ path, slowed to the common safe duration in `long_manifest.json`
  and muxed with the matching `audio_long/safe_sync` WAV.
- `original_timing/` — continuous generated motion at the original speech
  timing. Use these to judge gesture quality, not to infer real-robot speed.
- `exact_robot_paths/` — one silent video per deployable NPZ. These preserve
  each file's own stored safe duration before the three conditions are aligned.

The paper-figure showcase has no long video because its genuine source is only
five seconds. It was intentionally not repeated or ping-pong looped.

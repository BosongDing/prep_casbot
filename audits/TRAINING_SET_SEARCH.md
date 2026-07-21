# Training-set / overfit demo search

This search was performed because a strong demo is more important than a
held-out evaluation for the one-day hardware session. It is kept separate from
the five deployable trios so the evidence boundary stays explicit.

## Search protocol

- Source: six eight-second excerpts from BEAT speaker 1 (Wayne).
- Split status: speaker `1` is explicitly listed in
  `usecase_splits.json -> beat.train_speakers`; it is not held out.
- Sampling: seeds 0 and 1, guidance 2, with the RNG reset for every condition.
- Comparison unit: one complete Presentation/Tabletop/Casual trio. No condition
  was selected independently.
- Ranking: the same iconic-pose scores used for the paper figure plus whole-trio
  separation. All 12 rows are in `training_speaker_whole_trio_scores.csv`.
- Robot gate: palm-aware W1 retarget, 35-degree hand-bend cap, joint-limit and
  speed/acceleration preparation, then every-frame MuJoCo self-collision sweep.

## Outcome

No training-set trio was added to `motions/`.

| Candidate | Result |
|---|---|
| Wayne clip 50, seed 1 (rank 1) | Original retarget penetrated the chassis by 17.8 cm. A moderate lift still penetrated. A stronger lift made Presentation and Tabletop pass, but Casual still penetrated by 19.2 cm. |
| Wayne clip 5, seed 1 (rank 2) | Original retarget penetrated the chassis by 13.1 cm. |
| Wayne clip 100, seed 1 | Strong-lift mapping made all three paths collision-free, but visual inspection rejected it: both forearms stayed too vertical in the exact “hands raised all the way” pose the operator had already rejected. The moderate, more natural mapping penetrated by up to 11.8 cm. |

The important result is negative but useful: optimizing the human-motion trio
score alone exploits poses that do not survive the W1's long double-wrist
geometry. The collision-free high-lift workaround also destroys the desired
naturalness. It is therefore safer and visually better to use the five accepted
trios already in the package than to claim an “overfit demo” that only looks
good before embodiment.

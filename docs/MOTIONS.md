# What we need the CASBOT W1 to actually do

> **Historical planning document.** The statements below about the
> setting-conditioned files not existing are now superseded. The deployable
> files are in `../motions`, with current status in `../README.md` and exact
> safe-speed values in `../MOTION_MANIFEST.md`.

**Purpose of this file:** so that the first session on the hardware has one defined goal
instead of open-ended poking, and so the difference between "already built" and "still to
build" is written down rather than discovered at the vendor's lab.

Terms used here are defined in `CONCEPTS.md`. The procedure is in `OPERATING_GUIDE.md`.

**Which paper this is for:** CASBOT is **ICRA 2027** material (deadline 15 Sep 2026), the
cross-setting / use-case paper. It is not part of Humanoids 2026, which uses the NAO. The robot
section was deliberately cut from the current submission (`final_submission/READINESS.md`) and
will be rewritten around this work.

---

## The short version

| Question | Answer |
|---|---|
| Can the robot play gesture motion today? | **Yes** - one 2.6 minute clip is prepared and validated offline |
| Is that the motion the paper needs? | **No** - it is generic gesture, not setting-conditioned |
| Can it play speech with the gesture? | **Roughly** - two commands fired by hand, not synchronised |
| Can it switch between settings on demand? | **No** - nothing to sequence clips exists |
| What should Session 1 aim for? | Prove the robot reproduces our motion correctly. Nothing more |

---

## Part 1 - What the robot can play today

One file: `data/w1_traj.npz`. Verified by loading it.

| | |
|---|---|
| Joints driven | 14: `left_joint1..7`, `right_joint1..7` |
| Poses | 6311 |
| Stored sample rate | 40.09 Hz (streamer interpolates to fixed 100 Hz) |
| Duration | 157 s, about 2.6 minutes |
| Units | radians |
| Wrist twist (`joint7`) | held at 0.0 on both arms |
| Not driven at all | grippers, head, waist, lifting column, wheels |

### What this motion actually is

Generic co-speech gesture from the source dataset. Real human gesture, retargeted onto the W1
and safety-processed. It demonstrates *that the pipeline reaches the robot*. It does not
demonstrate any claim the paper makes.

Six style groups have already been rendered as videos with the matching speech
(`render_styles.py`, `videos/style_*.mp4`), picked by measurable properties of the motion:

| Group | Picked because |
|---|---|
| `energetic` | fastest average hand speed |
| `calm` | slowest average hand speed |
| `expansive` | hands furthest from the body |
| `compact` | hands closest to the body |
| `raised` | hands held highest |
| `asymmetric` | the two arms least alike |

These are a useful demo vocabulary and a good thing to show the engineers. They are **not** the
paper's settings.

### Three limitations to state plainly

**A third of the gestures had to be dropped.** Of 64 clips, **39 survived**. The rest were cut
because the robot collides with itself. People bring their hands together in front of the chest
constantly while speaking, and on this body that puts metal into metal. The dropped clips are
exactly the hands-together and hands-to-chest ones. This is a genuine limitation of putting
human gesture on the W1 and belongs in the paper, not hidden.

**Stored frame rate and robot command rate are now separate.** The safety audit produced a
40.09 Hz trajectory, while the vendor requires commands at **50-200 Hz** (doc p.12).
`stream_ros2.py` now interpolates the stored path onto a fixed 100 Hz command stream. Its
`--speed` option changes how quickly that path is traversed without moving the command rate
outside the legal band.

**And the same audit silently breaks gesture-speech synchrony.** This matters more than the
rate does. Numbers, all measured:

| | Duration |
|---|---|
| The 39 gesture clips at their true recorded speed, plus bridges | about 118 s |
| Committed file (`--rate 50`) | 157.4 s, roughly **1.3x slower than real** |
| Regenerated (`--rate 90`) | 186.3 s, roughly **1.6x slower than real** |

The time-stretch is a safety mechanism doing its job - it slows the clock rather than distorting
the path. But it means **the gesture no longer lines up with the speech it was generated from**,
in the committed file as much as in the regenerated one. Any co-speech claim on this robot has
to resolve it first, by one of:

- time-stretching the audio by the same factor (honest, but changes the voice)
- reducing gesture amplitude with `--amp` until no stretch is needed (changes the gesture)
- raising `--amax` from its current 40 rad/s^2, if that is justifiable against the arm's real
  capability (the vendor documents max joint *speed* on doc p.4 but no acceleration limit)

This is a decision for before Session 2, not something to settle at the vendor's lab.

**We have never confirmed the robot interprets our joint angles the way our model does.**
Step 5 of the operating guide is the test. Until it passes, "the robot can play this" is an
assumption, not a fact.

---

## Part 2 - What the paper actually needs, and what is missing

The demonstration the ICRA paper is built around, in its own words:

> One audio clip, three codes, three behaviors, rendered on the real CASBOT W1.
> (`usecase_lab/report/NIGHT_REPORT.md`)

That is: **the same sentence, spoken three times, with the robot's body language visibly
different each time** - because the deployment setting changed, not because the words did.

The three settings:

| Name in the paper | Key in the code | Physical staging |
|---|---|---|
| Presentation | `presentation` | robot at a podium |
| Tabletop | `seated_screen` | robot behind a desk |
| Casual | `standing_studio` | robot free-standing in a room |

**Never rename the code keys.** The display names are for the paper only; the keys are load-
bearing throughout the codebase.

The claim being demonstrated is that setting lives in *how* the gesture moves - speed, timing,
how long poses are held, how far the hands travel - rather than in *which* gesture is made. So
the three clips must be visibly different in dynamics while remaining recognisably the same
speech.

### The four things that do not exist yet

**1. Setting-conditioned motion has never been retargeted to this robot.**
The generator that produces setting-conditioned gesture emits a different representation from
the one our committed trajectory came from. It has never been run through
`dirvec_to_robot.py --robot casbot_w1`. Two gotchas are already documented and will bite:

- the forward axis of the generator's output must be **negated** before retargeting, or the
  hands point backwards into the torso and nearly everything self-collides
- `dirvec_to_robot.py` passes a limits argument into the wrong slot of the installed version of
  the IK solver and must be wrapped

Both are recorded in `final_submission/READINESS.md`.

**2. There is no home pose.** `stream_ros2.py` ramps from, and returns to, whatever pose it
*measured* when it started. Two clips played back to back therefore have no shared reference
point, and a viewer sees the robot drift. A canonical home pose needs defining - most likely
the vendor's standing pose from doc p.15, which Step 4 of the operating guide already uses.

**3. There is no sequencer.** One invocation plays exactly one file. Showing three settings
means three separate manual runs, with whatever pose drift that implies.

**4. There is no synchronised audio.** The only gesture-audio alignment that exists is offline
video muxing. On the robot, speech and motion are two commands fired by hand from two terminal
windows. Fine for showing that they belong together; not fine for a paper figure claiming
timing.

---

## Part 3 - Out of scope, and why

Not oversights. These follow from how the motion is represented: it stores **bone directions**,
which carries where a limb points but not how it is twisted about its own axis.

| Part | Why not |
|---|---|
| Head | Needs rotations the representation does not carry |
| Wrist twist (`joint7`) | Same reason - held at 0.0 |
| Grippers / hands | No hand data in the source; also a safety liability |
| Waist, lifting column | Held fixed; every offline collision check assumed this |
| Wheels / navigation | The robot stands still for all of this work |

This "both arms, no head, no wrist twist" set is the **minimum shared embodiment** - the common
ground across every robot in the study, which is what makes cross-robot comparison meaningful
at all.

---

## Part 4 - Recommended session split

### Session 1: bring-up, with the vendor's engineers present

**Goal: prove the robot reproduces our motion correctly.** Nothing else.

1. Connect, turn on joint reporting, read joint positions (guide Steps 2-3)
2. Reach the vendor's standing pose at 5 percent speed (Step 4)
3. **Complete the 14-row direction table** (Step 5) - the real deliverable of the day
4. Climb the escalation ladder to one full playback of the existing clip (Step 6)
5. Optionally fire a speech clip alongside it (Step 7)
6. Get the six questions in `VENDOR_BRIEF_CN.md` answered while they are in the room

**Success looks like:** a completed direction table and one clean 2.6 minute playback with no
aborts. **It does not look like a paper figure**, and trying for one on day one is how sessions
end badly.

### Session 2: the demonstration

Needs the four missing pieces from Part 2 built and tested in simulation first:

1. Retarget setting-conditioned motion to the W1, handling the two documented gotchas
2. Check all three clips through the offline collision sweep, and watch all three videos
3. Define a home pose and make clips start and end there
4. Write a small sequencer that holds home, plays a clip, returns home, with audio triggered
   from the same program
5. Only then: shoot presentation / tabletop / casual, same audio, same camera, same framing

---

## Part 5 - Open questions for the vendor

Full list with context in `VENDOR_BRIEF_CN.md`. The two that affect motion directly:

- **Does `Movej_transparent` accept a partial joint list?** We send 14 arm joints; their example
  sends all 20 including head, waist and column. If all 20 are required, our streamer needs to
  pad every frame with hold-still values.
- **Do the controller's positive joint directions match the model they gave us?** Step 5 tests
  it empirically, but a direct answer would save an hour and remove all doubt.

# CASBOT W1: everything you need to know before you touch it

**Read this before you travel. Nothing here asks you to operate anything.**

This document assumes you have never used a robot, never used a terminal, and never
configured a network. Every term is defined the first time it appears. Where the vendor's
document uses a Chinese term, it is kept alongside the English so that when you point at a
step, their engineers recognise it instantly.

Page references like `(doc p.13)` point to
`CASBOTW1 二次开发文档V2.0--外部小伙伴-2026.3.17.pdf`, the 34-page development document the
CASBOT engineers gave us. That document is the authority. This one is the translation of it
into language you and I can both act on.

When you are actually standing next to the robot, use `OPERATING_GUIDE.md` instead. That one
is a checklist. This one is the background that makes the checklist make sense.

---

## Contents

1. [What this machine physically is](#1-what-this-machine-physically-is)
2. [The parts, and what they are called](#2-the-parts-and-what-they-are-called)
3. [Joints, angles, and limits](#3-joints-angles-and-limits)
4. [Pose, trajectory, and control rate](#4-pose-trajectory-and-control-rate)
5. [Command versus measurement](#5-command-versus-measurement)
6. [What "stopping" actually means](#6-what-stopping-actually-means)
7. [The norms nobody writes down](#7-the-norms-nobody-writes-down)
8. [Where our motion data comes from](#8-where-our-motion-data-comes-from)
9. [Networking from zero](#9-networking-from-zero)
10. [The terminal from zero](#10-the-terminal-from-zero)
11. [ROS 2 from zero](#11-ros-2-from-zero)
12. [Glossary](#12-glossary)

---

## 1. What this machine physically is

The CASBOT W1 is not a toy and not a desktop arm. Numbers first, because they set your
instincts:

| Property | Value | Source |
|---|---|---|
| Weight | **274 kg** | doc p.2 |
| Size | 910 x 615 x 1348 mm (lift column all the way down) | doc p.2 |
| Arm reach | **610 mm** from shoulder | doc p.4 |
| Arm payload | 5 kg per arm | doc p.4 |
| Fastest joint speed | 180 deg/s (joints 1-2), 225 deg/s (joints 3-7) | doc p.4 |
| Base top speed | 1.4 m/s | doc p.3 |
| Turning radius | 490 mm | doc p.3 |

Read those two bold numbers together. Each arm can put its hand anywhere in a sphere about
0.6 m in radius, centred on its shoulder, roughly at chest height. And a joint can rotate at
225 degrees per second, which is more than half a turn per second.

So the working picture is: **a quarter-tonne machine with two arms that can each sweep a
0.6 m sphere faster than you can pull your hand back.** That is why the rest of this document
spends so much time on stopping and on going slowly. It is not bureaucratic caution. A 274 kg
base does not get knocked out of the way, and 225 deg/s is faster than a human reflex.

The good news: for our work the robot stands still. We drive **only the two arms**. The wheels
stay braked, the waist stays upright, the lifting column stays down. Everything else in the
vendor's document, and there is a lot of it, is out of scope for us.

---

## 2. The parts, and what they are called

Working from the ground up:

- **Base / chassis** 【底盘】 - the wheeled platform it stands on. Three wheels per side: one
  large powered wheel in the middle (150 mm across) and two smaller free-rolling wheels front
  and back (75 mm) (doc p.2-3). We never drive this.
- **Lifting column** 【升降柱】 - a vertical post that raises and lowers the whole upper body,
  like a height-adjustable desk. Travel is 0 to about 1.0 m (doc p.3, p.8). We keep it down.
- **Waist** 【腰部】 - a single bending joint that lets the torso lean forward, like bowing.
  0 is upright (doc p.3, p.7). We keep it at 0.
- **Torso / chest** 【胸腔】 - the body block the arms attach to. Has a depth camera in it.
- **Head** 【头部】 - turns left/right ("yaw") and nods up/down ("pitch") (doc p.3). We do not
  drive it.
- **Arms** 【机械臂】 - the two 7-joint arms. **This is the only part we control.**
- **End effector** - the general robotics word for "whatever is on the end of the arm". On this
  robot that is either a **two-finger gripper** 【二指夹爪】 or a **five-finger hand**
  【五指手】 (doc p.6-7). We use neither, but they are physically present, so they matter for
  clearance and for the "do not force them" warning in section 7.
- **E-stop** - short for **emergency stop** 【急停】. A big button that cuts power to the
  motors. This robot has a physical one on the body and a **wireless** one you can hold
  (doc p.4). There is also a separate **power button** 【开关机按键】, which is not the same
  thing and is not an emergency control.

A note on one more word you will see everywhere: a **link** is the rigid segment between two
joints, the equivalent of your upper arm bone or forearm bone. Joints move; links do not bend.

---

## 3. Joints, angles, and limits

### What a "joint" is

Your arm bends in a few specific places: shoulder, elbow, wrist. Each place that can bend is a
**joint**. The robot arm is the same idea, except it has 7 of them per arm, and they are just
numbered: joint1 is closest to the shoulder, joint7 is closest to the hand.

The vendor calls them `left_joint1` ... `left_joint7` and `right_joint1` ... `right_joint7`
(doc p.6). That is the robot's whole vocabulary for "arm". When you tell the robot to move,
you are always giving it 14 numbers: one angle per joint.

Why 7 and not 3? Because with 7 joints an arm can reach the same point in space in many
different ways, the way you can touch your nose with your elbow high or low. Roboticists call
each independently movable joint a **degree of freedom**, abbreviated **DoF**. So this is a
"7-DoF arm". You will hear that phrase constantly; it just means "7 joints".

### The unit is radians, not degrees

Everyone learns angles as degrees: a right angle is 90. Robots use a different unit called
**radians**, where a right angle is about 1.57.

```
degrees = radians x 57.3
radians = degrees / 57.3
```

So when the doc writes `1.5708`, that means 90 degrees. When it writes `0.05`, that means about
3 degrees, a small nudge. When it writes `3.105`, that means about 178 degrees, very nearly a
half-turn.

Why does this matter? Because if you ever type a number in degrees by mistake, say `90` where
you meant `1.57`, you have asked the arm for **5157 degrees**. It will drive at full speed into
whatever stops it first. This is the single most common beginner accident in robotics, and it
is worth re-reading the two conversion lines above until they are automatic.

A few conversions worth memorising:

| Radians | Degrees | What it looks like |
|---|---|---|
| 0.05 | 3 | a small nudge, our safety test move |
| 0.5 | 29 | a noticeable move |
| 1.57 | 90 | a right angle |
| 3.14 | 180 | a half turn |

### What a "joint limit" is

Your elbow does not bend backwards. It has a limit. Every robot joint has two: a smallest and a
largest angle it can reach. From doc p.3-4:

| Joint | Lower limit (rad) | Upper limit (rad) | Roughly, in degrees |
|---|---|---|---|
| joint1 | -3.105 | +3.105 | +/- 178 |
| joint2 | -2.267 | +2.267 | +/- 130 |
| joint3 | -3.105 | +3.105 | +/- 178 |
| joint4 | -2.35 | +2.35 | +/- 135 |
| joint5 | -3.105 | +3.105 | +/- 178 |
| joint6 | -2.232 | +2.232 | +/- 128 |
| joint7 | -6.28 | +6.28 | +/- 360 |

The robot's own controller will refuse or clip a command past a limit, but you should never
rely on that. Our software keeps a **0.05 rad safety margin** inside every limit before a
command is ever sent (`prepare_traj.py`, `limit_clamp`). Riding a hard stop is how you damage
a gearbox.

### Positive and negative: the direction problem

Here is a subtlety that will matter more than anything else in section 5 of the operating guide.

Saying "joint2 is at +0.5 rad" only means something if you know **which way is positive**. Is
+0.5 the arm lifting up, or lifting down? There is no universal answer. It is a convention that
whoever built the robot chose, and it has to be written down somewhere.

We have a computer model of this robot (see section 8) with its own idea of which way is
positive. The real robot's controller has its own idea too. **We have never checked that these
two agree.** And we have one piece of evidence suggesting they might not: the vendor's own
"stand up straight" pose (doc p.15) puts `left_joint3` at `+1.5708`, while our motion file
starts that same joint at `-1.645`. Those are nearly opposite.

That could be innocent, two genuinely different poses. Or it could mean our model's positive
is the robot's negative on that joint, in which case the robot would play our gesture
**mirrored on that joint** and could swing into its own body.

This is why the operating guide makes you nudge each joint by 0.05 rad, one at a time, and
write down which way it actually went, before anything else is allowed to move. That test takes
about fifteen minutes and removes the single largest unknown in the whole exercise.

---

## 4. Pose, trajectory, and control rate

**A pose is 14 numbers.** One angle for each arm joint. A pose is a single photograph of the
arms: this is where every joint is, right now. Nothing about it says anything about movement.

**A trajectory is a list of poses in order.** Think of a flipbook. Each page is one pose, and
flipping through them makes motion. Our file `data/w1_traj.npz` holds **6311 poses**, which is
6311 pages of flipbook.

**The control rate is how fast you flip the pages.** It is measured in **hertz** (Hz), which
just means "times per second". Our file is played at about **40 Hz**, so 40 poses per second.
6311 poses at 40 per second is 157 seconds, about two and a half minutes of gesture.

Three things follow from this, and all three matter:

1. **The robot does not interpolate for you.** You send pose after pose, on time, forever. If
   your program stutters and stops sending, the arm stops where it is. If your program sends
   two poses that are far apart, the arm tries to jump between them, which is violent. The
   vendor is explicit: consecutive positions must be continuous, and a jump of more than about
   10 degrees can make the arm judder or refuse to move (doc p.12).

2. **There is a supported speed band: 50 to 200 Hz** (doc p.12). Below 50 Hz the vendor does
   not promise smooth behaviour. **Our current file is at 40 Hz, which is under that floor.**
   This is a real defect, not a rounding issue, and section 8 explains where it came from and
   how we fix it before the trip.

3. **Getting to the first page is its own problem.** The flipbook starts at some pose, and the
   robot is currently at some completely different pose. Moving between them is a large single
   motion, and it is the most dangerous moment of any session. The vendor's advice is to make
   that move separately and slowly first, using a different, slower interface, and only then
   start flipping pages (doc p.12, note ii). The operating guide follows that advice.

---

## 5. Command versus measurement

This is the distinction that separates people who are safe around robots from people who are
not.

At every instant there are **two** different sets of 14 numbers:

- **the command** - what you asked for
- **the measurement** - where the joints actually are

They are never exactly equal, because motors take time and the arm has weight. In normal
operation they differ by a tiny amount. But when something goes wrong, they diverge, and *how*
they diverge tells you what went wrong:

| What you see | What it usually means |
|---|---|
| Measurement lags command by a little, steadily | Normal. The arm is heavy. |
| Measurement stops changing while command keeps moving | The arm is **jammed** or has hit something |
| Measurement goes silent entirely | Communication lost, or an E-stop fired |
| Measurement moves opposite to command | **Direction convention is wrong** (section 3) |

Our streaming program watches for exactly these. It reads the measurement continuously and
aborts if the measurement falls more than 0.35 rad (about 20 degrees) behind the command, or if
the measurement goes silent for more than 0.6 seconds (`stream_ros2.py`). A 20-degree gap
between what you asked for and what happened is what a collision looks like from software.

There is a trap here, and it has cost people entire lab sessions. **The robot does not report
its joint positions by default.** You have to switch reporting on with a specific command
(doc p.11-12). If you skip that step, the robot looks completely dead: no measurements, no
feedback, and our program gives up after 10 seconds with what appears to be a connection error.
The vendor even lists this in their own troubleshooting section as "arm does not actively report
joint angles" 【机械臂不主动上报关节角度】 (doc p.22). It is step 3 of the operating guide for
exactly this reason.

---

## 6. What "stopping" actually means

There are several ways to stop this robot and they are not equivalent. Strongest first:

### 1. Hardware E-stop 【急停按键】 and wireless E-stop 【无线急停】 (doc p.4)

A physical button that cuts motor power. Nothing in software can override it or delay it. There
is a button on the robot and a **wireless** one that can be held by a person standing away from
the machine. **In any session, one person holds the wireless E-stop and does nothing else.**

This always wins. If you are ever unsure, this is the answer.

### 2. Gamepad soft emergency stop (doc p.27)

The robot ships with a Logitech F710 gamepad. Holding **LT** and double-tapping **A** engages a
"soft emergency stop" 【软急停】 that locks the wheels. Holding **LT** and double-tapping **B**
releases it. It is a software stop, so it is weaker than the red button, but it is faster to
reach than a laptop keyboard, and it is a second pair of hands that does not have to be near the
machine.

Also worth knowing: hold **LB + RB** together to enable the gamepad, hold **LT + RT** together
to disable it (doc p.28). Disable it when you are not using it, so nobody leans on it.

### 3. Ctrl-C in our program

Pressing Ctrl-C in the terminal running our streamer stops it sending commands immediately.

### 4. The software guards inside our program

The watchdog and tracking checks from section 5. These act in a fraction of a second, but only
for the failure modes they were written to catch.

### The thing that surprises everyone

**When you stop sending commands, the arms do not go limp. They hold their last position.**

These are position-controlled motors: they are continuously working to hold the angle they were
last told. Stopping your program removes the *instruction to change*, not the *holding force*.
The arm freezes exactly where it is, still stiff, still powered.

This is usually what you want, because a limp 5 kg arm falling under gravity is worse. But it
means:

- "The program stopped" does **not** mean "the robot is safe to walk up to".
- If an arm is pressing on something, stopping your program does not release the pressure.
- To actually make it safe to approach, use the E-stop, or move the arm somewhere clear first.

The vendor gives you one more escape for exactly this situation: each arm has a **green button
on its end** which, held down, lets you physically drag that arm to a safe position by hand
(doc p.20). Useful when an arm has ended up somewhere awkward and you would rather move it than
command it.

---

## 7. The norms nobody writes down

Every robotics lab runs on these. Nobody puts them in a manual, and everyone assumes you
already know them. Here they are.

**Say what you are about to do, out loud, every time.** "Enabling arms." "Moving to home,
slowly." "Starting playback in three." Not politeness: it is how the person on the E-stop knows
whether what they are seeing is intended. A robot moving unexpectedly and a robot moving as
planned look identical from outside.

**Know where the arms can reach, and stand outside it.** Reach is 610 mm per arm from the
shoulder (doc p.4). Our own checklist asks for 1.5 m of clear space on each side. Never stand
between the robot and a wall, a bench, or a doorway. If the arm goes wrong, you want somewhere
to step back to.

**One person owns the E-stop and does only that.** Not the person typing. Not the person
filming. Their entire job is to watch the robot and hold the button. This is the rule people
skip when they are in a hurry, and it is the one that matters most.

**Move slowly the first time. Always.** Every interface here has a speed setting. The vendor's
own examples use `vel_scale: 0.05`, meaning 5 percent of full speed (doc p.15). Use it. A wrong
move at 5 percent is a story you tell later; the same wrong move at full speed is a repair bill
and a cancelled trip.

**Know your reset pose before you move.** Before any session, know the exact command that puts
the arms back somewhere safe. On this robot that is `Movej_to_namedPose` with `init` (doc p.17),
and the explicit "restore standing" 【恢复站立】 pose vector on doc p.15. Have it in your
clipboard.

**Never leave an enabled robot alone.** Not for coffee, not for a phone call. Powered position
control means it is holding torque, and a fault while nobody is watching is how equipment gets
destroyed.

**When something looks wrong, stop first and understand second.** The instinct to watch a moment
longer and figure out what is happening is the wrong one. Stopping costs you two minutes of
restart. Not stopping can cost the arm. There is no penalty for a false alarm, so have them
freely.

**Two vendor-specific rules that will damage the hardware if broken:**

- **After the robot has been transported, before anything else, press "zero pose"**
  【零位姿态】 **on both arm web pages**, which straightens both arms out horizontally
  (doc p.20, section 3.2.1.2). The vendor states plainly that skipping this risks a collision
  that can damage the equipment. Transport can leave the arms' internal position sense
  inconsistent with reality; this re-establishes it. If the robot has been moved since it was
  last used, this is your first action.
- **Never force a powered gripper open or closed by hand** (doc p.22, section 3.3). The vendor
  says even gentle force can break it. If a gripper needs to move, command it or power it down.

**Finally: you are a guest in their lab.** The engineers who wrote that document are letting you
operate a 274 kg machine they are responsible for. The way you earn that is by visibly following
their procedure. Every command in the operating guide is one of their own documented calls, cited
to their page number, and `VENDOR_BRIEF_CN.md` is a one-page Chinese summary you can hand them
that says exactly that. Being the visitor who read the manual is worth more than any amount of
explaining.

---

## 8. Where our motion data comes from

You do not need this to operate the robot, but you do need it to judge whether what the robot is
doing is correct, and to answer questions from their engineers.

### The chain, in plain terms

1. **Humans were recorded gesturing while talking.** This is **motion capture**, "mocap": the
   3D position of each body joint, many times a second. Our source is a public dataset of people
   speaking.
2. **The recording is stored as directions, not positions.** Rather than "the left hand is at
   this point in the room", we store "the forearm points this way relative to the upper arm".
   This makes the data independent of how tall the person was, which is what lets it transfer to
   a robot of a different size at all.
3. **Retargeting: human body to robot body.** The robot is not shaped like a person. Its arms
   have different segment lengths and different joint arrangements. **Retargeting** means
   working out the robot pose that best reproduces the human pose. We do this with a tool called
   GMR, and a model of the W1 which the vendor supplied.
4. **Inverse kinematics (IK).** Inside retargeting sits this question: "I want the hand *there*,
   what angle does each of the 7 joints need to be?" Working backwards from a desired hand
   position to joint angles is called **inverse kinematics**. Forwards, angles to position, is
   easy and unique; backwards is hard and has many answers, which is why a 7-joint arm can reach
   the same point in many poses.
5. **Safety processing.** This is `prepare_traj.py`, and it does five things:
   - smooths out single-frame glitches from the IK
   - resamples to a steady playback rate
   - clamps every angle to stay 0.05 rad inside its limit
   - checks speed and acceleration, and slows the whole thing down if anything is too fast
   - simulates every single frame and checks **whether the robot hits itself**
6. **The result is one file**, `data/w1_traj.npz`, which is what the robot actually plays.

### What is actually in that file

| | |
|---|---|
| Joints | 14: `left_joint1..7`, `right_joint1..7` |
| Poses | 6311 |
| Playback rate | 40.09 Hz |
| Duration | 157 s, about 2.6 minutes |
| Units | radians |
| Wrist twist (`joint7`) | held at 0.0 on both arms |

### Three honest caveats

**We had to throw away a third of the gestures.** Of 64 gesture clips, only **39** survived. The
rest were dropped because the robot collided with itself. Humans bring their hands together in
front of the chest constantly while speaking; the W1's arms and torso are shaped such that this
puts metal into metal. The dropped clips are exactly the hands-together and hands-to-chest ones.
This is a real limitation of putting human gesture on this body, and it is worth saying plainly
rather than hiding.

**Stored path rate and command rate are separate.** The safety processing produced a path
sampled at 40.09 Hz, while the vendor command stream must stay within 50-200 Hz (doc p.12).
`stream_ros2.py` interpolates the stored path at a fixed 100 Hz. Its `--speed` option changes
the traversal duration without changing that legal controller frequency; the checklist in
`OPERATING_GUIDE.md` has the exact commands.

A consequence worth knowing, because it affects what you can honestly claim: that same
slowing-down means the gesture **no longer runs at the speed the human performed it**, so it no
longer lines up with the speech it came from. This is true of the current file too, not just the
regenerated one. It does not affect safety or the bring-up, but it does affect any co-speech
demonstration. `MOTIONS.md` has the numbers and the options.

**The gestures in this file are generic, not the ones the paper needs.** They are unconditioned
gestures from the source dataset. The demonstration the ICRA paper actually wants, the same
sentence spoken three times in three different settings with visibly different body language,
has not been generated for this robot yet. See `MOTIONS.md`. This is why the first session's
goal is "prove the robot plays our motion correctly", not "shoot the paper figure".

---

## 9. Networking from zero

### What an IP address is

**IP** stands for Internet Protocol, and an **IP address** is a number that identifies one
machine on a network, written as four parts separated by dots, like `172.16.0.10`. It is a
postal address: to send data to a machine, you need its address.

The robot's onboard computer lives at **`172.16.0.10`** (doc p.8). The two arms have their own
small computers at **`172.16.0.89`** (left) and **`172.16.0.88`** (right), each serving a web
page you open in a browser (doc p.20).

Notice they all start with `172.16.0.`. That shared prefix means they are on the same local
network, in the same way that houses on one street share a street name. **For your laptop to
talk to them, it has to be on that street too**, meaning its address must also start with
`172.16.0.` and end with something nobody else is using. We will use `172.16.0.50`.

### Why you have to set this by hand

Normally when you plug into a network, a service called **DHCP** (Dynamic Host Configuration
Protocol) hands your machine an address automatically. That is why you never think about this
at a cafe.

The robot's network has no such service, or gives out addresses in the wrong range. So your Mac
would sit there with no valid address and be unable to reach anything. You have to set the
address manually. This is called a **static IP**, and the operating guide walks through the
exact clicks.

The vendor gives two ways to wire it (doc p.8): laptop and robot both plugged into a router, or
a single cable directly between laptop and robot. Direct is simpler and one less thing to
borrow.

### Use the cable, not WiFi

A MacBook Pro has no Ethernet socket, so you need a **USB-C to Gigabit Ethernet adapter**. Put
it on the packing list now; it is the single item whose absence ends the trip before it starts.

Do not be tempted to skip it and use WiFi. The vendor's own troubleshooting section says that
when arm control stutters, the fix is to change the connection from WiFi to wired (doc p.22).
We send 50 position updates per second and the robot judders if they arrive late. This is
precisely the workload WiFi is worst at.

---

## 10. The terminal from zero

### What a terminal is

A **terminal** is a window where you type commands instead of clicking. On macOS, press Cmd and
Space, type "Terminal", press Return.

You get a **prompt**, a line ending in `$` or `%` that means "ready". You type a command, press
Return, it runs, prints something, and you get the prompt back.

Three commands cover almost everything:

```bash
pwd            # print working directory: where am I?
ls             # list: what files are here?
cd foldername  # change directory: go into that folder
cd ..          # go back up one level
```

Anything after a `#` is a comment for humans, not part of the command.

### SSH: a terminal on someone else's computer

**SSH** stands for Secure Shell. The idea is simple: it gives you a terminal window that is
actually running on a *different* machine. You type here, it executes there.

```bash
ssh casbot@172.16.0.10
```

That reads as: connect to the machine at `172.16.0.10` and log in as the user `casbot`
(doc p.8). It will ask for a password. **Nothing appears as you type a password**, no dots, no
stars. That is normal, not a broken keyboard. Type it and press Return.

After that, the prompt changes, and every command you type runs **on the robot**. This is the
key move for our whole trip: we do not install anything on the Mac. All the robot software
already exists on the robot's computer. The Mac is just a window into it.

To leave, type `exit`.

### scp: copying a file to the robot

**scp** is "secure copy". Same idea as SSH, but for files.

```bash
scp w1_traj.npz casbot@172.16.0.10:~/
```

Reads as: copy the local file `w1_traj.npz` to the machine at `172.16.0.10`, logging in as
`casbot`, and put it in that user's home folder (the `~` means home). Run this in a terminal on
your Mac, **not** inside an SSH session.

### Two windows at once

You will often need one window streaming motion and another sending a command. Cmd-N opens a
new Terminal window; you can SSH from each one independently. Put them side by side.

### Stopping a running program

**Ctrl-C** (hold Control, press C) stops whatever is currently running in that terminal. This is
your most-used key combination. Re-read section 6 for what "stopped" means for the arms: they
freeze holding position, they do not relax.

### Reading a file

```bash
cat /tmp/launcher/last_run_w1_crb_motion.bash.log
```

`cat` prints a file to the screen. That particular file is the robot's motion-system log
(doc p.8), and it is the first place to look when something does not behave. If it is very long,
`tail -50 <file>` shows just the last 50 lines, which is usually what you want.

---

## 11. ROS 2 from zero

### What ROS is, and what it is not

**ROS** stands for Robot Operating System, which is a misleading name. It is not an operating
system like macOS. It is a set of conventions and tools that let many small programs on a robot
talk to each other. **ROS 2** is the current version.

The mental model: a robot is not one big program. It is dozens of small ones running at the same
time. One reads the cameras. One talks to the left arm. One drives the wheels. ROS 2 is the
plumbing between them.

Each of those small programs is called a **node**.

### The three ways nodes talk

This is the only ROS concept you actually need, and the vendor's document is organised around it
(doc p.8, section 3.1.2).

**A topic is a radio station.** A node broadcasts continuously on a named channel. Anyone can
tune in; nobody has to. The broadcaster does not know or care who is listening. Topics are for
continuous streams of data.

> Example: `/motion_unified/get/joint_state` is the robot broadcasting where its joints are,
> many times a second (doc p.18). And `/motion_unified/control/Movej_transparent` is the channel
> **we** broadcast on to tell the arms where to go (doc p.13).

**A service is a phone call.** You call, you ask one question, you get one answer, the call
ends. Services are for one-off requests.

> Example: "move to this pose at 5 percent speed" is a service call (doc p.14). "Start reporting
> your joint positions" is a service call (doc p.11).

**An action is a phone call for a long job.** You call, ask for something that takes a while, and
they keep you updated until it is done. Actions are for slow tasks with progress.

> Example: "play this sound file" is an action, because it takes as long as the audio does
> (doc p.5-6).

The vendor states the rule directly: **continuous high-rate data goes over a topic, one-off
requests go over a service** (doc p.8). That is exactly how our work splits. Getting the arm to
its starting pose is a one-off request, so it is a service. Streaming 50 poses a second is
continuous, so it is a topic.

### Names and types

Every topic has a **name**, always starting with `/`, and a **type**, which says what shape the
data is. Our command topic is:

```
name: /motion_unified/control/Movej_transparent
type: sensor_msgs/msg/JointState
```

`JointState` is a standard ROS message that carries a list of joint names and a matching list of
positions. That is why our program can talk to this robot with no vendor-specific code: it
speaks a standard message.

### The five commands worth learning

Run these on the robot, over SSH.

```bash
ros2 topic list                   # every channel currently broadcasting
ros2 topic echo --once <name>     # print one message from a channel, then stop
ros2 topic info -v <name>         # who publishes and who listens to this channel
ros2 service list                 # every available one-off request
ros2 service call <name> <type> "<data>"   # make a request
```

`ros2 topic echo --once /motion_unified/get/joint_state` is the single most useful one. It
prints the robot's current joint positions and proves the whole chain works, without moving
anything (doc p.18).

### Why service calls look so intimidating

In the vendor's document you will meet things like this (doc p.17):

```bash
ros2 service call /motion_unified/control crb_ros_msg/srv/MotionUnifiedControl "
    motion_unified: {
        func_name: Movej_to_namedPose,
        str_name: ['pose_name'],
        str_val:  ['init'],
    }
"
```

It looks awful, but it is only three parts:

1. `/motion_unified/control` - which phone number you are calling
2. `crb_ros_msg/srv/MotionUnifiedControl` - what kind of call this is
3. everything in quotes - what you are actually asking for

And the third part has an unusual design worth understanding, because it explains every service
example in their document. CASBOT put **all** their functions behind one phone number. So the
first thing inside the request is `func_name`, which says which function you actually want. The
rest are arguments, and they are passed as **parallel lists**: `str_name` lists the names of the
text arguments, `str_val` lists their values in the same order. There are matching pairs for
numbers (`int_name`/`int_val`, `double_name`/`double_val`).

So the block above reads: "call the function `Movej_to_namedPose`, with one text argument named
`pose_name` whose value is `init`." Which means: move to the pose saved in the configuration
under the name `init`.

Once you see that pattern, every service example in their document becomes readable. Lines
starting with `#` are commented out, i.e. inactive, which is how they show optional arguments.

---

## 12. Glossary

| Term | Chinese | Meaning |
|---|---|---|
| Action | | A ROS request for a long job that reports progress while it runs |
| Base / chassis | 底盘 | The wheeled platform. We never drive it |
| Command | | The pose you asked for, as opposed to the pose that happened |
| Control rate | | How many poses per second you send. Measured in Hz |
| DHCP | | The service that normally hands out IP addresses automatically |
| DoF (degree of freedom) | | One independently movable joint. This arm is 7-DoF |
| E-stop | 急停 | Emergency stop. A physical button that cuts motor power |
| End effector | | Whatever is mounted on the end of the arm: gripper or hand |
| Gripper | 二指夹爪 | The two-finger clamp. Never force it by hand while powered |
| Home / park pose | | The known safe pose you return the arms to |
| Hz (hertz) | | Times per second |
| IK (inverse kinematics) | | Computing joint angles from a desired hand position |
| IP address | | A machine's address on a network, e.g. 172.16.0.10 |
| Joint | 关节 | A place the arm bends. 7 per arm, numbered shoulder to hand |
| Joint limit | 限位 | The smallest and largest angle a joint can reach |
| Lifting column | 升降柱 | The vertical post that raises the upper body. We keep it down |
| Link | | The rigid segment between two joints |
| Measurement | | Where the joints actually are, as reported by the robot |
| Mocap (motion capture) | | Recording human 3D body motion over time |
| Movej | | Vendor function: move to a set of joint angles, one-off, with a speed setting |
| Movej_transparent | | Vendor topic: stream continuous poses at 50-200 Hz |
| Node | | One running program in a ROS system |
| Pose | | 14 numbers, one angle per arm joint. A single snapshot |
| Radian | 弧度 | The angle unit robots use. 1 rad = 57.3 degrees |
| Retargeting | | Converting motion from a human body to a robot body |
| ROS 2 | | The plumbing that lets a robot's many programs talk to each other |
| scp | | Secure copy: copy a file to another machine |
| Service | | A ROS request with one answer. For one-off commands |
| Soft E-stop | 软急停 | A software stop, weaker than the red button. On the gamepad |
| SSH | | A terminal window that runs on another machine |
| Static IP | | An address you set by hand instead of receiving automatically |
| Terminal | | A window where you type commands instead of clicking |
| Topic | | A ROS channel that broadcasts continuously. For streams of data |
| Trajectory | | A list of poses in order. A flipbook of motion |
| Waist | 腰部 | The single bending joint in the torso. We keep it at 0 |
| Zero pose | 零位姿态 | The arms-straight-out calibration pose. Press after transport |

---

## Where to go next

- **`OPERATING_GUIDE.md`** - the step-by-step checklist to follow at the robot.
- **`MOTIONS.md`** - what we need the robot to actually perform, and what is not built yet.
- **`VENDOR_BRIEF_CN.md`** - the one-page Chinese summary to send their engineers.
- **`README.md`** - the technical runbook for regenerating trajectories on the workstation.

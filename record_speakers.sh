#!/usr/bin/env bash
set -euo pipefail

STREAM=/home/casbot/stream_ros2.py
MOTIONS=/home/casbot/motions
AUDIO=/home/casbot/safe_sync

run_take()
{
    local take_number=$1
    local speaker=$2
    local variant=$3
    local trajectory=$4
    local audio=$5
    local video_speedup=$6

    echo
    echo "============================================================"
    echo "TAKE ${take_number}: ${speaker} / ${variant}"
    echo "Raw video: ${speaker}_${variant}_raw.mp4"
    echo "Shared audio: ${audio}"
    echo "Post-production gesture speedup: ${video_speedup}x"
    echo "Start a fresh camera recording before typing 'go'."
    echo "============================================================"

    python3 "$STREAM" \
        --traj "$trajectory" \
        --enable-feedback \
        --arms both \
        --split-arm-topics \
        --speed 0.25 \
        --command-rate 50 \
        --ramp 20 \
        --movej-first \
        --movej-vel 0.01 \
        --track-tol 0.15

    echo "CLEAN TAKE: ${speaker} / ${variant}"
}

run_take 01 neerja_forward presentation \
    "$MOTIONS/02_neerja_forward/presentation.npz" \
    "$AUDIO/02_neerja_forward.wav" 3.526160225500
run_take 02 neerja_forward tabletop \
    "$MOTIONS/02_neerja_forward/tabletop.npz" \
    "$AUDIO/02_neerja_forward.wav" 3.993471127160
run_take 03 neerja_forward casual \
    "$MOTIONS/02_neerja_forward/casual.npz" \
    "$AUDIO/02_neerja_forward.wav" 3.433737118416

run_take 04 sonia presentation \
    "$MOTIONS/03_sonia/presentation.npz" \
    "$AUDIO/03_sonia.wav" 3.588223572764
run_take 05 sonia tabletop \
    "$MOTIONS/03_sonia/tabletop.npz" \
    "$AUDIO/03_sonia.wav" 3.563951350628
run_take 06 sonia casual \
    "$MOTIONS/03_sonia/casual.npz" \
    "$AUDIO/03_sonia.wav" 3.995580209516

run_take 07 ava presentation \
    "$MOTIONS/04_ava/presentation.npz" \
    "$AUDIO/04_ava.wav" 3.998302736836
run_take 08 ava tabletop \
    "$MOTIONS/04_ava/tabletop.npz" \
    "$AUDIO/04_ava.wav" 3.942761044708
run_take 09 ava casual \
    "$MOTIONS/04_ava/casual.npz" \
    "$AUDIO/04_ava.wav" 3.968433393352

run_take 10 neerja_expressive presentation \
    "$MOTIONS/05_neerja_expressive/presentation.npz" \
    "$AUDIO/05_neerja_expressive.wav" 3.855373630388
run_take 11 neerja_expressive tabletop \
    "$MOTIONS/05_neerja_expressive/tabletop.npz" \
    "$AUDIO/05_neerja_expressive.wav" 3.993873596512
run_take 12 neerja_expressive casual \
    "$MOTIONS/05_neerja_expressive/casual.npz" \
    "$AUDIO/05_neerja_expressive.wav" 3.539371902648

echo
echo "ALL TWELVE SPEAKER TAKES FINISHED CLEANLY."

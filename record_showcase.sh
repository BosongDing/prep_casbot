#!/usr/bin/env bash
set -euo pipefail

STREAM=/home/casbot/stream_ros2.py

run_take()
{
    local label=$1
    local trajectory=$2
    local video_speedup=$3

    echo
    echo "============================================================"
    echo "RECORD: ${label}"
    echo "Post-production gesture speedup: ${video_speedup}x"
    echo "Start the camera before typing 'go'."
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

    echo "CLEAN TAKE: ${label}"
}

run_take \
    "01 Presentation -> showcase_presentation_raw.mp4" \
    "/home/casbot/presentation.npz" \
    "3.631109384612"

run_take \
    "02 Tabletop -> showcase_tabletop_raw.mp4" \
    "/home/casbot/tabletop.npz" \
    "3.943772458960"

run_take \
    "03 Casual -> showcase_casual_raw.mp4" \
    "/home/casbot/casual.npz" \
    "3.999109905184"

echo
echo "ALL THREE SHOWCASE TAKES FINISHED CLEANLY."
echo "Shared audio: /home/casbot/01_showcase.wav"

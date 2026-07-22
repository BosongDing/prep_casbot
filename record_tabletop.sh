#!/usr/bin/env bash
set -euo pipefail

STREAM=/home/casbot/stream_ros2.py
MOTIONS=/home/casbot/motions

run_take()
{
    local take_number=$1
    local speaker=$2
    local trajectory=$3
    local video_speedup=$4

    echo
    echo "============================================================"
    echo "TABLETOP TAKE ${take_number}: ${speaker}"
    echo "Raw video: ${speaker}_tabletop_raw.mp4"
    echo "Post-production gesture speedup: ${video_speedup}x"
    echo "Verify table clearance and start recording before typing 'go'."
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

    echo "CLEAN TABLETOP TAKE: ${speaker}"
}

echo "TABLETOP SESSION: place and secure the table before continuing."

run_take 01 neerja_forward \
    "$MOTIONS/02_neerja_forward/tabletop.npz" \
    3.993471127160
run_take 02 sonia \
    "$MOTIONS/03_sonia/tabletop.npz" \
    3.563951350628
run_take 03 ava \
    "$MOTIONS/04_ava/tabletop.npz" \
    3.942761044708
run_take 04 neerja_expressive \
    "$MOTIONS/05_neerja_expressive/tabletop.npz" \
    3.993873596512

echo
echo "ALL FOUR TABLETOP TAKES FINISHED CLEANLY."

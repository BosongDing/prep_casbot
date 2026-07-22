#!/usr/bin/env python3
"""Render the original TED-Expressive 126-D generations with their audio.

Each source NPZ contains three mean-subtracted 126-D direction-vector streams
(`presentation`, `seated_screen`, and `standing_studio`) and one shared audio
waveform.  The renderer decodes all 42 bones, including the articulated
fingers and face, and places the three conditions in one synchronized video.

Examples:

    python3 render_126d_skeleton.py --all --seconds 5
    python3 render_126d_skeleton.py \
        --input original_126d_sources/03_sonia.npz \
        --output previews/original_126d_skeleton/03_sonia.mp4

This is research code: malformed inputs and failed encoders raise immediately.
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation
import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "original_126d_sources"
OUTPUT_DIR = ROOT / "previews" / "original_126d_skeleton"
MEAN_PATH = SOURCE_DIR / "ted_expressive_mean_dir_vec.npy"

STREAMS = (
    ("presentation", "PRESENTATION", "#2878c7"),
    ("seated_screen", "TABLETOP", "#16a085"),
    ("standing_studio", "CASUAL", "#e39b00"),
)

# TED-Expressive skeleton, in topological order. Each tuple is
# (parent joint, child joint, canonical bone length).
DIR_VEC_PAIRS = (
    (0, 1, 0.26),
    (1, 2, 0.22), (1, 3, 0.22),
    (2, 4, 0.36), (4, 6, 0.33),
    (6, 8, 0.137), (8, 9, 0.044), (9, 10, 0.031),
    (6, 11, 0.144), (11, 12, 0.042), (12, 13, 0.033),
    (6, 14, 0.127), (14, 15, 0.027), (15, 16, 0.026),
    (6, 17, 0.134), (17, 18, 0.039), (18, 19, 0.033),
    (6, 20, 0.068), (20, 21, 0.042), (21, 22, 0.036),
    (3, 5, 0.36), (5, 7, 0.33),
    (7, 23, 0.137), (23, 24, 0.044), (24, 25, 0.031),
    (7, 26, 0.144), (26, 27, 0.042), (27, 28, 0.033),
    (7, 29, 0.127), (29, 30, 0.027), (30, 31, 0.026),
    (7, 32, 0.134), (32, 33, 0.039), (33, 34, 0.033),
    (7, 35, 0.068), (35, 36, 0.042), (36, 37, 0.036),
    (1, 38, 0.18), (38, 39, 0.14), (38, 40, 0.14),
    (39, 41, 0.15), (40, 42, 0.15),
)

LEFT_BONES = frozenset(range(3, 20))
RIGHT_BONES = frozenset(range(20, 37))
FACE_BONES = frozenset(range(37, 42))
LEFT_COLOR = "#3d7fd3"
RIGHT_COLOR = "#d45878"
BODY_COLOR = "#303743"
FACE_COLOR = "#687386"


def decode_direction_vectors(vectors: np.ndarray, mean: np.ndarray) -> np.ndarray:
    assert vectors.ndim == 2 and vectors.shape[1] == 126, vectors.shape
    direction = (vectors.astype(np.float64) + mean[None, :]).reshape(-1, 42, 3)
    norms = np.linalg.norm(direction, axis=2)
    assert np.isfinite(direction).all()
    assert np.min(norms) > 1e-8
    direction /= norms[:, :, None]

    joints = np.zeros((len(direction), 43, 3), dtype=np.float64)
    for bone, (parent, child, length) in enumerate(DIR_VEC_PAIRS):
        joints[:, child] = joints[:, parent] + length * direction[:, bone]
    return joints


def interpolate(sequence: np.ndarray, source_fps: float, output_fps: float,
                duration: float) -> np.ndarray:
    output_count = int(round(duration * output_fps))
    output_time = np.arange(output_count, dtype=np.float64) / output_fps
    source_position = np.minimum(output_time * source_fps, len(sequence) - 1)
    lo = np.floor(source_position).astype(np.int64)
    hi = np.minimum(lo + 1, len(sequence) - 1)
    alpha = (source_position - lo)[:, None, None]
    return sequence[lo] * (1.0 - alpha) + sequence[hi] * alpha


def bone_color(index: int) -> str:
    if index in LEFT_BONES:
        return LEFT_COLOR
    if index in RIGHT_BONES:
        return RIGHT_COLOR
    if index in FACE_BONES:
        return FACE_COLOR
    return BODY_COLOR


def shared_bounds(sequences: list[np.ndarray]) -> tuple[tuple[float, float], ...]:
    points = np.concatenate(sequences, axis=0).reshape(-1, 3)
    horizontal = points[:, 0]
    depth = points[:, 2]
    vertical = -points[:, 1]
    center = np.array([
        (horizontal.min() + horizontal.max()) / 2,
        (depth.min() + depth.max()) / 2,
        (vertical.min() + vertical.max()) / 2,
    ])
    radius = 0.55 * max(
        np.ptp(horizontal), np.ptp(depth), np.ptp(vertical), 1e-3
    )
    return tuple((float(c - radius), float(c + radius)) for c in center)


def render(source_path: Path, output_path: Path, seconds: float | None,
           output_fps: float) -> None:
    source = np.load(source_path, allow_pickle=False)
    assert set(key for key, _, _ in STREAMS).issubset(source.files)
    assert {"audio", "sr", "fps"}.issubset(source.files)

    source_fps = float(source["fps"])
    sample_rate = int(source["sr"])
    audio = np.asarray(source["audio"], dtype=np.float32)
    mean = np.load(MEAN_PATH, allow_pickle=False).astype(np.float64).reshape(-1)
    assert mean.shape == (126,), mean.shape
    assert audio.ndim == 1 and np.isfinite(audio).all()
    assert source_fps > 0 and sample_rate > 0 and output_fps > 0

    raw_streams = [np.asarray(source[key]) for key, _, _ in STREAMS]
    frame_count = min(len(stream) for stream in raw_streams)
    duration = min(frame_count / source_fps, len(audio) / sample_rate)
    if seconds is not None:
        assert seconds > 0
        duration = min(duration, seconds)
    assert duration > 0

    source_frames = int(np.ceil(duration * source_fps))
    poses = [
        interpolate(
            decode_direction_vectors(stream[:source_frames], mean),
            source_fps,
            output_fps,
            duration,
        )
        for stream in raw_streams
    ]
    audio = audio[:int(round(duration * sample_rate))]
    assert len({len(pose) for pose in poses}) == 1
    bounds = shared_bounds(poses)

    fig = plt.figure(figsize=(13.44, 5.12), dpi=100, facecolor="#f7f5f1")
    fig.suptitle(
        "ORIGINAL GENERATED MOTION · TED-EXPRESSIVE 126-D SKELETON",
        x=0.5,
        y=0.985,
        fontsize=14,
        fontweight="bold",
        color="#202734",
    )
    fig.text(
        0.5,
        0.94,
        "same speech · three independently generated setting-conditioned motions",
        ha="center",
        va="center",
        fontsize=9,
        color="#5b6471",
    )

    panels = []
    for panel_index, ((_, title, title_color), pose) in enumerate(zip(STREAMS, poses)):
        axis = fig.add_subplot(1, 3, panel_index + 1, projection="3d")
        axis.set_facecolor("#f7f5f1")
        axis.set_xlim(*bounds[0])
        axis.set_ylim(*bounds[1])
        axis.set_zlim(*bounds[2])
        axis.set_box_aspect((1, 1, 1))
        axis.set_proj_type("ortho")
        axis.view_init(elev=8, azim=-90)
        axis.set_axis_off()
        axis.set_title(title, fontsize=15, fontweight="bold", color=title_color, pad=1)

        lines = []
        for bone, _ in enumerate(DIR_VEC_PAIRS):
            linewidth = 2.7 if bone < 5 or bone in (20, 21) else 1.45
            line = axis.plot([], [], [], color=bone_color(bone),
                             linewidth=linewidth, solid_capstyle="round")[0]
            lines.append(line)
        joints = axis.scatter([], [], [], s=7, c=BODY_COLOR, depthshade=False)
        panels.append((pose, lines, joints))

    time_text = fig.text(
        0.5, 0.028, "", ha="center", va="center", fontsize=9, color="#68717e"
    )
    fig.subplots_adjust(left=0.015, right=0.985, top=0.89, bottom=0.075, wspace=0.015)

    def animate(frame: int):
        artists = []
        for pose, lines, joint_artist in panels:
            points = pose[frame]
            horizontal = points[:, 0]
            depth = points[:, 2]
            vertical = -points[:, 1]
            for line, (parent, child, _) in zip(lines, DIR_VEC_PAIRS):
                line.set_data(
                    [horizontal[parent], horizontal[child]],
                    [depth[parent], depth[child]],
                )
                line.set_3d_properties([vertical[parent], vertical[child]])
            joint_artist._offsets3d = (horizontal, depth, vertical)
            artists.extend(lines)
            artists.append(joint_artist)
        time_text.set_text(f"{frame / output_fps:05.2f} s")
        artists.append(time_text)
        return artists

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="render_126d_") as temp_dir:
        temp = Path(temp_dir)
        silent_path = temp / "silent.mp4"
        audio_path = temp / "audio.wav"
        animation = FuncAnimation(
            fig,
            animate,
            frames=len(poses[0]),
            interval=1000.0 / output_fps,
            blit=False,
        )
        animation.save(
            silent_path,
            writer=FFMpegWriter(
                fps=output_fps,
                codec="libx264",
                bitrate=4500,
                extra_args=["-pix_fmt", "yuv420p"],
            ),
            dpi=100,
        )
        plt.close(fig)
        sf.write(audio_path, audio, sample_rate, subtype="PCM_16")
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-i", str(silent_path),
                "-i", str(audio_path),
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", f"{duration:.9f}",
                str(output_path),
            ],
            check=True,
        )

    print(
        f"rendered {output_path} from {source_path}: "
        f"{len(poses[0])} frames @ {output_fps:g} fps, {duration:.3f} s"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--all", action="store_true", help="render every bundled source")
    mode.add_argument("--input", type=Path, help="one generated 126-D NPZ")
    parser.add_argument("--output", type=Path, help="output path for --input")
    parser.add_argument("--seconds", type=float, default=None, help="crop from t=0")
    parser.add_argument("--output-fps", type=float, default=30.0)
    args = parser.parse_args()

    if args.all:
        assert args.output is None
        sources = sorted(SOURCE_DIR.glob("[0-9][0-9]_*.npz"))
        assert len(sources) == 5, sources
        for source in sources:
            render(source, OUTPUT_DIR / f"{source.stem}.mp4", args.seconds, args.output_fps)
    else:
        assert args.input is not None and args.output is not None
        render(args.input, args.output, args.seconds, args.output_fps)


if __name__ == "__main__":
    main()

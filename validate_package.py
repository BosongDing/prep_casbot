#!/usr/bin/env python3
"""Assert that every packaged CASBOT trajectory and audio file is deployable.

This deliberately has no recovery path: the first violated invariant raises and
stops. It needs only Python, NumPy, and the standard library.
"""
import hashlib
import json
from pathlib import Path
import wave

import numpy as np

from stream_ros2 import resample_speed


ROOT = Path(__file__).resolve().parent
CONDITIONS = {"presentation", "tabletop", "casual"}
JOINT_LIMIT = np.array([3.1, 2.268, 3.1, 2.355, 3.1, 2.233, 6.28] * 2)
LIMIT_MARGIN = 0.05
VMAX = 1.5
AMAX = 40.0


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((ROOT / "package_manifest.json").read_text())
    long_manifest = json.loads((ROOT / "long_manifest.json").read_text())
    collision = json.loads((ROOT / "audits/collision_audit.json").read_text())
    expected_names = manifest["joint_order"]
    assert manifest["conditions"] == ["presentation", "tabletop", "casual"]
    assert manifest["command_rate_hz"] == 100.0

    paths = sorted((ROOT / "motions").glob("*/*.npz"))
    expected_paths = {
        ROOT / "motions" / set_name / f"{condition}.npz"
        for set_name in manifest["sets"]
        for condition in CONDITIONS
    }
    assert set(paths) == expected_paths
    short_relative_paths = {str(path.relative_to(ROOT)) for path in paths}

    report = {"motion_count": len(paths), "sets": {}, "files": {}}
    for set_name, set_meta in manifest["sets"].items():
        set_dir = ROOT / "motions" / set_name
        assert {path.stem for path in set_dir.glob("*.npz")} == CONDITIONS
        sync_duration = float(set_meta["safe_sync_duration_s"])
        assert sync_duration >= 5.0

        reference_audio = ROOT / set_meta["audio_reference"]
        sync_audio = ROOT / set_meta["audio_safe_sync"]
        for audio, expected_duration in ((reference_audio, 5.0),
                                         (sync_audio, sync_duration)):
            with wave.open(str(audio), "rb") as wav:
                assert wav.getnchannels() == 1
                assert wav.getsampwidth() == 2
                assert wav.getframerate() == 16000
                duration = wav.getnframes() / wav.getframerate()
            assert abs(duration - expected_duration) <= 1.0 / 16000.0
            report["files"][str(audio.relative_to(ROOT))] = sha256(audio)

        overview = ROOT / "previews/original_timing" / f"{set_name}_same_audio.mp4"
        assert overview.is_file() and overview.stat().st_size > 0
        report["files"][str(overview.relative_to(ROOT))] = sha256(overview)

        set_report = {}
        for condition in sorted(CONDITIONS):
            path = set_dir / f"{condition}.npz"
            data = np.load(path, allow_pickle=True)
            assert set(data.files) >= {"names", "q", "rate", "q_start", "vmax"}
            names = [str(name) for name in data["names"]]
            q = np.asarray(data["q"], dtype=float)
            rate = float(data["rate"])
            assert names == expected_names
            assert q.ndim == 2 and q.shape == (247, 14)
            assert np.isfinite(q).all()
            assert rate > 0.0
            assert np.array_equal(q[0].astype(np.float32), data["q_start"])
            assert float(data["vmax"]) == VMAX
            assert (q >= -JOINT_LIMIT + LIMIT_MARGIN - 1e-6).all()
            assert (q <= JOINT_LIMIT - LIMIT_MARGIN + 1e-6).all()

            peak_velocity = np.abs(np.diff(q, axis=0)).max() * rate
            peak_acceleration = np.abs(np.diff(q, n=2, axis=0)).max() * rate * rate
            assert peak_velocity <= VMAX + 2e-5
            assert peak_acceleration <= AMAX + 5e-4

            speed = float(set_meta["speed"][condition])
            assert 0.0 < speed <= 1.0
            q100 = resample_speed(q, rate, 100.0, speed)
            assert np.allclose(q100[0], q[0])
            assert np.allclose(q100[-1], q[-1])
            playback_duration = (len(q100) - 1) / 100.0
            assert abs(playback_duration - sync_duration) <= 0.0051
            for test_speed in (0.25, 0.5, 1.0):
                test_q = resample_speed(q, rate, 100.0, test_speed)
                assert np.allclose(test_q[0], q[0])
                assert np.allclose(test_q[-1], q[-1])

            exact_preview = ROOT / "previews/exact_robot_paths" / set_name / f"{condition}.mp4"
            assert exact_preview.is_file() and exact_preview.stat().st_size > 0
            relative = str(path.relative_to(ROOT))
            assert collision["motions"][relative] == "pass_no_self_penetration"
            report["files"][relative] = sha256(path)
            report["files"][str(exact_preview.relative_to(ROOT))] = sha256(exact_preview)
            set_report[condition] = {
                "stored_rate_hz": rate,
                "stored_duration_s": (len(q) - 1) / rate,
                "safe_sync_speed": speed,
                "safe_sync_duration_s": playback_duration,
                "peak_velocity_rad_s": peak_velocity,
                "peak_acceleration_rad_s2": peak_acceleration,
                "collision_audit": collision["motions"][relative]
            }
        report["sets"][set_name] = set_report

    long_paths = sorted((ROOT / "motions_long").glob("*/*.npz"))
    expected_long_paths = {
        ROOT / "motions_long" / set_name / f"{condition}.npz"
        for set_name in long_manifest["sets"]
        for condition in CONDITIONS
    }
    assert set(long_paths) == expected_long_paths
    long_relative_paths = {str(path.relative_to(ROOT)) for path in long_paths}
    assert set(collision["motions"]) == short_relative_paths | long_relative_paths
    report["long_motion_count"] = len(long_paths)
    report["long_sets"] = {}

    for set_name, set_meta in long_manifest["sets"].items():
        set_dir = ROOT / "motions_long" / set_name
        assert {path.stem for path in set_dir.glob("*.npz")} == CONDITIONS
        sync_duration = float(set_meta["safe_sync_duration_s"])
        assert 12.0 <= sync_duration <= 20.0

        reference_audio = ROOT / set_meta["audio_reference"]
        sync_audio = ROOT / set_meta["audio_safe_sync"]
        for audio, expected_duration in (
                (reference_audio, float(set_meta["audio_reference_duration_s"])),
                (sync_audio, sync_duration)):
            with wave.open(str(audio), "rb") as wav:
                assert wav.getnchannels() == 1
                assert wav.getsampwidth() == 2
                assert wav.getframerate() == 16000
                duration = wav.getnframes() / wav.getframerate()
            assert abs(duration - expected_duration) <= 1.0 / 16000.0
            report["files"][str(audio.relative_to(ROOT))] = sha256(audio)

        for preview_kind in ("original_timing", "safe_robot_timing"):
            preview = ROOT / "previews_long" / preview_kind / f"{set_name}.mp4"
            assert preview.is_file() and preview.stat().st_size > 0
            report["files"][str(preview.relative_to(ROOT))] = sha256(preview)

        set_report = {}
        for condition in sorted(CONDITIONS):
            path = set_dir / f"{condition}.npz"
            data = np.load(path, allow_pickle=True)
            assert set(data.files) >= {
                "names", "q", "rate", "q_start", "vmax", "amp"
            }
            names = [str(name) for name in data["names"]]
            q = np.asarray(data["q"], dtype=float)
            rate = float(data["rate"])
            assert names == expected_names
            assert q.ndim == 2 and q.shape[0] >= 600 and q.shape[1] == 14
            assert np.isfinite(q).all()
            assert rate > 0.0
            assert np.array_equal(q[0].astype(np.float32), data["q_start"])
            assert float(data["vmax"]) == VMAX
            assert float(data["amp"]) == float(set_meta["amp"])
            assert (q >= -JOINT_LIMIT + LIMIT_MARGIN - 1e-6).all()
            assert (q <= JOINT_LIMIT - LIMIT_MARGIN + 1e-6).all()

            peak_velocity = np.abs(np.diff(q, axis=0)).max() * rate
            peak_acceleration = np.abs(np.diff(q, n=2, axis=0)).max() * rate * rate
            assert peak_velocity <= VMAX + 2e-5
            assert peak_acceleration <= AMAX + 5e-4

            speed = float(set_meta["speed"][condition])
            assert 0.0 < speed <= 1.0
            q100 = resample_speed(q, rate, 100.0, speed)
            assert np.allclose(q100[0], q[0])
            assert np.allclose(q100[-1], q[-1])
            playback_duration = (len(q100) - 1) / 100.0
            assert abs(playback_duration - sync_duration) <= 0.0051

            exact_preview = ROOT / "previews_long/exact_robot_paths" / \
                set_name / f"{condition}.mp4"
            assert exact_preview.is_file() and exact_preview.stat().st_size > 0
            relative = str(path.relative_to(ROOT))
            assert collision["motions"][relative] == "pass_no_self_penetration"
            report["files"][relative] = sha256(path)
            report["files"][str(exact_preview.relative_to(ROOT))] = sha256(exact_preview)
            set_report[condition] = {
                "frames": len(q),
                "stored_rate_hz": rate,
                "stored_duration_s": (len(q) - 1) / rate,
                "amplitude": float(data["amp"]),
                "safe_sync_speed": speed,
                "safe_sync_duration_s": playback_duration,
                "peak_velocity_rad_s": peak_velocity,
                "peak_acceleration_rad_s2": peak_acceleration,
                "collision_audit": collision["motions"][relative]
            }
        report["long_sets"][set_name] = set_report

    report_path = ROOT / "audits/validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"PASS: {len(paths)} short + {len(long_paths)} long trajectories, "
          f"{len(manifest['sets']) + len(long_manifest['sets'])} same-audio trios")
    print(f"wrote {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

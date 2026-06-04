from pathlib import Path
from datetime import datetime


LOGS_DIR = Path("logs")


def reset_logs_dir():
    LOGS_DIR.mkdir(exist_ok=True)

    for file_path in LOGS_DIR.iterdir():
        if file_path.is_file():
            file_path.unlink()


def format_stage_timings(stage_timings: dict) -> str:
    if not stage_timings:
        return "No stage timings recorded."

    lines = []
    for key, value in stage_timings.items():
        if isinstance(value, (int, float)):
            lines.append(f"{key}: {value:.6f} s")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)


def write_run_log(
    run_index: int,
    backend_mode: str,
    scene_name: str,
    width: int,
    height: int,
    max_depth: int,
    workers: int,
    tile_size: int,
    total_time: float,
    stage_timings: dict
):
    filename = LOGS_DIR / f"run_{run_index:02d}.txt"

    content = []
    content.append(f"Run: {run_index:02d}")
    content.append(f"Timestamp: {datetime.now().isoformat(timespec='seconds')}")
    content.append(f"Backend: {backend_mode}")
    content.append(f"Scene: {scene_name}")
    content.append(f"Resolution: {width}x{height}")
    content.append(f"Max depth: {max_depth}")
    content.append(f"Workers: {workers}")
    content.append(f"Tile size: {tile_size}")
    content.append("")
    content.append("Stage timings:")
    content.append(format_stage_timings(stage_timings))
    content.append("")
    content.append(f"Total run time: {total_time:.6f} s")

    filename.write_text("\n".join(content), encoding="utf-8")


def write_summary_log(
    backend_mode: str,
    scene_name: str,
    width: int,
    height: int,
    max_depth: int,
    workers: int,
    tile_size: int,
    all_run_times: list[float],
    average_time: float,
    average_without_first: float | None,
    best_time: float,
    worst_time: float,
    build_stage_timings: dict
):
    filename = LOGS_DIR / "summary.txt"

    content = []
    content.append("Benchmark Summary")
    content.append(f"Timestamp: {datetime.now().isoformat(timespec='seconds')}")
    content.append("")
    content.append(f"Backend: {backend_mode}")
    content.append(f"Scene: {scene_name}")
    content.append(f"Resolution: {width}x{height}")
    content.append(f"Max depth: {max_depth}")
    content.append(f"Workers: {workers}")
    content.append(f"Tile size: {tile_size}")
    content.append("")
    content.append("Build / setup timings:")
    content.append(format_stage_timings(build_stage_timings))
    content.append("")
    content.append("All run times:")
    for i, t in enumerate(all_run_times, start=1):
        content.append(f"Run {i:02d}: {t:.6f} s")
    content.append("")
    content.append(f"Average time: {average_time:.6f} s")
    if average_without_first is not None:
        content.append(f"Average without first run: {average_without_first:.6f} s")
    content.append(f"Best time: {best_time:.6f} s")
    content.append(f"Worst time: {worst_time:.6f} s")

    filename.write_text("\n".join(content), encoding="utf-8")
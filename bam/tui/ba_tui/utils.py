from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path


def detect_hardware() -> dict[str, str | int]:
    cpu = _detect_cpu() or platform.machine() or "Unknown"
    cores = _detect_cores()
    ram = _detect_ram()

    gpu, gpu_count = _detect_gpu()
    return {
        "cpu": cpu,
        "cores": cores,
        "ram": ram,
        "gpu": gpu,
        "gpu_count": gpu_count,
    }


def _detect_cpu() -> str:
    try:
        cpuinfo = Path("/proc/cpuinfo")
        if cpuinfo.exists():
            for line in cpuinfo.read_text().splitlines():
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["lscpu"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass

    return platform.processor()


def _detect_ram() -> str:
    try:
        meminfo = Path("/proc/meminfo")
        if meminfo.exists():
            for line in meminfo.read_text().splitlines():
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    if len(parts) >= 2:
                        kb = int(parts[1])
                        gb = kb / (1024**2)
                        return f"{int(round(gb))} GB"
    except Exception:
        pass

    try:
        import psutil  # type: ignore

        total_gb = int(psutil.virtual_memory().total // (1024**3))
        return f"{total_gb} GB"
    except Exception:
        return ""


def _detect_cores() -> str:
    try:
        count = os.cpu_count()
        if count:
            return str(count)
    except Exception:
        pass
    return ""


def _detect_gpu() -> tuple[str, int]:
    """Detect GPU(s) and return (gpu_name, gpu_count).

    Groups identical GPUs together and returns the count separately.
    Returns: (gpu_description, gpu_count)
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            lines = [
                line.strip() for line in result.stdout.splitlines() if line.strip()
            ]
            if lines:
                # Group GPUs by name and count
                from collections import Counter

                gpu_counts = Counter(lines)

                # Format grouped GPUs
                gpu_parts = []
                for gpu_name, count in gpu_counts.items():
                    if count > 1:
                        gpu_parts.append(f"{count}x {gpu_name}")
                    else:
                        gpu_parts.append(gpu_name)

                gpu_description = ", ".join(gpu_parts)
                total_count = len(lines)

                return (gpu_description, total_count)
    except Exception:
        return ("", 0)
    return ("", 0)


def detect_git_remote(project_root: Path) -> str:
    config = project_root / ".git" / "config"
    if not config.exists():
        return ""

    current_remote = ""
    url = ""
    try:
        for raw_line in config.read_text().splitlines():
            line = raw_line.strip()
            if line.startswith("[remote "):
                current_remote = ""
                if '"' in line:
                    current_remote = line.split('"', 2)[1]
                continue
            if current_remote and line.startswith("url"):
                _, value = line.split("=", 1)
                candidate = value.strip()
                if current_remote == "origin":
                    return candidate
                if not url:
                    url = candidate
        return url
    except Exception:
        return ""

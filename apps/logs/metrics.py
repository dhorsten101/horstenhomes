from __future__ import annotations

import os
import shutil
from dataclasses import dataclass


@dataclass(frozen=True)
class SystemMetrics:
	loadavg_1: float | None
	loadavg_5: float | None
	loadavg_15: float | None
	mem_total_kb: int | None
	mem_available_kb: int | None
	rss_kb: int | None
	disk_total_bytes: int
	disk_used_bytes: int
	disk_free_bytes: int


def _read_meminfo() -> dict[str, int]:
	out: dict[str, int] = {}
	try:
		with open("/proc/meminfo", "r", encoding="utf-8") as f:
			for line in f:
				parts = line.split()
				if len(parts) >= 2 and parts[0].endswith(":"):
					key = parts[0][:-1]
					out[key] = int(parts[1])
	except Exception:
		pass
	return out


def _read_rss_kb() -> int | None:
	try:
		with open("/proc/self/status", "r", encoding="utf-8") as f:
			for line in f:
				if line.startswith("VmRSS:"):
					return int(line.split()[1])
	except Exception:
		return None
	return None


def get_system_metrics() -> SystemMetrics:
	try:
		la = os.getloadavg()
		load1, load5, load15 = float(la[0]), float(la[1]), float(la[2])
	except Exception:
		load1 = load5 = load15 = None

	mem = _read_meminfo()
	total = mem.get("MemTotal")
	avail = mem.get("MemAvailable")
	rss = _read_rss_kb()

	du = shutil.disk_usage("/")
	return SystemMetrics(
		loadavg_1=load1,
		loadavg_5=load5,
		loadavg_15=load15,
		mem_total_kb=total,
		mem_available_kb=avail,
		rss_kb=rss,
		disk_total_bytes=du.total,
		disk_used_bytes=du.used,
		disk_free_bytes=du.free,
	)


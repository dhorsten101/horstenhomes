from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from django.db import connection


def list_test_files(*, app_label: str, base_dir: Path) -> list[str]:
	"""
	Best-effort list of test modules for UI display.
	"""
	try:
		app_name = app_label.split(".", 1)[1]
		test_dir = base_dir / "apps" / app_name / "tests"
		if not test_dir.exists() or not test_dir.is_dir():
			return []
		return sorted(p.name for p in test_dir.glob("test*.py") if p.is_file())
	except Exception:
		return []


@dataclass(frozen=True)
class TestRunResult:
	app: str
	ok: bool
	returncode: int
	duration_ms: int
	output: str


def run_django_tests(*, app_label: str, timeout_s: int = 600) -> TestRunResult:
	"""
	Run `manage.py test <app_label>` and capture output.
	"""
	start = time.monotonic()
	res = subprocess.run(
		[
			sys.executable,
			"manage.py",
			"test",
			app_label,
			"-v",
			"2",
			"--keepdb",
			"--noinput",
		],
		check=False,
		capture_output=True,
		text=True,
		timeout=timeout_s,
	)
	duration_ms = int((time.monotonic() - start) * 1000)
	out = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
	out = out.strip()
	max_len = 40_000
	if len(out) > max_len:
		out = out[:max_len] + "\n\n... (truncated) ..."
	return TestRunResult(app=app_label, ok=res.returncode == 0, returncode=res.returncode, duration_ms=duration_ms, output=out)


def build_tenant_switch_rows(
	*,
	tenants: list,
	primary_domains: dict[int, str],
	request_host: str,
	request_scheme: str,
	base_domain: str,
) -> list[dict]:
	"""
	Build rows used by Platform's "switch tenant" UI.

	Returns list of:
	  { tenant, domain, login_url, crm_url }
	"""
	host = request_host or ""
	port = ""
	if ":" in host:
		port = host.split(":", 1)[1].strip()
	if port in {"80", "443"}:
		port = ""

	scheme = request_scheme or "http"
	rows: list[dict] = []
	for t in tenants:
		domain = primary_domains.get(t.id) or f"{t.slug}.{base_domain}"
		tenant_host = f"{domain}:{port}" if port else domain
		rows.append(
			{
				"tenant": t,
				"domain": domain,
				"login_url": f"{scheme}://{tenant_host}/login/",
				"crm_url": f"{scheme}://{tenant_host}/crm/",
			}
		)
	return rows


def get_pg_stat_statements(
	*,
	limit: int = 50,
	schema_filter: str = "",
) -> tuple[list[dict], list[dict], list[dict]]:
	"""
	Read pg_stat_statements and return (top_total, top_mean, top_calls).

	Raises if pg_stat_statements is unavailable.
	"""
	limit = min(int(limit or 50), 200)
	schema_filter = (schema_filter or "").strip().lower()

	def _fetch(order_sql: str):
		# Try modern pg_stat_statements column names first, then fall back.
		stat_queries: list[str] = [
			f"""
			SELECT
			  queryid,
			  calls,
			  total_exec_time AS total_ms,
			  mean_exec_time AS mean_ms,
			  rows,
			  shared_blks_hit,
			  shared_blks_read,
			  temp_blks_written,
			  query
			FROM pg_stat_statements
			ORDER BY {order_sql}
			LIMIT %s
			""",
			f"""
			SELECT
			  queryid,
			  calls,
			  total_time AS total_ms,
			  mean_time AS mean_ms,
			  rows,
			  shared_blks_hit,
			  shared_blks_read,
			  temp_blks_written,
			  query
			FROM pg_stat_statements
			ORDER BY {order_sql.replace("total_exec_time", "total_time").replace("mean_exec_time", "mean_time")}
			LIMIT %s
			""",
		]

		last_exc: Exception | None = None
		rows: list[dict] = []
		for sql in stat_queries:
			try:
				with connection.cursor() as cur:
					cur.execute(sql, [limit])
					cols = [c[0] for c in cur.description]
					rows = [dict(zip(cols, r, strict=False)) for r in cur.fetchall()]
					break
			except Exception as e:
				last_exc = e
				rows = []
				continue

		if not rows and last_exc is not None:
			raise last_exc

		if schema_filter:
			sf = schema_filter

			def match(row) -> bool:
				q = (row.get("query") or "").lower()
				return (f"{sf}." in q) or (f"\"{sf}\"." in q)

			rows = [r for r in rows if match(r)]

		for r in rows:
			q = (r.get("query") or "").strip()
			r["query_short"] = (q[:300] + "…") if len(q) > 300 else q

		return rows

	top_total = _fetch("total_exec_time DESC")
	top_mean = _fetch("mean_exec_time DESC")
	top_calls = _fetch("calls DESC")
	return top_total, top_mean, top_calls


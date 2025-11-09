# import pytest
# import json
# import os
# from datetime import datetime, timedelta
# from generate_report import load_report_data, generate_html_report, send_email, calculate_percentage
#
# # --- Configuration ---
# REPORT_FILE = "report_data.json"
# DAYS_TO_KEEP = 7
# REPORT_TITLE = "Comprehensive Automation Test Report"
# PROJECT_NAME = "Project Phoenix"
# DEFAULT_ENVIRONMENT = "staging"  # Default environment if not specified
#
#
# # --- Utility Functions ---
#
# def load_report_data():
#     """Loads existing report data from the JSON file."""
#     if not os.path.exists(REPORT_FILE):
#         return {
#             "report_title": REPORT_TITLE,
#             "project_name": PROJECT_NAME,
#             "environments": {
#                 "dev": {"trend_data": []},
#                 "staging": {"trend_data": []},
#                 "prod": {"trend_data": []}
#             }
#         }
#     try:
#         with open(REPORT_FILE, 'r') as f:
#             data = json.load(f)
#             # Ensure the environment keys exist in the loaded data
#             if "environments" not in data:
#                 data["environments"] = {
#                     "dev": {"trend_data": []},
#                     "staging": {"trend_data": []},
#                     "prod": {"trend_data": []}
#                 }
#             for env in ["dev", "staging", "prod"]:
#                 if env not in data["environments"]:
#                     data["environments"][env] = {"trend_data": []}
#             return data
#     except (json.JSONDecodeError, FileNotFoundError):
#         print(
#             f"Warning: Could not load or decode existing report data from {REPORT_FILE}. Starting with fresh data structure.")
#         return load_report_data()  # Return the default structure
#
#
# def save_report_data(data):
#     """Saves the updated report data to the JSON file."""
#     with open(REPORT_FILE, 'w') as f:
#         json.dump(data, f, indent=4)
#
#
# def prune_old_data(trend_data):
#     """Removes trend data older than DAYS_TO_KEEP."""
#     cutoff_date = (datetime.now() - timedelta(days=DAYS_TO_KEEP)).date()
#
#     # Filter out records older than the cutoff date
#     new_trend_data = [
#         record for record in trend_data
#         if datetime.strptime(record["date"], "%Y-%m-%d").date() >= cutoff_date
#     ]
#     return new_trend_data
#
#
# def update_trend_data(trend_data, new_data):
#     """
#     Updates the trend data:
#     1. Removes any existing entry for the current day.
#     2. Appends the new data.
#     """
#     current_date_str = new_data["date"]
#
#     # Remove existing entry for today
#     trend_data = [
#         record for record in trend_data
#         if record["date"] != current_date_str
#     ]
#
#     # Append the new data
#     trend_data.append(new_data)
#
#     return trend_data
#
#
# # --- Pytest Hooks ---
#
# def pytest_addoption(parser):
#     """Adds command line option to specify the environment."""
#     parser.addoption(
#         "--env",
#         action="store",
#         default=DEFAULT_ENVIRONMENT,
#         choices=["dev", "staging", "prod"],
#         help="Environment to run tests against: dev, staging, or prod"
#     )
#
#
# @pytest.fixture(scope="session")
# def env(request):
#     """Fixture to provide the environment to tests and hooks."""
#     return request.config.getoption("--env")
#
#
# @pytest.hookimpl(tryfirst=True, hookwrapper=True)
# def pytest_runtestloop(session):
#     """
#     Hook to initialize and finalize the reporting process.
#     """
#     # Get the environment from the fixture
#     environment = session.config.getoption("--env")
#
#     # Initialize session data storage
#     session.results = {
#         "passed": 0,
#         "failed": 0,
#         "skipped": 0,
#         "total": 0,
#         "package_tag_summary": {}  # New structure for package-wise and tag-wise counts
#     }
#
#     # Execute all tests
#     yield
#
#     # --- Finalization (After all tests are done) ---
#
#     # 1. Load existing data
#     report_data = load_report_data()
#
#     # 2. Get the environment-specific trend data
#     env_data = report_data["environments"].get(environment, {"trend_data": []})
#     trend_data = env_data["trend_data"]
#
#     # 3. Prepare new trend entry
#     current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     current_date_str = datetime.now().strftime("%Y-%m-%d")
#
#     new_trend_entry = {
#         "date": current_date_str,
#         "timestamp": current_time_str,
#         "total": session.results["total"],
#         "passed": session.results["passed"],
#         "failed": session.results["failed"],
#         "skipped": session.results["skipped"],
#         "package_tag_summary": session.results["package_tag_summary"]  # Include package and tag summary
#     }
#
#     # 4. Update and prune trend data
#     trend_data = update_trend_data(trend_data, new_trend_entry)
#     trend_data = prune_old_data(trend_data)
#
#     # 5. Update the main report structure with the new trend data
#     report_data["environments"][environment]["trend_data"] = trend_data
#
#     # 6. Save the final data
#     save_report_data(report_data)
#     print(
#         f"\n[Pytest Report Generator] Successfully updated report data for environment '{environment}' in {REPORT_FILE}")
#
#     # 7. Generate and Send Email Report
#     try:
#         # Extract the current run data from the last entry in the trend data
#         if not trend_data:
#             print(
#                 f"[Pytest Report Generator] No test data found for environment '{environment}'. Skipping email generation.")
#             return
#
#         current_run_data = trend_data[-1]
#
#         # Create a temporary structure for generate_report.py
#         final_report_data = {
#             "report_title": report_data["report_title"],
#             "project_name": report_data["project_name"],
#             "environment": environment.capitalize(),
#             "current_run": current_run_data,
#             "trend_data": trend_data
#         }
#
#         # Generate HTML
#         html_report = generate_html_report(final_report_data)
#
#         # Define Subject
#         success_rate = calculate_percentage(current_run_data["passed"], current_run_data["total"])
#         subject = f'Automation Report: {final_report_data["project_name"]} - {final_report_data["environment"]} - {success_rate}% Success'
#
#         # Send Email
#         # NOTE: The send_email function is commented out. Uncomment to send.
#         send_email(html_report, subject)
#
#         # Save HTML for inspection
#         with open(f"report_output_{environment}.html", "w") as f:
#             f.write(html_report)
#
#         print(f"[Pytest Report Generator] HTML report saved to report_output_{environment}.html.")
#         print(f"[Pytest Report Generator] Email generation complete. Uncomment 'send_email' in conftest.py to send.")
#
#     except Exception as e:
#         print(f"[Pytest Report Generator] Error during email generation for {environment}: {e}")
#
#
# @pytest.hookimpl(hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     """
#     Hook to capture test results (passed, failed, skipped).
#     """
#     outcome = yield
#     report = outcome.get_result()
#
#     # Only count in the tag loop below to avoid duplicate counting
#
#     # Determine the package name (e.g., 'resumeBuilder' or 'aiVoiceInterview')
#     # item.fspath is the path to the test file. We extract the directory name under 'tests/'
#     try:
#         # Get the path relative to the rootdir
#         # item.fspath is the path to the test file. We want the directory name under 'tests/'
#         # item.session.fspath.dirname is the root directory where pytest is run
#
#         # Get the full path of the test file
#         test_file_path = str(item.fspath)
#
#         # Find the index of the 'testcases' directory
#         if "testcases" + os.sep in test_file_path:
#             tests_dir_index = test_file_path.find("testcases" + os.sep)
#             # Extract the path after 'testcases/'
#             path_after_tests = test_file_path[tests_dir_index + len("testcases" + os.sep):]
#             # The package name is the first directory in this path
#             package_name = path_after_tests.split(os.sep)[0]
#         else:
#             package_name = "Other"
#     except Exception:
#         package_name = "Other"
#
#     # Get test tags (markers)
#     tags = [mark.name for mark in item.iter_markers()]
#     if not tags:
#         tags = ["untagged"]  # Default tag for tests without markers
#
#     # Initialize package and tag summary if it doesn't exist
#     if package_name not in item.session.results["package_tag_summary"]:
#         item.session.results["package_tag_summary"][package_name] = {}
#
#     package_tag_summary = item.session.results["package_tag_summary"][package_name]
#
#     for tag in tags:
#         if tag not in package_tag_summary:
#             package_tag_summary[tag] = {
#                 "passed": 0,
#                 "failed": 0,
#                 "skipped": 0,
#                 "total": 0
#             }
#
#         tag_summary = package_tag_summary[tag]
#
#         # Only count once per test, not per tag
#         if tag == tags[0]:  # Count only for the first tag to avoid duplicates
#             if report.when == "call":
#                 item.session.results["total"] += 1
#                 if report.passed:
#                     item.session.results["passed"] += 1
#                 elif report.failed:
#                     item.session.results["failed"] += 1
#                 elif report.skipped:
#                     item.session.results["skipped"] += 1
#             elif report.when == "setup" and report.skipped:
#                 item.session.results["total"] += 1
#                 item.session.results["skipped"] += 1
#
#         # Count for each tag
#         if report.when == "call":
#             tag_summary["total"] += 1
#             if report.passed:
#                 tag_summary["passed"] += 1
#             elif report.failed:
#                 tag_summary["failed"] += 1
#             elif report.skipped:
#                 tag_summary["skipped"] += 1
#         elif report.when == "setup" and report.skipped:
#             tag_summary["total"] += 1
#             tag_summary["skipped"] += 1
#
#
#


"""
Modern pytest conftest.py
- New JSON structure: env → trend_data[] with daily snapshots
- Enhanced header with project/env/time/duration/status
- Progress bar visualization
- Auto-purges >7 days per environment
- Mails beautiful HTML report
"""
from __future__ import annotations
import json, os, smtplib, ssl, time, datetime as dt
from pathlib import Path
from email.message import EmailMessage
from typing import Dict, Any

import pytest
from _pytest.config import Config
from _pytest.reports import TestReport

# ------------------------------------------------------------------
# CONFIG – change only here
# ------------------------------------------------------------------
PROJECT_NAME = "Project Phoenix"  # Your project name
ENVIRONMENTS = {"dev", "staging", "prod"}
DEFAULT_ENV = "dev"
METRICS_FILE = Path(__file__).with_name("test_metrics.json")
REPORT_DIR = Path(__file__).with_name("html_reports")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_TO = ["qa@mycompany.com"]


# ------------------------------------------------------------------

class MetricsCollector:
    def __init__(self) -> None:
        self._data: Dict[str, Any] = self._load()
        self.start_ts = time.time()

    # ---------- persistence ----------
    def _load(self) -> Dict[str, Any]:
        if METRICS_FILE.exists():
            data = json.loads(METRICS_FILE.read_text())
        else:
            data = {
                "report_title": "Comprehensive Automation Test Report",
                "project_name": PROJECT_NAME,
                "environments": {}
            }

        # Ensure all environments exist
        for env in ENVIRONMENTS:
            data["environments"].setdefault(env, {"trend_data": []})

        return data

    def _save(self) -> None:
        METRICS_FILE.parent.mkdir(exist_ok=True)
        METRICS_FILE.write_text(json.dumps(self._data, indent=2))

    def _delete_old_data(self) -> None:
        """Keep only last 7 days per environment"""
        cutoff_date = dt.date.today() - dt.timedelta(days=7)
        for env_data in self._data["environments"].values():
            env_data["trend_data"] = [
                entry for entry in env_data["trend_data"]
                if dt.date.fromisoformat(entry["date"]) >= cutoff_date
            ]

    # ---------- public ---------------
    def add_result(self, env: str, pkg: str, outcome: str) -> None:
        # Map pytest outcome to JSON keys (full words)
        outcome_map = {"passed": "passed", "failed": "failed", "skipped": "skipped"}
        metric_key = outcome_map.get(outcome)
        if not metric_key:
            print(f"⚠️ Unknown outcome '{outcome}', skipping")
            return

        today = dt.date.today().isoformat()
        timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Get environment data
        env_data = self._data["environments"][env]
        trend_data = env_data["trend_data"]

        # Find or create today's entry
        today_entry = next((e for e in trend_data if e["date"] == today), None)

        if not today_entry:
            today_entry = {
                "date": today,
                "timestamp": timestamp,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "package_summary": {}
            }
            trend_data.append(today_entry)

        # Update totals
        today_entry["total"] += 1
        today_entry[metric_key] += 1
        today_entry["timestamp"] = timestamp  # Update to latest

        # Update package summary
        pkg_summary = today_entry["package_summary"].setdefault(pkg, {
            "passed": 0, "failed": 0, "skipped": 0, "total": 0
        })
        pkg_summary["total"] += 1
        pkg_summary[metric_key] += 1

        self._delete_old_data()
        self._save()

    def today_summary(self, env: str) -> Dict[str, Any]:
        """Return today's data in format expected by HTML generator"""
        today = dt.date.today().isoformat()
        env_data = self._data["environments"].get(env, {"trend_data": []})

        # Find today's entry
        today_entry = next((e for e in env_data["trend_data"] if e["date"] == today), None)

        if not today_entry:
            return {
                "totals": {"pass": 0, "fail": 0, "skip": 0, "total": 0},
                "packages": {}
            }

        # Convert to format expected by HTML (short keys for classes)
        packages = {}
        for pkg, data in today_entry["package_summary"].items():
            packages[pkg] = {
                "pass": data["passed"],
                "fail": data["failed"],
                "skip": data["skipped"]
            }

        return {
            "totals": {
                "pass": today_entry["passed"],
                "fail": today_entry["failed"],
                "skip": today_entry["skipped"],
                "total": today_entry["total"]
            },
            "packages": packages
        }

    def last7(self, env: str) -> Dict[str, Any]:
        """Return last 7 days data for trend chart"""
        env_data = self._data["environments"].get(env, {"trend_data": []})
        # Get last 7 entries sorted by date
        sorted_data = sorted(env_data["trend_data"], key=lambda x: x["date"])[-7:]

        days = []
        passed = []
        failed = []
        skipped = []

        for entry in sorted_data:
            days.append(entry["date"])
            passed.append(entry["passed"])
            failed.append(entry["failed"])
            skipped.append(entry["skipped"])

        return {"days": days, "series": {"pass": passed, "fail": failed, "skip": skipped}}

    def get_project_info(self) -> Dict[str, str]:
        """Return project metadata"""
        return {
            "title": self._data.get("report_title", "Comprehensive Automation Test Report"),
            "name": self._data.get("project_name", PROJECT_NAME)
        }


# ------------------------------------------------------------------
# pytest hooks
# ------------------------------------------------------------------
_metrics = MetricsCollector()


def pytest_configure(config: Config):
    config._env = config.getoption("--env") or DEFAULT_ENV
    REPORT_DIR.mkdir(exist_ok=True)


def pytest_addoption(parser):
    parser.addoption("--env", choices=ENVIRONMENTS, default=DEFAULT_ENV)
    parser.addoption("--no-email", action="store_true")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep: TestReport = outcome.get_result()
    if rep.when != "call" and rep.outcome != "skipped":
        return
    pkg = rep.nodeid.split("/")[0] if "/" in rep.nodeid else "unknown"
    env = item.config._env
    _metrics.add_result(env, pkg, rep.outcome)


def pytest_sessionfinish(session, exitstatus):
    env = session.config._env
    summary = _metrics.today_summary(env)
    last7 = _metrics.last7(env)
    project_info = _metrics.get_project_info()

    html_path = REPORT_DIR / f"report-{env}-{dt.datetime.now():%Y%m%d-%H%M%S}.html"
    html = _build_html(summary, last7, env, time.time() - _metrics.start_ts, project_info)
    html_path.write_text(html, encoding="utf-8")
    print("\n📊 HTML report →", html_path)
    if not session.config.getoption("--no-email"):
        _send_email(html_path, env)


# ------------------------------------------------------------------
# HTML builder
# ------------------------------------------------------------------
def _build_html(summary: Dict[str, Any], last7: Dict[str, Any],
                env: str, duration: float, project_info: Dict[str, str]) -> str:
    totals = summary["totals"]
    pkgs = summary["packages"]

    total = totals["total"]
    pass_pct = (totals["pass"] / total * 100) if total else 0
    fail_pct = (totals["fail"] / total * 100) if total else 0
    skip_pct = (totals["skip"] / total * 100) if total else 0

    # Determine overall status
    if totals["fail"] == 0:
        status = "SUCCESS"
        status_color = "var(--success)"
    elif totals["fail"] <= 5:
        status = "WARNING"
        status_color = "var(--warning)"
    else:
        status = "FAILURE"
        status_color = "var(--danger)"

    # Build table rows
    rows = ""
    for pkg, cnt in sorted(pkgs.items()):
        p = cnt.get("pass", 0)
        f = cnt.get("fail", 0)
        s = cnt.get("skip", 0)
        pkg_total = p + f + s
        rate = (p / pkg_total * 100) if pkg_total else 0
        rows += f"""
        <tr>
          <td style="text-align:left">{pkg}</td>
          <td class="pass">{p}</td>
          <td class="fail">{f}</td>
          <td class="skip">{s}</td>
          <td><strong>{pkg_total}</strong></td>
          <td class="rate">{rate:.1f}%</td>
        </tr>"""

    execution_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Test Report – {env} – {dt.date.today()}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root{{
      --bg:#ffffff;--fg:#222;--card:#f5f5f5;--acc:#0d6efd;
      --success:#198754;--warning:#ffc107;--danger:#dc3545;
    }}
    @media(prefers-color-scheme:dark){{
      :root{{--bg:#121212;--fg:#eee;--card:#1e1e1e;--acc:#0ea5e9;
             --success:#22c55e;--warning:#f59e0b;--danger:#ef4444;}}
    }}
    body{{
      font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
      background:var(--bg);color:var(--fg);margin:0;padding:2rem;
    }}
    h1,h2{{margin-top:0}}
    .header{{
      background:var(--card);padding:2rem;border-radius:.75rem;margin-bottom:2rem;
      border-left:5px solid var(--acc);
    }}
    .project-title{{font-size:1.5rem;font-weight:600;margin-bottom:.5rem}}
    .meta{{display:flex;gap:2rem;flex-wrap:wrap;color:var(--fg);opacity:.8}}
    .status-badge{{
      display:inline-block;padding:.5rem 1rem;border-radius:.25rem;font-weight:600;
      margin-left:1rem;
    }}
    .card{{
      background:var(--card);padding:1.5rem;border-radius:.75rem;margin-bottom:1.5rem;
    }}
    .badge{{
      display:inline-block;padding:.25rem .5rem;border-radius:.25rem;font-size:.875rem;
    }}
    .pass{{background:#198754;color:#fff}}
    .fail{{background:#dc3545;color:#fff}}
    .skip{{background:#ffc107;color:#000}}
    table{{
      width:100%;border-collapse:collapse;font-size:.95rem;
    }}
    th,td{{
      padding:.5rem .75rem;text-align:center;
    }}
    th{{
      background:rgba(0,0,0,.1);position:sticky;top:0;
    }}
    tbody tr:nth-child(odd){{
      background:rgba(0,0,0,.05);
    }}
    .rate{{
      font-weight:600;
    }}
    canvas{{max-height:250px}}

    /* Progress bar */
    .progress-bar-container{{
      width:100%;height:30px;background:rgba(0,0,0,.1);border-radius:4px;
      overflow:hidden;margin:1rem 0;display:flex;
    }}
    .progress-bar-pass,.progress-bar-fail,.progress-bar-skip{{
      height:100%;display:flex;align-items:center;justify-content:center;
      color:#fff;font-weight:600;font-size:.85rem;transition:width .3s;
    }}
    .progress-bar-pass{{background:var(--success)}}
    .progress-bar-fail{{background:var(--danger)}}
    .progress-bar-skip{{background:var(--warning);color:#000}}
  </style>
</head>
<body>
  <!-- HEADER -->
  <div class="header">
    <div class="project-title">📊 {project_info["title"]}</div>
    <div class="meta">
      <div><strong>Project:</strong> {project_info["name"]}</div>
      <div><strong>Environment:</strong> <span style="color:var(--acc)">{env.upper()}</span></div>
      <div><strong>Executed:</strong> {execution_time}</div>
      <div><strong>Duration:</strong> {duration:.2f}s</div>
    </div>
    <div style="margin-top:1rem">
      <strong>Overall Status:</strong>
      <span class="status-badge" style="background:{status_color}">{status}</span>
    </div>
  </div>

  <!-- PROGRESS BAR SECTION -->
  <div class="card">
    <h2>Current Run Summary</h2>
    <div class="progress-bar-container">
      <div class="progress-bar-pass" style="width:{pass_pct:.2f}%;">
        {pass_pct:.1f}%
      </div>
      <div class="progress-bar-fail" style="width:{fail_pct:.2f}%;">
        {fail_pct:.1f}%
      </div>
      <div class="progress-bar-skip" style="width:{skip_pct:.2f}%;">
        {skip_pct:.1f}%
      </div>
    </div>
    <p style="text-align:center;font-size:.85rem;color:var(--fg);opacity:.8;margin:0">
      <span style="color:var(--success)">✔ Pass: {pass_pct:.1f}%</span> |
      <span style="color:var(--danger)">✖ Fail: {fail_pct:.1f}%</span> |
      <span style="color:var(--warning)">⏭ Skip: {skip_pct:.1f}%</span>
    </p>
  </div>

  <!-- CHARTS GRID -->
  <div class="grid" style="display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))">
    <!-- TODAY TOTALS + PIE -->
    <div class="card">
      <h2>📈 Today Details</h2>
      <p>
        <strong>Total Tests:</strong> {totals["total"]}<br>
        <span class="badge pass">Passed: {totals["pass"]}</span>
        <span class="badge fail">Failed: {totals["fail"]}</span>
        <span class="badge skip">Skipped: {totals["skip"]}</span>
      </p>
      <p><strong>Execution Time:</strong> {duration:.2f}s</p>
      <div style="height:200px"><canvas id="pieToday"></canvas></div>
    </div>

    <!-- 7-DAY TREND -->
    <div class="card">
      <h2>📅 Last 7 Days Trend</h2>
      <div style="height:200px"><canvas id="trendChart"></canvas></div>
    </div>
  </div>

  <!-- PACKAGE TABLE -->
  <div class="card">
    <h2>📦 Package-wise Breakdown</h2>
    <div style="overflow-x:auto;">
      <table>
        <thead>
          <tr>
            <th style="text-align:left">Package</th>
            <th class="pass">Pass</th>
            <th class="fail">Fail</th>
            <th class="skip">Skip</th>
            <th>Total</th>
            <th>Pass Rate</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>

  <script>
    // Pie – today
    new Chart(document.getElementById('pieToday'),{{
      type:'pie',
      data:{{
        labels:['Pass','Fail','Skip'],
        datasets:[{{
          data:[{totals["pass"]},{totals["fail"]},{totals["skip"]}],
          backgroundColor:['#198754','#dc3545','#ffc107']
        }}]
      }},
      options:{{plugins:{{legend:{{position:'bottom'}}}}}}
    }});

    // Trend line – 7 days
    new Chart(document.getElementById('trendChart'),{{
      type:'line',
      data:{{
        labels:{last7["days"]!r},
        datasets:[
          {{label:'Pass',data:{last7["series"]["pass"]!r},borderColor:'#198754',fill:false,tension:0.3}},
          {{label:'Fail',data:{last7["series"]["fail"]!r},borderColor:'#dc3545',fill:false,tension:0.3}},
          {{label:'Skip',data:{last7["series"]["skip"]!r},borderColor:'#ffc107',fill:false,tension:0.3}}
        ]
      }},
      options:{{plugins:{{legend:{{display:true}}}},scales:{{y:{{beginAtZero:true}}}}}}
    }});
  </script>
</body>
</html>"""


# ------------------------------------------------------------------
# Email helper
# ------------------------------------------------------------------
def _send_email(html_path: Path, env: str):
    if not (SMTP_USER and SMTP_PASSWORD):
        print("⚠️  SMTP credentials missing – skipping e-mail")
        return
    msg = EmailMessage()
    msg["Subject"] = f"{_metrics.get_project_info()['title']} – {env} – {dt.date.today()}"
    msg["From"] = SMTP_USER
    msg["To"] = MAIL_TO
    msg.add_alternative(html_path.read_text(), subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as smtp:
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)
    print("📧 Report mailed to", MAIL_TO)
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
Minimal pytest conftest.py
- Collects test metrics
- Delegates to report_generator and reporter modules
"""
import pytest

# import pytest
# import os
# from pathlib import Path
# import time
# import datetime as dt
# from typing import Dict, Any
# import json
#
# # Import local modules
# from report_generator import ReportGenerator
# from reporter import Reporter
#
# # ────────── CONFIGURATION ──────────
# ENVIRONMENTS = {"local", "staging", "prod"}
# DEFAULT_ENV = "staging"
# METRICS_FILE = Path(__file__).with_name("test_metrics.json")
# REPORT_DIR = Path(__file__).with_name("html_reports")
# PROJECT_NAME = "NLB API Testing"
#
# # Email config
# SMTP_SERVER = "smtp.gmail.com"
# SMTP_PORT = 465
# SMTP_USER = os.getenv("SMTP_USER", "")
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
# MAIL_TO = ["qa@example.com"]
#
# # Slack config
# SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")
# # ───────────────────────────────────
#
# class MetricsCollector:
#     def __init__(self):
#         self._data = self._load()
#         self.start_ts = time.time()
#
#     def _load(self) -> Dict[str, Any]:
#         if METRICS_FILE.exists():
#             return json.loads(METRICS_FILE.read_text())
#         return {
#             "report_title": "API/UI TESTING REPORT",
#             "project_name": PROJECT_NAME,
#             "environments": {}
#         }
#
#     def _save(self):
#         METRICS_FILE.parent.mkdir(exist_ok=True)
#         METRICS_FILE.write_text(json.dumps(self._data, indent=2))
#
#     def _purge_old(self):
#         """Keep only last 7 days per environment"""
#         cutoff = (dt.date.today() - dt.timedelta(days=7)).isoformat()
#         for env_data in self._data["environments"].values():
#             env_data["trend_data"] = [
#                 entry for entry in env_data["trend_data"]
#                 if entry["date"] >= cutoff
#             ]
#
#     def add_result(self, env: str, pkg: str, outcome: str):
#         outcome_map = {"passed": "passed", "failed": "failed", "skipped": "skipped"}
#         metric_key = outcome_map.get(outcome)
#         if not metric_key:
#             return
#
#         today = dt.date.today().isoformat()
#         timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#
#         # Initialize environment if needed
#         if env not in self._data["environments"]:
#             self._data["environments"][env] = {"trend_data": []}
#
#         env_data = self._data["environments"][env]
#         trend_data = env_data["trend_data"]
#
#         # Find today's entry
#         today_entry = next((e for e in trend_data if e["date"] == today), None)
#
#         if not today_entry:
#             today_entry = {
#                 "date": today,
#                 "timestamp": timestamp,
#                 "total": 0,
#                 "passed": 0,
#                 "failed": 0,
#                 "skipped": 0,
#                 "package_summary": {}
#             }
#             trend_data.append(today_entry)
#
#         # Update totals
#         today_entry["total"] += 1
#         today_entry[metric_key] += 1
#         today_entry["timestamp"] = timestamp
#
#         # Update package summary
#         pkg_summary = today_entry["package_summary"].setdefault(pkg, {
#             "passed": 0, "failed": 0, "skipped": 0, "total": 0
#         })
#         pkg_summary["total"] += 1
#         pkg_summary[metric_key] += 1
#
#         self._purge_old()
#         self._save()
#
#     def today_summary(self, env: str) -> Dict[str, Any]:
#         today = dt.date.today().isoformat()
#         env_data = self._data["environments"].get(env, {"trend_data": []})
#         today_entry = next((e for e in env_data["trend_data"] if e["date"] == today), None)
#
#         if not today_entry:
#             return {
#                 "totals": {"pass": 0, "fail": 0, "skip": 0, "total": 0},
#                 "packages": {}
#             }
#
#         packages = {}
#         for pkg, data in today_entry["package_summary"].items():
#             packages[pkg] = {
#                 "pass": data["passed"],
#                 "fail": data["failed"],
#                 "skip": data["skipped"]
#             }
#
#         return {
#             "totals": {
#                 "pass": today_entry["passed"],
#                 "fail": today_entry["failed"],
#                 "skip": today_entry["skipped"],
#                 "total": today_entry["total"]
#             },
#             "packages": packages
#         }
#
#     def last7(self, env: str) -> Dict[str, Any]:
#         env_data = self._data["environments"].get(env, {"trend_data": []})
#         sorted_data = sorted(env_data["trend_data"], key=lambda x: x["date"])[-7:]
#
#         days = []
#         passed = []
#         failed = []
#         skipped = []
#
#         for entry in sorted_data:
#             days.append(entry["date"])
#             passed.append(entry["passed"])
#             failed.append(entry["failed"])
#             skipped.append(entry["skipped"])
#
#         return {"days": days, "series": {"pass": passed, "fail": failed, "skip": skipped}}
#
#     def get_project_info(self) -> Dict[str, str]:
#         return {
#             "title": self._data.get("report_title", "API/UI TESTING REPORT"),
#             "name": self._data.get("project_name", PROJECT_NAME)
#         }
#
# _metrics = MetricsCollector()
#
# def pytest_configure(config):
#     config._env = config.getoption("--env") or DEFAULT_ENV
#     REPORT_DIR.mkdir(exist_ok=True)
#
# def pytest_addoption(parser):
#     parser.addoption("--env", choices=ENVIRONMENTS, default=DEFAULT_ENV)
#     parser.addoption("--no-email", action="store_true")
#     parser.addoption("--no-slack", action="store_true")
#
# @pytest.hookimpl(tryfirst=True, hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     outcome = yield
#     rep = outcome.get_result()
#
#     if rep.when != "call" and rep.outcome != "skipped":
#         return
#
#     from pathlib import Path
#     node_path = Path(rep.nodeid.split("::")[0])
#     parts = node_path.parts
#
#     if "testcases" in parts:
#         idx = parts.index("testcases")
#         pkg = parts[idx + 1] if len(parts) > idx + 1 else "testcases"
#     else:
#         pkg = parts[0] if parts else "unknown"
#
#     env = item.config._env
#     _metrics.add_result(env, pkg, rep.outcome)
#
#
# def pytest_sessionfinish(session, exitstatus):
#     env = session.config._env
#     summary = _metrics.today_summary(env)
#     last7 = _metrics.last7(env)
#     project_info = _metrics.get_project_info()
#     duration = time.time() - _metrics.start_ts
#
#     # Initialize generator and reporter
#     generator = ReportGenerator(PROJECT_NAME, project_info)
#     reporter = Reporter(smtp_server=SMTP_SERVER,smtp_port=SMTP_PORT,smtp_user=SMTP_USER,smtp_password=SMTP_PASSWORD,mail_to=MAIL_TO,slack_webhook=SLACK_WEBHOOK)
#
#     # Generate reports
#     html_content = generator.generate_html(summary, last7, env, duration)
#     text_content = generator.generate_text(summary, last7, env, duration)
#
#     # Save HTML
#     html_path = REPORT_DIR / f"report-{env}-{dt.datetime.now():%Y%m%d-%H%M%S}.html"
#     html_path.write_text(html_content, encoding="utf-8")
#     print(f"\n📊 HTML report → {html_path}")
#
#     # Print preview to console
#     # print("="*60)
#     # print(text_content)
#     # print("="*60)
#
#     # Send email
#     if not session.config.getoption("--no-email"):
#         try:
#             reporter.send_email(html_path, env, project_info["title"])
#             print("📧 Email sent successfully")
#         except Exception as e:
#             print(f"⚠️ Email failed: {e}")
#
#     # Send Slack
#     if not session.config.getoption("--no-slack") :
#         try:
#             reporter.send_slack(text_content, env)
#             print("💬 Slack message sent successfully")
#         except Exception as e:
#             print(f"⚠️ Slack failed: {e}")


import pytest
import json
import os
import datetime
from collections import defaultdict
from typing import Dict, Any, List

# Import report utilities
try:
    from report_utils import generate_html_report, send_email_report
except ImportError:
    def generate_html_report(*args, **kwargs):
        print("WARNING: report_utils.generate_html_report not found. Skipping HTML report generation.")


    def send_email_report(*args, **kwargs):
        print("WARNING: report_utils.send_email_report not found. Skipping email sending.")

# --- Configuration ---
REPORT_DIR = "test_reports"
HISTORY_FILE = os.path.join(REPORT_DIR, "test_history.json")
HTML_REPORT_FILE = os.path.join(REPORT_DIR, "latest_report.html")
HISTORY_DAYS = 7


# --- Helper Functions ---

def load_history() -> Dict[str, Any]:
    """Loads the test history from the JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return {
            "report_title": "Comprehensive Automation Test Report",
            "project_name": "Test Automation Project",
            "environments": {}
        }
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {
            "report_title": "Comprehensive Automation Test Report",
            "project_name": "Test Automation Project",
            "environments": {}
        }


def save_history(history: Dict[str, Any]):
    """Saves the test history to the JSON file, ensuring the directory exists."""
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)


def clean_old_history(history: Dict[str, Any]):
    """Removes test runs older than HISTORY_DAYS for each environment."""
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=HISTORY_DAYS)

    for env in history.get("environments", {}):
        trend_data = history["environments"][env].get("trend_data", [])
        new_trend_data = []

        for run in trend_data:
            try:
                timestamp_str = run.get('timestamp')
                if not timestamp_str:
                    continue

                run_date = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                if run_date >= cutoff_date:
                    new_trend_data.append(run)
            except ValueError:
                # Discard runs with invalid timestamps
                pass

        history["environments"][env]["trend_data"] = new_trend_data


def format_execution_time(delta: datetime.timedelta) -> str:
    """
    Converts a timedelta object to hh:mm:ss format.
    Example: 0:00:15.123456 -> "00:00:15"
    """
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def find_and_update_entry(history: Dict[str, Any], environment: str, current_date: str,
                          new_run_data: Dict[str, Any]) -> bool:
    """
    Checks if an entry exists for the same date and environment.
    If found, updates it and returns True.
    If not found, returns False (indicating a new entry should be added).
    """
    if environment not in history.get("environments", {}):
        return False

    trend_data = history["environments"][environment].get("trend_data", [])

    for i, run in enumerate(trend_data):
        if run.get("date") == current_date:
            # Found an entry for the same date and environment
            # Update it with new data
            history["environments"][environment]["trend_data"][i] = new_run_data
            return True

    return False


# --- Pytest Hooks ---

def pytest_addoption(parser):
    """Adds custom command-line options for environment and email."""
    parser.addoption(
        "--env", action="store", default="staging", help="Environment to run tests against (e.g., dev, staging, prod)"
    )
    parser.addoption(
        "--email-to", action="store", default="", help="Comma-separated list of email addresses to send the report to"
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtestloop(session):
    """Hook to capture the start time of the test session."""
    session.start_time = datetime.datetime.now()
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture the result of each test item."""
    outcome = yield
    report = outcome.get_result()

    # Initialize custom session attribute if it doesn't exist
    if not hasattr(item.session, 'test_results'):
        item.session.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "package_results": defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0})
        }

    # Only process the 'call' phase for pass/fail/skip
    if report.when == 'call':

        try:
            filepath = item.fspath  # full path to test file
            package_name = os.path.basename(os.path.dirname(str(filepath)))
        except (ValueError, IndexError):
            pass

        # Aggregate results
        item.session.test_results["total_tests"] += 1

        if report.passed:
            item.session.test_results["passed"] += 1
            item.session.test_results["package_results"][package_name]["passed"] += 1
        elif report.failed:
            item.session.test_results["failed"] += 1
            item.session.test_results["package_results"][package_name]["failed"] += 1
        elif report.skipped:
            item.session.test_results["skipped"] += 1
            item.session.test_results["package_results"][package_name]["skipped"] += 1


def pytest_sessionfinish(session):
    """Hook to process results after the entire test session finishes."""

    # 1. Calculate execution time
    end_time = datetime.datetime.now()
    start_time = getattr(session, 'start_time', end_time)
    execution_delta = end_time - start_time
    execution_time_formatted = format_execution_time(execution_delta)

    # Get results from the custom attribute
    results = getattr(session, 'test_results', {
        "total_tests": 0, "passed": 0, "failed": 0, "skipped": 0,
        "package_results": defaultdict(lambda: {"passed": 0, "failed": 0, "skipped": 0})
    })

    # Get environment
    environment = session.config.getoption("env")
    current_date = end_time.strftime("%Y-%m-%d")
    current_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")

    # 2. Build package_summary from package_results (simplified, no tag structure)
    package_summary = {}
    for package_name, pkg_results in results["package_results"].items():
        package_summary[package_name] = {
            "passed": pkg_results["passed"],
            "failed": pkg_results["failed"],
            "skipped": pkg_results["skipped"],
            "total": pkg_results["passed"] + pkg_results["failed"] + pkg_results["skipped"]
        }

    # 3. Create current run data in the new format
    current_run_data = {
        "date": current_date,
        "timestamp": current_timestamp,
        "execution_time": execution_time_formatted,
        "total": results["total_tests"],
        "passed": results["passed"],
        "failed": results["failed"],
        "skipped": results["skipped"],
        "package_summary": package_summary
    }

    # 4. Load history and update with new data
    history = load_history()

    # Ensure the environment exists in the history
    if environment not in history["environments"]:
        history["environments"][environment] = {
            "trend_data": []
        }

    # Check if entry exists for same date and environment
    # If yes, update it; if no, add new entry
    entry_updated = find_and_update_entry(history, environment, current_date, current_run_data)

    if not entry_updated:
        # Add as new entry only if it doesn't exist
        history["environments"][environment]["trend_data"].append(current_run_data)

    # 5. Clean old history (older than 7 days)
    clean_old_history(history)

    # 6. Save history
    save_history(history)

    # 7. Generate HTML Report
    generate_html_report(current_run_data, history, environment)

    # 8. Send Email
    recipients = session.config.getoption("email_to")
    if recipients:
        send_email_report(HTML_REPORT_FILE, recipients, current_run_data)
    else:
        print("Email not sent: No recipients specified. Use --email-to option.")
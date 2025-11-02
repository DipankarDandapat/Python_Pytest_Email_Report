import pytest
import json
import os
from datetime import datetime, timedelta
from generate_report import load_report_data, generate_html_report, send_email, calculate_percentage

# --- Configuration ---
REPORT_FILE = "report_data.json"
DAYS_TO_KEEP = 7
REPORT_TITLE = "Comprehensive Automation Test Report"
PROJECT_NAME = "Project Phoenix"
DEFAULT_ENVIRONMENT = "staging"  # Default environment if not specified


# --- Utility Functions ---

def load_report_data():
    """Loads existing report data from the JSON file."""
    if not os.path.exists(REPORT_FILE):
        return {
            "report_title": REPORT_TITLE,
            "project_name": PROJECT_NAME,
            "environments": {
                "dev": {"trend_data": []},
                "staging": {"trend_data": []},
                "prod": {"trend_data": []}
            }
        }
    try:
        with open(REPORT_FILE, 'r') as f:
            data = json.load(f)
            # Ensure the environment keys exist in the loaded data
            if "environments" not in data:
                data["environments"] = {
                    "dev": {"trend_data": []},
                    "staging": {"trend_data": []},
                    "prod": {"trend_data": []}
                }
            for env in ["dev", "staging", "prod"]:
                if env not in data["environments"]:
                    data["environments"][env] = {"trend_data": []}
            return data
    except (json.JSONDecodeError, FileNotFoundError):
        print(
            f"Warning: Could not load or decode existing report data from {REPORT_FILE}. Starting with fresh data structure.")
        return load_report_data()  # Return the default structure


def save_report_data(data):
    """Saves the updated report data to the JSON file."""
    with open(REPORT_FILE, 'w') as f:
        json.dump(data, f, indent=4)


def prune_old_data(trend_data):
    """Removes trend data older than DAYS_TO_KEEP."""
    cutoff_date = (datetime.now() - timedelta(days=DAYS_TO_KEEP)).date()

    # Filter out records older than the cutoff date
    new_trend_data = [
        record for record in trend_data
        if datetime.strptime(record["date"], "%Y-%m-%d").date() >= cutoff_date
    ]
    return new_trend_data


def update_trend_data(trend_data, new_data):
    """
    Updates the trend data:
    1. Removes any existing entry for the current day.
    2. Appends the new data.
    """
    current_date_str = new_data["date"]

    # Remove existing entry for today
    trend_data = [
        record for record in trend_data
        if record["date"] != current_date_str
    ]

    # Append the new data
    trend_data.append(new_data)

    return trend_data


# --- Pytest Hooks ---

def pytest_addoption(parser):
    """Adds command line option to specify the environment."""
    parser.addoption(
        "--env",
        action="store",
        default=DEFAULT_ENVIRONMENT,
        choices=["dev", "staging", "prod"],
        help="Environment to run tests against: dev, staging, or prod"
    )


@pytest.fixture(scope="session")
def env(request):
    """Fixture to provide the environment to tests and hooks."""
    return request.config.getoption("--env")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtestloop(session):
    """
    Hook to initialize and finalize the reporting process.
    """
    # Get the environment from the fixture
    environment = session.config.getoption("--env")

    # Initialize session data storage
    session.results = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0,
        "package_tag_summary": {}  # New structure for package-wise and tag-wise counts
    }

    # Execute all tests
    yield

    # --- Finalization (After all tests are done) ---

    # 1. Load existing data
    report_data = load_report_data()

    # 2. Get the environment-specific trend data
    env_data = report_data["environments"].get(environment, {"trend_data": []})
    trend_data = env_data["trend_data"]

    # 3. Prepare new trend entry
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_date_str = datetime.now().strftime("%Y-%m-%d")

    new_trend_entry = {
        "date": current_date_str,
        "timestamp": current_time_str,
        "total": session.results["total"],
        "passed": session.results["passed"],
        "failed": session.results["failed"],
        "skipped": session.results["skipped"],
        "package_tag_summary": session.results["package_tag_summary"]  # Include package and tag summary
    }

    # 4. Update and prune trend data
    trend_data = update_trend_data(trend_data, new_trend_entry)
    trend_data = prune_old_data(trend_data)

    # 5. Update the main report structure with the new trend data
    report_data["environments"][environment]["trend_data"] = trend_data

    # 6. Save the final data
    save_report_data(report_data)
    print(
        f"\n[Pytest Report Generator] Successfully updated report data for environment '{environment}' in {REPORT_FILE}")

    # 7. Generate and Send Email Report
    try:
        # Extract the current run data from the last entry in the trend data
        if not trend_data:
            print(
                f"[Pytest Report Generator] No test data found for environment '{environment}'. Skipping email generation.")
            return

        current_run_data = trend_data[-1]

        # Create a temporary structure for generate_report.py
        final_report_data = {
            "report_title": report_data["report_title"],
            "project_name": report_data["project_name"],
            "environment": environment.capitalize(),
            "current_run": current_run_data,
            "trend_data": trend_data
        }

        # Generate HTML
        html_report = generate_html_report(final_report_data)

        # Define Subject
        success_rate = calculate_percentage(current_run_data["passed"], current_run_data["total"])
        subject = f'Automation Report: {final_report_data["project_name"]} - {final_report_data["environment"]} - {success_rate}% Success'

        # Send Email
        # NOTE: The send_email function is commented out. Uncomment to send.
        send_email(html_report, subject)

        # Save HTML for inspection
        with open(f"report_output_{environment}.html", "w") as f:
            f.write(html_report)

        print(f"[Pytest Report Generator] HTML report saved to report_output_{environment}.html.")
        print(f"[Pytest Report Generator] Email generation complete. Uncomment 'send_email' in conftest.py to send.")

    except Exception as e:
        print(f"[Pytest Report Generator] Error during email generation for {environment}: {e}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test results (passed, failed, skipped).
    """
    outcome = yield
    report = outcome.get_result()

    # Only count in the tag loop below to avoid duplicate counting

    # Determine the package name (e.g., 'resumeBuilder' or 'aiVoiceInterview')
    # item.fspath is the path to the test file. We extract the directory name under 'tests/'
    try:
        # Get the path relative to the rootdir
        # item.fspath is the path to the test file. We want the directory name under 'tests/'
        # item.session.fspath.dirname is the root directory where pytest is run

        # Get the full path of the test file
        test_file_path = str(item.fspath)

        # Find the index of the 'testcases' directory
        if "testcases" + os.sep in test_file_path:
            tests_dir_index = test_file_path.find("testcases" + os.sep)
            # Extract the path after 'testcases/'
            path_after_tests = test_file_path[tests_dir_index + len("testcases" + os.sep):]
            # The package name is the first directory in this path
            package_name = path_after_tests.split(os.sep)[0]
        else:
            package_name = "Other"
    except Exception:
        package_name = "Other"

    # Get test tags (markers)
    tags = [mark.name for mark in item.iter_markers()]
    if not tags:
        tags = ["untagged"]  # Default tag for tests without markers

    # Initialize package and tag summary if it doesn't exist
    if package_name not in item.session.results["package_tag_summary"]:
        item.session.results["package_tag_summary"][package_name] = {}

    package_tag_summary = item.session.results["package_tag_summary"][package_name]

    for tag in tags:
        if tag not in package_tag_summary:
            package_tag_summary[tag] = {
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "total": 0
            }

        tag_summary = package_tag_summary[tag]

        # Only count once per test, not per tag
        if tag == tags[0]:  # Count only for the first tag to avoid duplicates
            if report.when == "call":
                item.session.results["total"] += 1
                if report.passed:
                    item.session.results["passed"] += 1
                elif report.failed:
                    item.session.results["failed"] += 1
                elif report.skipped:
                    item.session.results["skipped"] += 1
            elif report.when == "setup" and report.skipped:
                item.session.results["total"] += 1
                item.session.results["skipped"] += 1

        # Count for each tag
        if report.when == "call":
            tag_summary["total"] += 1
            if report.passed:
                tag_summary["passed"] += 1
            elif report.failed:
                tag_summary["failed"] += 1
            elif report.skipped:
                tag_summary["skipped"] += 1
        elif report.when == "setup" and report.skipped:
            tag_summary["total"] += 1
            tag_summary["skipped"] += 1




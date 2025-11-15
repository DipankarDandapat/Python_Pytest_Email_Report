import json
import os
import datetime
from typing import Dict, Any, List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
from collections import defaultdict

# --- Configuration (Should be consistent with conftest.py) ---
REPORT_DIR = "test_reports"
HTML_REPORT_FILE = os.path.join(REPORT_DIR, "latest_report.html")


# --- Status Indicator Logic ---

def get_overall_status(pass_percentage: float) -> tuple:
    """
    Determines the overall status based on pass percentage.
    Returns: (status_label, status_color, status_icon)
    - Pass: > 90%
    - Warning: 70% - 90%
    - Failure: < 70%
    """
    if pass_percentage > 90:
        return ("PASS", "#28a745", "✓")
    elif pass_percentage >= 70:
        return ("WARNING", "#ffc107", "⚠")
    else:
        return ("FAILURE", "#dc3545", "✗")


# --- HTML Report Generation ---

def get_history_summary_by_environment(history: Dict[str, Any], environment: str) -> List[Dict[str, Any]]:
    """
    Retrieves historical data for the specified environment, organized by date.
    Returns a list of trend data entries for the last 7 days.
    """
    if environment not in history.get("environments", {}):
        return []

    trend_data = history["environments"][environment].get("trend_data", [])

    # Sort by timestamp in descending order (most recent first)
    sorted_trend = sorted(trend_data, key=lambda x: x.get('timestamp', ''), reverse=True)

    return sorted_trend


def generate_html_report(current_run: Dict[str, Any], history: Dict[str, Any], environment: str):
    """Generates a mobile-friendly, responsive HTML report with status indicator and environment-specific historical data."""

    os.makedirs(REPORT_DIR, exist_ok=True)

    # Prepare data for the report
    current_env = environment.upper()
    current_timestamp = current_run.get("timestamp", "N/A")
    current_date = current_run.get("date", "N/A")
    execution_time = current_run.get("execution_time", "N/A")
    total_tests = current_run.get("total", 0)
    passed = current_run.get("passed", 0)
    failed = current_run.get("failed", 0)
    skipped = current_run.get("skipped", 0)

    # Calculate percentages
    pass_percent = (passed / total_tests * 100) if total_tests else 0
    fail_percent = (failed / total_tests * 100) if total_tests else 0
    skip_percent = (skipped / total_tests * 100) if total_tests else 0

    # Get overall status
    status_label, status_color, status_icon = get_overall_status(pass_percent)

    # --- Package-wise results table (responsive format) ---
    package_rows = ""
    package_summary = current_run.get("package_summary", {})

    for package_name, package_data in package_summary.items():
        pkg_passed = package_data.get("passed", 0)
        pkg_failed = package_data.get("failed", 0)
        pkg_skipped = package_data.get("skipped", 0)
        pkg_total = package_data.get("total", 0)
        pkg_pass_percent = (pkg_passed / pkg_total * 100) if pkg_total else 0

        package_rows += f"""
        <tr>
            <td data-label="Package"><strong>{package_name}</strong></td>
            <td data-label="Passed"><span class="badge badge-pass">{pkg_passed}</span></td>
            <td data-label="Failed"><span class="badge badge-fail">{pkg_failed}</span></td>
            <td data-label="Skipped"><span class="badge badge-skip">{pkg_skipped}</span></td>
            <td data-label="Total"><strong>{pkg_total}</strong></td>
            <td data-label="Pass Rate"><strong>{pkg_pass_percent:.1f}%</strong></td>
        </tr>
        """

    # --- Historical data table (Last 7 days, organized by date) ---
    history_summary = get_history_summary_by_environment(history, environment)
    history_rows = ""

    for run in history_summary:
        run_date = run.get("date", "N/A")
        run_timestamp = run.get("timestamp", "N/A")
        run_passed = run.get("passed", 0)
        run_failed = run.get("failed", 0)
        run_skipped = run.get("skipped", 0)
        run_total = run.get("total", 0)
        run_pass_percent = (run_passed / run_total * 100) if run_total else 0

        history_rows += f"""
        <tr>
            <td data-label="Date"><strong>{run_date}</strong><br><small>{run_timestamp}</small></td>
            <td data-label="Passed"><span class="badge badge-pass">{run_passed}</span></td>
            <td data-label="Failed"><span class="badge badge-fail">{run_failed}</span></td>
            <td data-label="Skipped"><span class="badge badge-skip">{run_skipped}</span></td>
            <td data-label="Total"><strong>{run_total}</strong></td>
            <td data-label="Pass Rate"><strong>{run_pass_percent:.1f}%</strong></td>
        </tr>
        """

    # --- HTML Template with Mobile-Friendly Design ---
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pytest Automation Report - {current_timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
            padding: 10px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        }}

        h1 {{
            color: #1a1a2e;
            text-align: center;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}

        h2 {{
            color: #1a1a2e;
            margin-top: 25px;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #00d9ff;
            padding-bottom: 10px;
        }}

        /* Overall Status Section */
        .status-container {{
            background: linear-gradient(135deg, {status_color}20 0%, {status_color}10 100%);
            border-left: 5px solid {status_color};
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }}

        .status-badge {{
            display: inline-block;
            background-color: {status_color};
            color: white;
            padding: 12px 24px;
            border-radius: 50px;
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .status-icon {{
            font-size: 2em;
            margin-right: 10px;
        }}

        /* Metadata Section */
        .metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}

        .metadata-item {{
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border-top: 3px solid #00d9ff;
        }}

        .metadata-item strong {{
            display: block;
            font-size: 1.1em;
            color: #1a1a2e;
            word-break: break-word;
        }}

        .metadata-item span {{
            font-size: 0.85em;
            color: #666;
        }}

        /* Summary Cards */
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}

        .card {{
            background: linear-gradient(135deg, #f0f4f8 0%, #ffffff 100%);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}

        .card h3 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .card p {{
            font-size: 2em;
            font-weight: bold;
            margin: 5px 0;
        }}

        .card small {{
            display: block;
            font-size: 0.85em;
            color: #999;
        }}

        .card-total p {{ color: #343a40; }}
        .card-pass p {{ color: #28a745; }}
        .card-fail p {{ color: #dc3545; }}
        .card-skip p {{ color: #ffc107; }}

        /* Progress Bar */
        .progress-bar-container {{
            background-color: #e9ecef;
            border-radius: 5px;
            margin-bottom: 25px;
            overflow: hidden;
            height: 30px;
            display: flex;
        }}

        .progress-bar {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
            transition: width 0.5s;
        }}

        .progress-pass {{ background-color: #28a745; }}
        .progress-fail {{ background-color: #dc3545; }}
        .progress-skip {{ background-color: #ffc107; }}

        /* Responsive Tables */
        .table-wrapper {{
            overflow-x: auto;
            margin-bottom: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: #ffffff;
        }}

        th {{
            background-color: #1a1a2e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95em;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
            font-size: 0.95em;
        }}

        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}

        tr:hover {{
            background-color: #f0f0f0;
        }}

        /* Badge Styling */
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
            color: white;
        }}

        .badge-pass {{ background-color: #28a745; }}
        .badge-fail {{ background-color: #dc3545; }}
        .badge-skip {{ background-color: #ffc107; color: #333; }}

        /* Mobile Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}

            h1 {{
                font-size: 1.4em;
            }}

            h2 {{
                font-size: 1.1em;
            }}

            .metadata {{
                grid-template-columns: 1fr;
            }}

            .summary-cards {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .card {{
                padding: 12px;
            }}

            .card h3 {{
                font-size: 0.8em;
            }}

            .card p {{
                font-size: 1.5em;
            }}

            /* Responsive Table */
            table {{
                font-size: 0.85em;
            }}

            th {{
                padding: 10px;
                font-size: 0.8em;
            }}

            td {{
                padding: 8px;
            }}

            .badge {{
                padding: 3px 8px;
                font-size: 0.8em;
            }}
        }}

        @media (max-width: 480px) {{
            .container {{
                padding: 10px;
            }}

            h1 {{
                font-size: 1.2em;
            }}

            h2 {{
                font-size: 1em;
            }}

            .summary-cards {{
                grid-template-columns: 1fr;
            }}

            .card p {{
                font-size: 1.3em;
            }}

            .metadata-item strong {{
                font-size: 0.95em;
            }}

            .metadata-item span {{
                font-size: 0.75em;
            }}

            /* Horizontal scrolling for tables on small screens */
            .table-wrapper {{
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }}

            table {{
                font-size: 0.8em;
                min-width: 500px;
            }}

            th, td {{
                padding: 6px;
            }}

            .badge {{
                padding: 2px 6px;
                font-size: 0.7em;
            }}
        }}

        /* Footer */
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            color: #999;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Automation Test Report</h1>

        <!-- Overall Status Section -->
        <div class="status-container">
            <div class="status-badge">
                <span class="status-icon">{status_icon}</span>
                {status_label} - {pass_percent:.1f}% Pass Rate
            </div>
            <p style="color: #666; margin-top: 10px;">Overall test execution status for current run</p>
        </div>

        <!-- Metadata Section -->
        <div class="metadata">
            <div class="metadata-item">
                <strong>{current_env}</strong>
                <span>Environment</span>
            </div>
            <div class="metadata-item">
                <strong style="word-break: break-word;">{current_date}</strong>
                <span>Execution Date</span>
            </div>
            <div class="metadata-item">
                <strong style="word-break: break-word;">{execution_time}</strong>
                <span>Total Execution Time</span>
            </div>
        </div>

        <h2>Current Run Summary</h2>
        <div class="summary-cards">
            <div class="card card-total">
                <h3>Total Tests</h3>
                <p>{total_tests}</p>
            </div>
            <div class="card card-pass">
                <h3>Passed</h3>
                <p>{passed}</p>
                <small>{pass_percent:.1f}%</small>
            </div>
            <div class="card card-fail">
                <h3>Failed</h3>
                <p>{failed}</p>
                <small>{fail_percent:.1f}%</small>
            </div>
            <div class="card card-skip">
                <h3>Skipped</h3>
                <p>{skipped}</p>
                <small>{skip_percent:.1f}%</small>
            </div>
        </div>

        <div class="progress-bar-container">
            <div class="progress-bar progress-pass" style="width: {pass_percent:.1f}%;">{passed if passed > 0 else ''}</div>
            <div class="progress-bar progress-fail" style="width: {fail_percent:.1f}%;">{failed if failed > 0 else ''}</div>
            <div class="progress-bar progress-skip" style="width: {skip_percent:.1f}%;">{skipped if skipped > 0 else ''}</div>
        </div>

        <h2>Package-wise Results</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Package</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Skipped</th>
                        <th>Total</th>
                        <th>Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {package_rows if package_rows else '<tr><td colspan="6" style="text-align: center; color: #999;">No test packages found</td></tr>'}
                </tbody>
            </table>
        </div>

        <h2>Historical Trend (Last 7 Days) - {current_env}</h2>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Skipped</th>
                        <th>Total</th>
                        <th>Pass Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {history_rows if history_rows else '<tr><td colspan="6" style="text-align: center; color: #999;">No historical data available</td></tr>'}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Report generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>This is an automated test report. For more details, please contact your QA team.</p>
        </div>
    </div>
</body>
</html>
    """

    with open(HTML_REPORT_FILE, 'w') as f:
        f.write(html_content)

    print(f"✓ HTML report generated: {HTML_REPORT_FILE}")


# --- Email Functionality ---

def send_email_report(report_path: str, recipients: str, current_run: Dict[str, Any]):
    """Sends the HTML report as an attachment via email."""

    if not recipients:
        print("No email recipients specified. Skipping email.")
        return

    # --- IMPORTANT: Configure your SMTP settings here ---
    SMTP_SERVER = "smtp.example.com"
    SMTP_PORT = 587
    SMTP_USERNAME = "your_email@example.com"
    SMTP_PASSWORD = "your_email_password"
    SENDER_EMAIL = "your_email@example.com"

    if SMTP_SERVER == "smtp.example.com":
        print(
            "⚠ WARNING: SMTP configuration is using placeholder values. Please update report_utils.py with your actual SMTP details to enable email functionality.")
        return

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipients
        msg['Subject'] = f"🧪 Pytest Report - {current_run.get('date', 'N/A')} - {current_run.get('timestamp', 'N/A')}"

        # Create a text version for email clients that don't support HTML
        text_body = f"""
Pytest Automation Report
========================

Execution Date: {current_run.get('date', 'N/A')}
Execution Time: {current_run.get('timestamp', 'N/A')}

SUMMARY:
--------
Total Tests: {current_run.get('total', 0)}
Passed: {current_run.get('passed', 0)}
Failed: {current_run.get('failed', 0)}
Skipped: {current_run.get('skipped', 0)}

Pass Rate: {(current_run.get('passed', 0) / current_run.get('total', 1) * 100):.1f}%

Please see the attached HTML report for detailed information.
        """

        msg.attach(MIMEText(text_body, 'plain'))

        # Attach the HTML report file
        with open(report_path, "rb") as f:
            html_part = MIMEText(f.read(), 'html')
            msg.attach(html_part)

        # Connect to the SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipients.split(','), msg.as_string())

        print(f"✓ Successfully sent report to {recipients}")

    except Exception as e:
        print(f"✗ ERROR: Failed to send email report. Check SMTP configuration and credentials. Error: {e}")
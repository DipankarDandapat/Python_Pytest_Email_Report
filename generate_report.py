import json
from datetime import datetime, timedelta, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os

# --- Configuration ---
# Replace with your actual email credentials and recipient
SENDER_EMAIL = "d.dandapat96@gmail.com"
SENDER_PASSWORD = "XXXX XXXX XXXX XXXX"  # Use an App Password for security
RECEIVER_EMAIL = "d.dandapat96@gmail.com"


# --- JSON Data Loading Function ---
# NOTE: The load_report_data function is not used directly in the Pytest flow anymore,
# but is kept for compatibility with the original design. The Pytest hook handles loading.
# The structure of the data passed to generate_html_report is now a temporary, flattened structure.
def load_report_data(file_path="report_data.json"):
    """Loads report data from an external JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] JSON file not found at {file_path}. Please create it.")
        return None
    except json.JSONDecodeError:
        print(f"[ERROR] Could not decode JSON from {file_path}. Check file format.")
        return None


def calculate_percentage(part, total):
    """Calculates percentage and handles division by zero."""
    return round((part / total) * 100, 2) if total > 0 else 0.00


def generate_html_report(report_data):
    """Generates the full HTML content for the email report."""

    # The data passed to this function is a temporary, flattened structure
    current_run = report_data["current_run"]
    trend_data = report_data["trend_data"]
    total = current_run["total"]
    package_tag_summary = current_run.get("package_tag_summary",
                                          {})  # Get package and tag summary, default to empty dict

    # Calculate overall status and color
    success_rate = calculate_percentage(current_run["passed"], total)
    overall_status = "PASS" if success_rate >= 90 else ("WARNING" if success_rate >= 70 else "FAIL")
    status_color = "#4CAF50" if overall_status == "PASS" else ("#FFC107" if overall_status == "WARNING" else "#F44336")

    # --- HTML Styling ---
    # Define CSS for the report
    style = f"""
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            overflow: hidden;
        }}
        .header {{
            background-color: #3f51b5;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .section {{ padding: 20px; }}
        h2 {{
            color: #3f51b5;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 5px;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
            table-layout: auto;
            word-break: break-word;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            font-size: 14px;
        }}
        th {{
            background-color: #f2f2f2;
            color: #333;
            font-weight: 600;
        }}
        .summary-table td:nth-child(2) {{ font-weight: bold; }}

        /* Status Colors */
        .status-pass {{ background-color: #E8F5E9; color: #4CAF50; font-weight: bold; }}
        .status-fail {{ background-color: #FFEBEE; color: #F44336; font-weight: bold; }}
        .status-skip {{ background-color: #FFF3E0; color: #FF9800; font-weight: bold; }}
        .status-total {{ background-color: #E3F2FD; color: #2196F3; font-weight: bold; }}

        /* Overall Status Badge */
        .overall-status {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 5px;
            color: white;
            font-size: 18px;
            font-weight: bold;
            margin-top: 10px;
            background-color: {status_color};
        }}

        /* Progress Bar Styling */
        .progress-bar-container {{
            width: 100%;
            background-color: #e0e0e0;
            border-radius: 5px;
            margin: 10px 0;
            overflow: hidden;
        }}
        .progress-bar-pass {{ height: 20px; background-color: #4CAF50; float: left; }}
        .progress-bar-fail {{ height: 20px; background-color: #F44336; float: left; }}
        .progress-bar-skip {{ height: 20px; background-color: #FF9800; float: left; }}
        .progress-text {{
            line-height: 20px;
            color: white;
            text-align: center;
            font-size: 12px;
            font-weight: bold;
        }}

        /* Table Specific Styling */
        .trend-table th {{ background-color: #3f51b5; color: white; }}
        .trend-table tr:nth-child(even) {{ background-color: #f9f9f9; }}

        .package-table th {{ background-color: #607d8b; color: white; }}
        .package-table tr:nth-child(even) {{ background-color: #f5f5f5; }}

        /* Responsive Fix for Mobile Email Clients */
        @media only screen and (max-width: 600px) {{
            body, .container {{
                padding: 10px !important;
            }}
            table, th, td {{
                font-size: 12px !important;
                padding: 8px !important;
            }}
            h2 {{
                font-size: 16px !important;
            }}
            h3 {{
                font-size: 14px !important;
            }}
            .trend-table-wrapper,
            .package-table-wrapper {{
                overflow-x: auto !important;
                display: block !important;
                width: 100% !important;
            }}
            .overall-status {{
                font-size: 14px !important;
                padding: 8px 15px !important;
            }}
        }}
    </style>
    """

    # --- Current Run Summary Table ---
    summary_html = f"""
    <h2>Current Run Summary</h2>
    <div style="text-align: center;">
        <div class="overall-status">{overall_status} </div>

        <div class="progress-bar-container">
            <div class="progress-bar-pass" style="width: {calculate_percentage(current_run["passed"], total)}%;">
                <span class="progress-text"></span>
            </div>
            <div class="progress-bar-fail" style="width: {calculate_percentage(current_run["failed"], total)}%;">
                <span class="progress-text"></span>
            </div>
            <div class="progress-bar-skip" style="width: {calculate_percentage(current_run["skipped"], total)}%;">
                <span class="progress-text"></span>
            </div>
        </div>
        <p style="font-size: 12px; color: #777;">
            <span style="color: #4CAF50;">Passed: {calculate_percentage(current_run["passed"], total)}%</span> |
            <span style="color: #F44336;">Failed: {calculate_percentage(current_run["failed"], total)}%</span> |
            <span style="color: #FF9800;">Skipped: {calculate_percentage(current_run["skipped"], total)}%</span>
        </p>

    </div>
    <table class="summary-table">
        <tr><th>Metric</th><th>Value</th><th>Percentage</th></tr>
        <tr><td>Project</td><td>{report_data["project_name"]}</td><td></td></tr>
        <tr><td>Environment</td><td>{report_data["environment"]}</td><td></td></tr>
        <tr><td>Execution Time</td><td>{current_run["timestamp"]}</td><td></td></tr>
        <tr class="status-total"><td>Total Tests</td><td>{total}</td><td>100.00%</td></tr>
        <tr class="status-pass"><td>Passed</td><td>{current_run["passed"]}</td><td>{calculate_percentage(current_run["passed"], total)}%</td></tr>
        <tr class="status-fail"><td>Failed</td><td>{current_run["failed"]}</td><td>{calculate_percentage(current_run["failed"], total)}%</td></tr>
        <tr class="status-skip"><td>Skipped</td><td>{current_run["skipped"]}</td><td>{calculate_percentage(current_run["skipped"], total)}%</td></tr>
    </table>
    """

    # --- Package and Tag Summary Table ---
    package_html = ""
    for package, tag_data in package_tag_summary.items():
        rows = ""
        for tag, counts in tag_data.items():
            tag_total = counts["total"]
            rows += f"""
            <tr>
                <td>{tag.capitalize()}</td>
                <td style="color: #4CAF50; font-weight: bold;">{counts["passed"]} ({calculate_percentage(counts["passed"], tag_total)}%)</td>
                <td style="color: #F44336; font-weight: bold;">{counts["failed"]} ({calculate_percentage(counts["failed"], tag_total)}%)</td>
                <td style="color: #FF9800; font-weight: bold;">{counts["skipped"]} ({calculate_percentage(counts["skipped"], tag_total)}%)</td>
                <td>{tag_total}</td>
            </tr>
            """
        package_html += f"""
        <h3 style="color: #3f51b5; margin-top: 20px; border-bottom: 1px dashed #e0e0e0; padding-bottom: 5px;">
            Package: {package}
        </h3>
        <div class="package-table-wrapper">
            <table class="package-table">
                <tr>
                    <th>Tag</th>
                    <th>Passed (Rate)</th>
                    <th>Failed (Rate)</th>
                    <th>Skipped (Rate)</th>
                    <th>Total</th>
                </tr>
                {rows}
            </table>
        </div>
        """

    summary_html += f"""
    <h2>Detailed Breakdown by Package and Tag</h2>
    {package_html}
    """

    # --- 7-Day Trend Analysis Table ---
    trend_rows = ""
    for day in trend_data:
        day_total = day["total"]
        trend_rows += f"""
        <tr>
            <td>{day["date"]}</td>
            <td style="color: #4CAF50; font-weight: bold;">{day["passed"]} ({calculate_percentage(day["passed"], day_total)}%)</td>
            <td style="color: #F44336; font-weight: bold;">{day["failed"]} ({calculate_percentage(day["failed"], day_total)}%)</td>
            <td style="color: #FF9800; font-weight: bold;">{day["skipped"]} ({calculate_percentage(day["skipped"], day_total)}%)</td>
            <td>{day_total}</td>
        </tr>
        """

    trend_html = f"""
    <h2>Last 7 Days Trend Analysis</h2>
    <div class="trend-table-wrapper">
        <table class="trend-table">
            <tr>
                <th>Date</th>
                <th>Passed (Rate)</th>
                <th>Failed (Rate)</th>
                <th>Skipped (Rate)</th>
                <th>Total</th>
            </tr>
            {trend_rows}
        </table>
    </div>
    """

    # --- Combine all HTML parts ---
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{report_data["report_title"]}</title>
        {style}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{report_data["report_title"]}</h1>
                <p>Project: {report_data["project_name"]} | Environment: {report_data["environment"]}</p>
            </div>
            <div class="section">
                {summary_html}
            </div>
            <div class="section">
                {trend_html}
            </div>

            <div class="section">
                <h2>Quick Links</h2>
                <p>
                    <a href="https://your-ci-server/job/{report_data["project_name"]}_{report_data["environment"]}/latest" style="color: #3f51b5; text-decoration: none; font-weight: bold;">View Full CI/CD Build Log</a> |
                    <a href="https://your-test-management-tool/dashboard" style="color: #3f51b5; text-decoration: none; font-weight: bold;">Test Management Dashboard</a> |
                    <a href="mailto:qa-team@example.com?subject=Question about {report_data["project_name"]} ({report_data["environment"]}) Report" style="color: #3f51b5; text-decoration: none; font-weight: bold;">Contact QA Team</a>
                </p>
            </div>

            <div class="section" style="text-align: center; font-size: 12px; color: #777; border-top: 1px solid #eee; padding-top: 10px;">
                &copy; {datetime.now().year} Automated Report Mailer
            </div>
        </div>
    </body>
    </html>
    """

    return html_content


def send_email(html_content, subject):
    """Sends the HTML email using Gmail's SMTP server."""

    # Create message container - the correct MIME type is 'multipart/alternative'.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    # Attach the HTML content
    part2 = MIMEText(html_content, 'html')
    msg.attach(part2)

    try:
        # Connect to Gmail's SMTP server
        # NOTE: You must use an App Password for your Gmail account, not your regular password.
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Send the email
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.close()

        print("\n[SUCCESS] Email report sent successfully!")
        print(f"Subject: {subject}")
        print(f"From: {SENDER_EMAIL} To: {RECEIVER_EMAIL}")

    except Exception as e:
        print(
            f"\n[ERROR] Failed to send email. Check your SENDER_EMAIL, SENDER_PASSWORD (must be App Password), and network settings.")
        print(f"Details: {e}")



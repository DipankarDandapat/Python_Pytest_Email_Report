"""
Report generator module
- Generates HTML and plaintext reports
"""
import datetime as dt
from typing import Dict, Any


class ReportGenerator:
    def __init__(self, project_name: str, project_info: Dict[str, Any]):
        self.project_name = project_name
        self.project_info = project_info

    def generate_html(self, summary: Dict[str, Any], last7: Dict[str, Any],
                      env: str, duration: float) -> str:
        """Generate modern HTML report with charts"""
        totals = summary["totals"]
        pkgs = summary["packages"]

        total = totals["total"]
        pass_pct = (totals["pass"] / total * 100) if total else 0
        fail_pct = (totals["fail"] / total * 100) if total else 0
        skip_pct = (totals["skip"] / total * 100) if total else 0

        # Determine status
        if totals["fail"] == 0:
            status = "SUCCESS"
            status_color = "var(--success)"
        elif totals["fail"] <= 5:
            status = "WARNING"
            status_color = "var(--warning)"
        else:
            status = "FAILURE"
            status_color = "var(--danger)"

        # Build package table rows
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
    <div class="project-title">📊 {self.project_info["title"]}</div>
    <div class="meta">
      <div><strong>Project:</strong> {self.project_info["name"]}</div>
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

    def generate_text(self, summary: Dict[str, Any], last7: Dict[str, Any],
                      env: str, duration: float) -> str:
        """Generate plaintext report for Slack/console"""
        totals = summary["totals"]
        packages = summary["packages"]

        lines = []
        lines.append("API/UI TESTING REPORT")
        lines.append("=" * 50)
        lines.append(f"Environment : {env}")
        lines.append(f"Date        : {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Duration    : {duration:.2f} seconds")
        lines.append("")
        lines.append(
            f"Totals      : Tests: {totals['total']} | Passed: {totals['pass']} | Failed: {totals['fail']} | Skipped: {totals['skip']}")
        lines.append("")
        lines.append("API TESTS SUMMARY")
        lines.append("-" * 30)

        for pkg_name, pkg_data in sorted(packages.items()):
            p = pkg_data.get("pass", 0)
            f = pkg_data.get("fail", 0)
            s = pkg_data.get("skip", 0)
            total = p + f + s
            lines.append(f"{pkg_name} > Total: {total} | Passed: {p} | Failed: {f} | Skipped: {s}")
            lines.append("")

        return "\n".join(lines)
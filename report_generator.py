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
        """Generate modern, mobile-first HTML report with WCAG-compliant colors"""
        totals = summary["totals"]
        pkgs = summary["packages"]

        total = totals["total"]
        pass_pct = (totals["pass"] / total * 100) if total else 0
        fail_pct = (totals["fail"] / total * 100) if total else 0
        skip_pct = (totals["skip"] / total * 100) if total else 0

        # Determine status with color-coded logic
        if totals["fail"] == 0:
            status = "✅ SUCCESS"
            status_color = "var(--success)"
        elif totals["fail"] <= 5:
            status = "⚠️ WARNING"
            status_color = "var(--warning)"
        else:
            status = "❌ FAILURE"
            status_color = "var(--danger)"

        # Build package table rows
        rows = ""
        for pkg, cnt in sorted(pkgs.items()):
            p = cnt.get("pass", 0)
            f = cnt.get("fail", 0)
            s = cnt.get("skip", 0)
            pkg_total = p + f + s
            rate = (p / pkg_total * 100) if pkg_total else 0
            # Add visual indicator for packages with failures
            row_class = "has-failures" if f > 0 else ""
            rows += f"""
            <tr class="{row_class}">
              <td style="text-align:left;font-weight:500">{pkg}</td>
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
  <meta name="theme-color" content="#0d6efd">
  <title>Test Report – {env} – {dt.date.today()}</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    /* ====== CSS Variables & Theming ====== */
    :root{{
      --bg:#ffffff;--fg:#222;--card:#f5f5f5;--acc:#0d6efd;
      --success:#198754;--warning:#ffc107;--danger:#dc3545;
      --shadow:0 4px 6px -1px rgba(0,0,0,0.1);
      --radius:10px;
      --transition:all 0.3s cubic-bezier(0.4,0,0.2,1);
    }}
    @media(prefers-color-scheme:dark){{
      :root{{--bg:#121212;--fg:#e2e8f0;--card:#1e1e1e;--acc:#0ea5e9;
             --success:#22c55e;--warning:#f59e0b;--danger:#ef4444;
             --shadow:0 4px 6px -1px rgba(0,0,0,0.3);}}
    }}

    /* ====== Reset & Base Styles ====== */
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
    html{{scroll-behavior:smooth}}
    body{{
      font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
      background:var(--bg);color:var(--fg);line-height:1.6;
      padding:1rem;min-height:100vh;
    }}
    @media(min-width:768px){{body{{padding:2rem}}}}

    /* ====== Typography ====== */
    h1{{font-size:clamp(1.5rem,4vw,2.5rem);margin-bottom:1rem;font-weight:700}}
    h2{{font-size:clamp(1.2rem,3vw,1.8rem);margin-bottom:1rem;font-weight:600}}

    /* ====== Header ====== */
    .header{{
      background:var(--card);padding:1.5rem;border-radius:var(--radius);
      margin-bottom:2rem;box-shadow:var(--shadow);border-left:5px solid var(--acc);
      transition:var(--transition);
    }}
    .header:hover{{transform:translateY(-2px);box-shadow:0 8px 15px -3px rgba(0,0,0,0.1)}}
    .project-title{{font-size:clamp(1.3rem,3vw,1.7rem);font-weight:700;margin-bottom:0.75rem}}
    .meta{{
      display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
      gap:0.75rem;font-size:0.9rem;color:var(--fg);opacity:0.85
    }}
    .meta strong{{opacity:1}}
    .status-badge{{
      display:inline-flex;align-items:center;gap:0.5rem;
      padding:0.5rem 1rem;border-radius:50px;font-weight:700;font-size:0.9rem;
      margin-left:0.5rem;box-shadow:var(--shadow);backdrop-filter:blur(10px);
    }}

    /* ====== Cards ====== */
    .card{{
      background:var(--card);padding:1.5rem;border-radius:var(--radius);
      margin-bottom:1.5rem;box-shadow:var(--shadow);transition:var(--transition);
    }}
    .card:hover{{transform:translateY(-3px);box-shadow:0 10px 20px -3px rgba(0,0,0,0.15)}}

    /* ====== Badges ====== */
    .badge{{
      display:inline-flex;align-items:center;gap:0.25rem;
      padding:0.4rem 0.75rem;border-radius:50px;font-size:0.8rem;font-weight:600;
      margin:0.25rem;box-shadow:var(--shadow);transition:var(--transition);
    }}
    .badge:hover{{transform:scale(1.05)}}
    .pass{{background:var(--success);color:#fff}}
    .fail{{background:var(--danger);color:#fff}}
    .skip{{background:var(--warning);color:#000}}

    /* ====== Progress Bar ====== */
    .progress-bar-container{{
      width:100%;height:40px;background:rgba(0,0,0,0.08);border-radius:var(--radius);
      overflow:hidden;margin:1.5rem 0;display:flex;box-shadow:inset 0 2px 4px rgba(0,0,0,0.1);
    }}
    .progress-bar-pass,.progress-bar-fail,.progress-bar-skip{{
      height:100%;display:flex;align-items:center;justify-content:center;
      color:#fff;font-weight:700;font-size:0.85rem;transition:width 0.5s ease;
      text-shadow:0 1px 2px rgba(0,0,0,0.3);
    }}
    .progress-bar-pass{{background:linear-gradient(90deg,var(--success),#22c55e)}}
    .progress-bar-fail{{background:linear-gradient(90deg,var(--danger),#ef4444)}}
    .progress-bar-skip{{background:linear-gradient(90deg,var(--warning),#f59e0b);color:#000}}

    /* ====== Table ====== */
    table{{
      width:100%;border-collapse:separate;border-spacing:0;
      font-size:0.9rem;border-radius:var(--radius);overflow:hidden;
      box-shadow:var(--shadow);
    }}
    th,td{{
      padding:0.75rem;text-align:center;transition:background 0.2s;
    }}
    th{{
      background:var(--acc);color:#fff;font-weight:700;position:sticky;top:0;
    }}
    tbody tr:hover{{background:rgba(0,0,0,0.05)}}
    tbody tr:nth-child(even){{background:rgba(0,0,0,0.02)}}
    tbody tr.has-failures{{border-left:4px solid var(--danger)}}

    /* ====== Charts ====== */
    canvas{{max-height:300px;border-radius:var(--radius)}}

    /* ====== Mobile Optimizations ====== */
    @media(max-width:768px){{
      body{{padding:0.5rem}}
      .header{{padding:1rem}}
      .card{{padding:1rem}}
      .meta{{grid-template-columns:1fr}}
      table{{font-size:0.8rem}}
      th,td{{padding:0.5rem 0.25rem}}
      .progress-bar-container{{height:35px}}
      .progress-bar-pass,.progress-bar-fail,.progress-bar-skip{{
        font-size:0.75rem;text-shadow:none;
      }}
    }}

    /* ====== Print Styles ====== */
    @media print{{
      body{{background:#fff;color:#000}}
      .card{{box-shadow:none;border:1px solid #ccc;page-break-inside:avoid}}
      .progress-bar-container{{background:#eee}}
    }}
  </style>
</head>
<body>
  <!-- HEADER -->
  <div class="header">
    <div class="project-title">📊 {self.project_info["title"]}</div>
    <div class="meta">
      <div><strong>Project:</strong> {self.project_info["name"]}</div>
      <div><strong>Environment:</strong> <span style="color:var(--acc);font-weight:700">{env.upper()}</span></div>
      <div><strong>Executed:</strong> {execution_time}</div>
      <div><strong>Duration:</strong> {duration:.2f}s</div>
    </div>
    <div style="margin-top:1rem">
      <strong>Overall Status:</strong>
      <span class="status-badge" style="background:{status_color};color:#fff">{status}</span>
    </div>
  </div>

  <!-- PROGRESS BAR SECTION -->
  <div class="card">
    <h2>📊 Current Run Summary</h2>
    <div class="progress-bar-container" aria-label="Test results progress bar">
      <div class="progress-bar-pass" style="width:{pass_pct:.2f}%;" title="Passed: {pass_pct:.1f}%">
        {pass_pct:.1f}%
      </div>
      <div class="progress-bar-fail" style="width:{fail_pct:.2f}%;" title="Failed: {fail_pct:.1f}%">
        {fail_pct:.1f}%
      </div>
      <div class="progress-bar-skip" style="width:{skip_pct:.2f}%;" title="Skipped: {skip_pct:.1f}%">
        {skip_pct:.1f}%
      </div>
    </div>
    <p style="text-align:center;font-size:.85rem;color:var(--fg);opacity:.8;margin:0.5rem 0 0">
      <span style="color:var(--success)">✔ Pass: {pass_pct:.1f}%</span> |
      <span style="color:var(--danger)">✖ Fail: {fail_pct:.1f}%</span> |
      <span style="color:var(--warning)">⏭ Skip: {skip_pct:.1f}%</span>
    </p>
  </div>

  <!-- CHARTS GRID -->
  <div class="grid" style="display:grid;gap:1.5rem;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))">
    <!-- TODAY TOTALS + PIE -->
    <div class="card">
      <h2>📈 Today Details</h2>
      <p style="font-size:0.95rem;margin-bottom:0.5rem">
        <strong>Total Tests:</strong> {totals["total"]}<br>
        <span class="badge pass">✔ Passed: {totals["pass"]}</span>
        <span class="badge fail">✖ Failed: {totals["fail"]}</span>
        <span class="badge skip">⏭ Skipped: {totals["skip"]}</span>
      </p>
      <p style="font-size:0.9rem;opacity:0.8"><strong>Execution Time:</strong> {duration:.2f}s</p>
      <div style="height:220px;margin-top:1rem"><canvas id="pieToday" role="img" aria-label="Today test results pie chart"></canvas></div>
    </div>

    <!-- 7-DAY TREND -->
    <div class="card">
      <h2>📅 Last 7 Days Trend</h2>
      <div style="height:220px"><canvas id="trendChart" role="img" aria-label="7-day test trend line chart"></canvas></div>
    </div>
  </div>

  <!-- PACKAGE TABLE -->
  <div class="card">
    <h2>📦 Package-wise Breakdown</h2>
    <div style="overflow-x:auto;border-radius:var(--radius);">
      <table role="table" aria-label="Package-wise test results">
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
    const pieCtx = document.getElementById('pieToday');
    new Chart(pieCtx,{{
      type:'pie',
      data:{{
        labels:['Pass','Fail','Skip'],
        datasets:[{{
          data:[{totals["pass"]},{totals["fail"]},{totals["skip"]}],
          backgroundColor:['#198754','#dc3545','#ffc107'],
          borderWidth:2,borderColor:'#fff'
        }}]
      }},
      options:{{
        responsive:true,maintainAspectRatio:false,
        plugins:{{legend:{{position:'bottom',labels:{{padding:15,font:{{size:12}}}}}}}},
        animation:{{animateRotate:true,animateScale:true}}
      }}
    }});

    // Trend line – 7 days
    const trendCtx = document.getElementById('trendChart');
    new Chart(trendCtx,{{
      type:'line',
      data:{{
        labels:{last7["days"]!r},
        datasets:[
          {{label:'Pass',data:{last7["series"]["pass"]!r},borderColor:'#198754',backgroundColor:'rgba(25,135,84,0.1)',borderWidth:3,fill:true,tension:0.4,pointRadius:5,pointHoverRadius:7}},
          {{label:'Fail',data:{last7["series"]["fail"]!r},borderColor:'#dc3545',backgroundColor:'rgba(220,53,69,0.1)',borderWidth:3,fill:true,tension:0.4,pointRadius:5,pointHoverRadius:7}},
          {{label:'Skip',data:{last7["series"]["skip"]!r},borderColor:'#ffc107',backgroundColor:'rgba(255,193,7,0.1)',borderWidth:3,fill:true,tension:0.4,pointRadius:5,pointHoverRadius:7}}
        ]
      }},
      options:{{
        responsive:true,maintainAspectRatio:false,
        plugins:{{legend:{{display:true,position:'top'}}}},
        scales:{{y:{{beginAtZero:true,grid:{{color:'rgba(0,0,0,0.1)'}}}},x:{{grid:{{display:false}}}}}},
        interaction:{{mode:'index',intersect:false}}
      }}
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
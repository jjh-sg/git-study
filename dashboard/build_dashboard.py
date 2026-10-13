"""버스 하차 더미 xlsx -> 단일 자체완결 HTML 대시보드(dashboard/index.html) 생성."""
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
XLSX = HERE.parent / "버스_노선_하차_더미데이터.xlsx"  # 저장소 루트
OUT = HERE / "index.html"
TYPES = ["일반", "청소년", "어린이", "경로", "기타"]
DAYS = ["월", "화", "수", "목", "금", "토", "일"]
CHART_JS = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"


def build_data(df: pd.DataFrame) -> dict:
    routes = []
    groups = [("전체", df)] + [(n, g) for n, g in df.groupby("노선명", sort=True)]
    for name, g in groups:
        hours = g.groupby("시간대")["하차합계"].sum().sort_index()
        stops = g.sort_values("정류소순번").groupby(["정류소순번", "정류소명"], sort=True)["하차합계"].sum()
        days = g.groupby("요일")["하차합계"].sum().reindex(DAYS, fill_value=0)
        routes.append({
            "name": name,
            "total": int(g["하차합계"].sum()),
            "hours": {"labels": list(hours.index), "values": [int(v) for v in hours.values]},
            "stops": {"labels": [k[1] for k in stops.index], "values": [int(v) for v in stops.values]},
            "types": [int(g[t].sum()) for t in TYPES],
            "days": [int(v) for v in days.values],
        })
    return {"types": TYPES, "days": DAYS, "routes": routes,
            "period": f"{df['일자'].min()} ~ {df['일자'].max()}"}


HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>노선별 하차 현황</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--text:#1d2330;--muted:#5d6678;--border:#dde1e8;--grid:#e6e9ef;--accent:#2563eb}
@media (prefers-color-scheme:dark){:root{--bg:#12151c;--card:#1b202b;--text:#e8ebf2;--muted:#9aa4b8;--border:#2d3445;--grid:#2a3141;--accent:#6ea0ff}}
*{box-sizing:border-box}
html,body{margin:0;overflow-x:hidden}
body{background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,"Malgun Gothic",sans-serif;line-height:1.4}
main{max-width:1200px;margin:0 auto;padding:16px}
header{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;margin-bottom:16px}
h1{font-size:1.3rem;margin:0}
.sub{color:var(--muted);font-size:.85rem}
select{font:inherit;padding:8px 12px;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text);max-width:100%}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:16px}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;min-width:0}
.kpi .l{color:var(--muted);font-size:.8rem}
.kpi .v{font-size:1.5rem;font-weight:700;margin-top:4px;overflow-wrap:anywhere}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.wide{grid-column:1/-1}
h2{font-size:.95rem;margin:0 0 8px}
.box{position:relative;height:280px}
@media (max-width:760px){.grid{grid-template-columns:minmax(0,1fr)}}
</style>
</head>
<body>
<main>
<header>
 <div><h1>노선별 하차 현황</h1><div class="sub" id="period"></div></div>
 <label>노선 <select id="route" aria-label="노선 선택"></select></label>
</header>
<section class="kpis">
 <div class="card kpi"><div class="l">총 하차</div><div class="v" id="k1"></div></div>
 <div class="card kpi"><div class="l">피크 시간대</div><div class="v" id="k2"></div></div>
 <div class="card kpi"><div class="l">최다 하차 정류소</div><div class="v" id="k3"></div></div>
</section>
<section class="grid">
 <div class="card wide"><h2>시간대별 하차 추이</h2><div class="box"><canvas id="c1"></canvas></div></div>
 <div class="card wide"><h2>정류소별 하차</h2><div class="box"><canvas id="c2"></canvas></div></div>
 <div class="card"><h2>승객유형 비율</h2><div class="box"><canvas id="c3"></canvas></div></div>
 <div class="card"><h2>요일별 합계</h2><div class="box"><canvas id="c4"></canvas></div></div>
</section>
</main>
<script src="__CHARTJS__"></script>
<script>
const DATA = __DATA__;
const PAL = ["#3b82f6","#f59e0b","#10b981","#ef4444","#8b5cf6"];
const fmt = n => n.toLocaleString("ko-KR");
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const sel = document.getElementById("route");
DATA.routes.forEach((r,i)=>{const o=document.createElement("option");o.value=i;o.textContent=r.name;sel.appendChild(o);});
document.getElementById("period").textContent = "기간 " + DATA.period;
let charts = [];
function argmax(a){return a.indexOf(Math.max.apply(null,a));}
function render(){
  charts.forEach(c=>c.destroy()); charts=[];
  const r = DATA.routes[+sel.value];
  document.getElementById("k1").textContent = fmt(r.total)+"명";
  document.getElementById("k2").textContent = r.hours.labels[argmax(r.hours.values)];
  const si = argmax(r.stops.values);
  document.getElementById("k3").textContent = r.stops.labels[si]+" ("+fmt(r.stops.values[si])+")";
  if(typeof Chart==="undefined"){return;}
  const text=css("--text"), muted=css("--muted"), grid=css("--grid"), card=css("--card"), accent=css("--accent");
  Chart.defaults.color = muted;
  Chart.defaults.borderColor = grid;
  const base = {responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:text}}}};
  const axes = {x:{ticks:{color:muted,maxRotation:60},grid:{color:grid}},y:{beginAtZero:true,ticks:{color:muted},grid:{color:grid}}};
  const mk=(id,cfg)=>charts.push(new Chart(document.getElementById(id),cfg));
  mk("c1",{type:"line",data:{labels:r.hours.labels.map(s=>s.slice(0,2)+"시"),datasets:[{label:"하차",data:r.hours.values,borderColor:accent,backgroundColor:accent+"33",fill:true,tension:.3,pointRadius:3}]},options:{...base,plugins:{legend:{display:false}},scales:axes}});
  mk("c2",{type:"bar",data:{labels:r.stops.labels,datasets:[{label:"하차",data:r.stops.values,backgroundColor:accent}]},options:{...base,plugins:{legend:{display:false}},scales:axes}});
  mk("c3",{type:"doughnut",data:{labels:DATA.types,datasets:[{data:r.types,backgroundColor:PAL,borderColor:card,borderWidth:2}]},options:{...base,plugins:{legend:{position:"bottom",labels:{color:text}}}}});
  mk("c4",{type:"bar",data:{labels:DATA.days,datasets:[{label:"하차",data:r.days,backgroundColor:accent}]},options:{...base,plugins:{legend:{display:false}},scales:axes}});
}
sel.addEventListener("change",render);
matchMedia("(prefers-color-scheme: dark)").addEventListener("change",render);
render();
</script>
</body>
</html>
"""


def main() -> None:
    df = pd.read_excel(XLSX, sheet_name="하차데이터", engine="openpyxl")
    data = json.dumps(build_data(df), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = HTML.replace("__CHARTJS__", CHART_JS).replace("__DATA__", data)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()

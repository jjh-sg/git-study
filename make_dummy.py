import random
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

random.seed(42)

# 노선(경로) 정의: 노선ID, 노선명, 유형, 정류소 이름 목록
STOPS = ["서울역", "시청앞", "광화문", "종로3가", "동대문", "청량리", "회기역", "이문동", "장위동", "월계역",
         "노원역", "상계동", "수락산역", "당고개", "강남역", "역삼역", "선릉역", "삼성역", "잠실역", "송파구청",
         "신촌", "이대입구", "마포구청", "공덕역", "여의도", "영등포", "신도림", "구로디지털단지", "가산디지털단지", "금천구청"]
ROUTES = [
    ("R100", "100번", "간선", 12), ("R143", "143번", "간선", 14), ("R271", "271번", "지선", 10),
    ("R340", "340번", "간선", 15), ("R472", "472번", "광역", 9), ("R501", "501번", "지선", 11),
    ("R7016", "7016번", "간선", 13), ("R9401", "9401번", "광역", 8),
]

stop_master = {n: f"S{1000 + i}" for i, n in enumerate(STOPS)}

route_rows, route_info = [], {}
for rid, rname, rtype, n in ROUTES:
    stops = random.sample(STOPS, n)
    route_info[rid] = (rname, stops)
    first, last = "05:00", "23:30" if rtype != "광역" else "22:00"
    interval = {"간선": 8, "지선": 12, "광역": 20}[rtype]
    for seq, s in enumerate(stops, 1):
        route_rows.append([rid, rname, rtype, seq, stop_master[s], s, stops[0], stops[-1],
                           round(seq * random.uniform(0.7, 1.2), 1), first, last, interval])

# 하차 데이터: 2026-09-01 ~ 2026-09-07, 시간대별
days = [date(2026, 9, 1) + timedelta(days=i) for i in range(7)]
peak = {7: 2.2, 8: 3.0, 9: 1.8, 12: 1.2, 13: 1.1, 17: 2.0, 18: 2.8, 19: 2.0}
alight_rows, n = [], 1
for d in days:
    weekend = d.weekday() >= 5
    for rid, (rname, stops) in route_info.items():
        for seq, s in enumerate(stops, 1):
            if seq == 1:
                continue  # 기점은 하차 없음
            for h in range(5, 24):
                base = random.randint(2, 12) * peak.get(h, 1.0) * (0.55 if weekend else 1.0)
                off = int(base * (0.6 + seq / len(stops)))
                board_cnt = int(off * random.uniform(0.8, 1.3))
                alight_rows.append([n, d.isoformat(), "토일"[d.weekday() - 5] if weekend else "월화수목금"[d.weekday()],
                                    f"{h:02d}:00~{h:02d}:59", rid, rname, seq, stop_master[s], s,
                                    off, random.choice(["일반", "청소년", "어린이", "경로", "환승"]) if False else None])
                n += 1

# 승객유형별로 분할 (하차 총합을 유형별 비율로 나눔)
final_rows, n = [], 1
for r in alight_rows:
    total = r[9]
    a = int(total * 0.65); y = int(total * 0.1); k = int(total * 0.03); e = int(total * 0.12)
    t = total - a - y - k - e
    final_rows.append(r[:9] + [a, y, k, e, t, total])

def sheet(wb, title, header, rows, widths):
    ws = wb.create_sheet(title)
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
        c.alignment = Alignment(horizontal="center")
    for r in rows:
        ws.append(r)
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

wb = Workbook(); wb.remove(wb.active)
sheet(wb, "노선데이터",
      ["노선ID", "노선명", "노선유형", "정류소순번", "정류소ID", "정류소명", "기점", "종점",
       "누적거리(km)", "첫차", "막차", "배차간격(분)"], route_rows,
      [10, 10, 10, 11, 11, 16, 14, 14, 13, 8, 8, 12])
sheet(wb, "하차데이터",
      ["번호", "일자", "요일", "시간대", "노선ID", "노선명", "정류소순번", "정류소ID", "정류소명",
       "일반", "청소년", "어린이", "경로", "기타", "하차합계"],
      [[i + 1] + r[1:] for i, r in enumerate(final_rows)],
      [8, 12, 6, 14, 10, 10, 11, 11, 16, 8, 8, 8, 8, 8, 10])

wb.save("버스_노선_하차_더미데이터.xlsx")
print(len(route_rows), len(final_rows))

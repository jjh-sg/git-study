"""버스 노선/시간대별 하차 더미 데이터 생성기 v2.

시트/컬럼 스키마(노선데이터, 하차데이터)는 v1과 동일하게 유지한다.
사용법: python make_dummy.py [--routes N] [--days N] [--start YYYY-MM-DD] [--seed N] [--out FILE]
"""
import argparse
import random
from datetime import date, timedelta

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

STOPS = ["서울역", "시청앞", "광화문", "종로3가", "동대문", "청량리", "회기역", "이문동", "장위동", "월계역",
         "노원역", "상계동", "수락산역", "당고개", "강남역", "역삼역", "선릉역", "삼성역", "잠실역", "송파구청",
         "신촌", "이대입구", "마포구청", "공덕역", "여의도", "영등포", "신도림", "구로디지털단지", "가산디지털단지", "금천구청"]
STOP_ID = {name: f"S{1000 + i}" for i, name in enumerate(STOPS)}  # 정류소ID는 전 노선 공통

# 환승 거점 정류소: 하차 가중치가 높다
HUBS = {"서울역", "종로3가", "강남역", "잠실역", "영등포", "신도림", "노원역", "공덕역"}

# 기본 노선 (노선ID, 노선명, 유형, 정류소 수)
BASE_ROUTES = [
    ("R100", "100번", "간선", 12), ("R143", "143번", "간선", 14), ("R271", "271번", "지선", 10),
    ("R340", "340번", "간선", 15), ("R472", "472번", "광역", 9), ("R501", "501번", "지선", 11),
    ("R7016", "7016번", "간선", 13), ("R9401", "9401번", "광역", 8),
]
TYPE_INFO = {  # 유형: (막차, 배차간격)
    "간선": ("23:30", 8), "지선": ("23:30", 12), "광역": ("22:00", 20),
}
FIRST_BUS = "05:00"

# 공휴일 (주말과 동일하게 수요 감소)
HOLIDAYS = {
    date(2026, 9, 24): "추석", date(2026, 9, 25): "추석", date(2026, 9, 26): "추석",
    date(2026, 10, 3): "개천절", date(2026, 10, 5): "대체공휴일", date(2026, 10, 9): "한글날",
}
HOUR_PEAK = {7: 2.2, 8: 3.0, 9: 1.8, 12: 1.2, 13: 1.1, 17: 2.0, 18: 2.8, 19: 2.0}
WEEKDAY_KO = "월화수목금토일"

ROUTE_HEADER = ["노선ID", "노선명", "노선유형", "정류소순번", "정류소ID", "정류소명", "기점", "종점",
                "누적거리(km)", "첫차", "막차", "배차간격(분)"]
ALIGHT_HEADER = ["번호", "일자", "요일", "시간대", "노선ID", "노선명", "정류소순번", "정류소ID", "정류소명",
                 "일반", "청소년", "어린이", "경로", "기타", "하차합계"]
ROUTE_WIDTHS = [10, 10, 10, 11, 11, 16, 14, 14, 13, 8, 8, 12]
ALIGHT_WIDTHS = [8, 12, 6, 14, 10, 10, 11, 11, 16, 8, 8, 8, 8, 8, 10]


def build_route_specs(count, rng):
    """노선 사양 목록. 기본 8개 이후는 중복 없는 ID로 자동 생성."""
    specs = BASE_ROUTES[:count]
    used = {s[0] for s in specs}
    types = list(TYPE_INFO)
    while len(specs) < count:
        num = rng.randint(100, 9999)
        rid = f"R{num}"
        if rid in used:
            continue
        used.add(rid)
        rtype = "광역" if num >= 9000 else rng.choice(types[:2])
        n_stops = rng.randint(8, 15) if rtype != "광역" else rng.randint(8, 10)
        specs.append((rid, f"{num}번", rtype, n_stops))
    return specs


def build_routes(specs, rng):
    """노선 정보와 노선데이터 행을 한 번에 만든다."""
    routes, rows = [], []
    for rid, rname, rtype, n in specs:
        stops = rng.sample(STOPS, n)
        last_bus, interval = TYPE_INFO[rtype]
        dist = 0.0
        for seq, stop in enumerate(stops, 1):
            if seq > 1:
                dist += rng.uniform(0.7, 1.2)
            rows.append([rid, rname, rtype, seq, STOP_ID[stop], stop, stops[0], stops[-1],
                         round(dist, 1), FIRST_BUS, last_bus, interval])
        routes.append({"id": rid, "name": rname, "stops": stops})
    return routes, rows


def stop_weight(stop, seq, n):
    """정류소 하차 가중치: 종점 최대, 환승거점 높음, 그 외 순번에 따라 완만히 증가."""
    w = 0.6 + seq / n
    if seq == n:
        w *= 2.2
    if stop in HUBS:
        w *= 1.8
    return w


def day_factor(d):
    if d in HOLIDAYS:
        return 0.4
    return 0.55 if d.weekday() >= 5 else 1.0


def split_passengers(total):
    adult, youth, child, senior = (int(total * r) for r in (0.65, 0.1, 0.03, 0.12))
    return [adult, youth, child, senior, total - adult - youth - child - senior, total]


def alight_rows(routes, days, rng):
    n = 0
    for d in days:
        factor = day_factor(d)
        dow = WEEKDAY_KO[d.weekday()]
        for r in routes:
            stops = r["stops"]
            for seq, stop in enumerate(stops, 1):
                if seq == 1:
                    continue  # 기점은 하차 없음
                w = stop_weight(stop, seq, len(stops))
                for h in range(5, 24):
                    base = rng.randint(2, 12) * HOUR_PEAK.get(h, 1.0) * factor
                    n += 1
                    yield [n, d.isoformat(), dow, f"{h:02d}:00~{h:02d}:59", r["id"], r["name"], seq,
                           STOP_ID[stop], stop, *split_passengers(int(base * w))]


def write_sheet(wb, title, header, rows, widths):
    ws = wb.create_sheet(title)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    cells = []
    for h in header:
        c = WriteOnlyCell(ws, value=h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
        c.alignment = Alignment(horizontal="center")
        cells.append(c)
    ws.append(cells)
    count = 0
    for r in rows:
        ws.append(r)
        count += 1
    ws.auto_filter.ref = f"A1:{get_column_letter(len(header))}{count + 1}"
    return count


def parse_args():
    p = argparse.ArgumentParser(description="버스 노선/하차 더미 데이터(xlsx) 생성기 v2")
    p.add_argument("--routes", type=int, default=8, help="노선 수 (기본 8)")
    p.add_argument("--days", type=int, default=7, help="기간(일) (기본 7)")
    p.add_argument("--start", type=date.fromisoformat, default=date(2026, 9, 1),
                   help="시작일 YYYY-MM-DD (기본 2026-09-01)")
    p.add_argument("--seed", type=int, default=42, help="난수 시드 (기본 42)")
    p.add_argument("--out", default="버스_노선_하차_더미데이터.xlsx", help="출력 파일명")
    args = p.parse_args()
    if args.routes < 1 or args.days < 1:
        p.error("--routes, --days는 1 이상이어야 합니다")
    return args


def main():
    args = parse_args()
    rng = random.Random(args.seed)
    routes, route_rows = build_routes(build_route_specs(args.routes, rng), rng)
    days = [args.start + timedelta(days=i) for i in range(args.days)]

    wb = Workbook(write_only=True)
    write_sheet(wb, "노선데이터", ROUTE_HEADER, route_rows, ROUTE_WIDTHS)
    n_alight = write_sheet(wb, "하차데이터", ALIGHT_HEADER, alight_rows(routes, days, rng), ALIGHT_WIDTHS)
    wb.save(args.out)
    print(f"{args.out}: 노선데이터 {len(route_rows)}행, 하차데이터 {n_alight}행")


if __name__ == "__main__":
    main()

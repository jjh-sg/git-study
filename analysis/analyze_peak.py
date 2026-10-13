"""시간대별·정류소별 하차 혼잡도 분석."""
import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "버스_노선_하차_더미데이터.xlsx")
OUT = os.path.join(BASE, "analysis", "혼잡도_분석결과.xlsx")

df = pd.read_excel(SRC, sheet_name="하차데이터")
df["구분"] = df["요일"].map(lambda x: "주말" if x in ("토", "일") else "평일")
ndays = df.groupby("구분")["일자"].nunique()

# 1) 시간대별 하차 합계
hourly = df.groupby("시간대")["하차합계"].sum().rename("하차합계").reset_index()
hourly["비중(%)"] = (hourly["하차합계"] / hourly["하차합계"].sum() * 100).round(2)

# 2) 평일/주말 비교 (일평균)
wk = df.groupby(["시간대", "구분"])["하차합계"].sum().unstack(fill_value=0)
wk = wk.div(ndays, axis=1).round(1)
wk.columns = [f"{c}_일평균" for c in wk.columns]
wk["평일/주말 비"] = (wk["평일_일평균"] / wk["주말_일평균"].replace(0, pd.NA)).astype(float).round(2)
wk = wk.reset_index()

# 3) 정류소 TOP10
st = (df.groupby(["정류소ID", "정류소명"])["하차합계"].sum()
        .sort_values(ascending=False).head(10).reset_index())
st.insert(0, "순위", range(1, len(st) + 1))

# 4) 노선별 피크 시간대
rt = df.groupby(["노선ID", "노선명", "시간대"])["하차합계"].sum().reset_index()
peak = rt.loc[rt.groupby("노선ID")["하차합계"].idxmax()].rename(columns={"시간대": "피크시간대", "하차합계": "피크하차합계"})
tot = rt.groupby("노선ID")["하차합계"].sum().rename("노선총하차")
peak = peak.merge(tot, on="노선ID")
peak["피크집중도(%)"] = (peak["피크하차합계"] / peak["노선총하차"] * 100).round(2)

# 5) 혼잡도 등급: 정류소x시간대 합계의 상위 20%=상, 20~60%=중, 나머지=하 (분위수)
cell = df.groupby(["정류소ID", "정류소명", "시간대"])["하차합계"].sum().reset_index()
q80, q40 = cell["하차합계"].quantile([0.8, 0.4])
cell["혼잡도"] = cell["하차합계"].apply(lambda v: "상" if v >= q80 else ("중" if v >= q40 else "하"))
grade_cnt = cell["혼잡도"].value_counts().reindex(["상", "중", "하"]).rename_axis("등급").reset_index(name="셀수")
crit = pd.DataFrame({"기준": ["상", "중", "하"],
                     "조건": [f"하차합계 >= {q80:.0f}", f"{q40:.0f} <= 하차합계 < {q80:.0f}", f"하차합계 < {q40:.0f}"]})
top_cell = cell.sort_values("하차합계", ascending=False)

with pd.ExcelWriter(OUT, engine="openpyxl") as w:
    hourly.to_excel(w, sheet_name="시간대별_하차합계", index=False)
    wk.to_excel(w, sheet_name="평일주말_비교", index=False)
    st.to_excel(w, sheet_name="정류소_TOP10", index=False)
    peak.to_excel(w, sheet_name="노선별_피크시간대", index=False)
    cell.to_excel(w, sheet_name="혼잡도등급_전체", index=False)
    grade_cnt.to_excel(w, sheet_name="혼잡도등급_요약", index=False)
    crit.to_excel(w, sheet_name="혼잡도등급_요약", index=False, startcol=4)

print("hourly top3:\n", hourly.sort_values("하차합계", ascending=False).head(3).to_string(index=False))
print("weekday/weekend days:", ndays.to_dict())
print(wk.to_string(index=False))
print(st.to_string(index=False))
print(peak.to_string(index=False))
print(crit.to_string(index=False)); print(grade_cnt.to_string(index=False))
print("total", df["하차합계"].sum())

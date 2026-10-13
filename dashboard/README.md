# 노선별 하차 현황 대시보드

`python make_dummy.py`로 만든 `버스_노선_하차_더미데이터.xlsx`(하차데이터 시트)를 읽어 단일 HTML을 생성한다.

```
pip install pandas openpyxl
python dashboard/build_dashboard.py   # -> dashboard/index.html
```

- 노선 드롭다운(전체 포함), KPI(총 하차/피크 시간대/최다 하차 정류소)
- 시간대별 라인, 정류소별 막대, 승객유형 도넛, 요일별 막대
- 데이터는 HTML에 JSON으로 인라인, Chart.js 4.4.1은 cdnjs에서 로드(인터넷 필요)
- 라이트/다크 자동(prefers-color-scheme), 모바일 폭 가로 스크롤 없음
- xlsx는 .gitignore 대상이라 커밋하지 않음

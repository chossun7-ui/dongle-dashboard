# 오사카 숙소 자동 비교 도구

> `dongle-dashboard` 저장소의 본래 목적(설비 Film Script 비교 대시보드)과는 **무관한 독립 CLI 도구**입니다.
> 브랜치 `claude/osaka-accommodation-comparison-bs6djd` 작업 요청에 따라 이 저장소 안에 별도 디렉토리로 추가되었습니다.

## 목적

2026-10-08(목) 체크인 ~ 2026-10-12(월) 체크아웃(4박), 성인 3명 기준으로 오사카 숙소를
**4박 총액(세금 포함) 오름차순**으로 자동 비교해 `results.md` / `results.csv`를 생성합니다.

날짜·인원은 CLI 인자로 바꿔서 재실행할 수 있도록 파라미터화되어 있습니다.

## 사용법

```bash
cd osaka-hotel-compare
pip install -r requirements.txt
cp .env.example .env   # API 키를 갖고 있다면 채워 넣기

python compare.py \
  --checkin 2026-10-08 --checkout 2026-10-12 \
  --adults 3 --rooms-preferred 1 \
  --out-dir .
```

키가 없어도 실행은 되며, 이 경우 `data/manual_research.json`에 저장된 **수동 조사 데이터**만
사용합니다(수동 데이터는 조사 시점·조회 URL이 각 항목에 명시되어 있고, 요청한 날짜/인원과
정확히 일치하지 않으면 자동으로 사용하지 않고 N/A 처리합니다).

## 데이터 소스 우선순위

1. **라쿠텐 트래블 공실검색 API** (`RAKUTEN_APP_ID` 환경변수 필요)
2. **Amadeus Self-Service Hotel Search API** (`AMADEUS_CLIENT_ID`/`AMADEUS_CLIENT_SECRET` 필요, OAuth2 client-credentials)
3. **SerpAPI Google Hotels** (`SERPAPI_KEY` 필요, 유료)
4. 위 API가 전부 비활성화(키 없음) 상태면 `data/manual_research.json`의 수동 조사값을 사용

**아고다·부킹닷컴·트립닷컴 등 OTA 페이지의 자동 스크래핑이나 로그인 자동화는 절대 하지 않습니다**
(명세 4번 항목 "절대 하지 말 것" 참고). 수동 조사값도 호텔 공식 홈페이지 / 라쿠텐 트래블 공개
페이지에서만 확인한 것입니다.

## ⚠️ 이번 세션(Claude Code 원격 실행 환경)에서의 알려진 한계

2026-07-29 작업 시점 기준으로 이 환경의 `WebFetch` 도구가 **모든 URL에 대해 HTTP 403을
반환하는 전면 장애 상태**였습니다(대조군으로 시도한 `example.com`조차 403). 그 결과:

- 각 호텔의 **정확한 날짜별·인원별 실시간 가격**은 페이지 본문을 열람해야 얻을 수 있는데,
  이번 조사에서는 이를 열람하지 못해 다수 숙소가 `price_found: false`로 남아 있습니다.
- `WebSearch`(검색 스니펫)로 확인 가능한 일반 정보(객실 컨셉, 위치, 대략적 최저가 문구 등)만
  `data/manual_research.json`의 `notes` 필드에 기록해 두었고, **날짜 특정 가격이 아닌 값은
  `nightly_rates_jpy`/`total_4nights_jpy`에 채우지 않았습니다** (명세의 "추정치 금지" 원칙 준수).
- 따라서 `results.md`의 상당수 행이 N/A입니다. 이는 도구 결함이 아니라 **"확인 못 한 값은
  추정하지 않는다"는 원칙을 지킨 결과**입니다. 사용자가 실제 예약 전 반드시 직접 확인해야
  합니다(섹션 6 체크리스트 참고).
- WebFetch가 정상화된 환경에서 이 스크립트의 API 연동부(특히 `sources/rakuten.py`)를
  실행하면 실시간 값으로 자동 채워집니다. API 키만 `.env`에 넣으면 됩니다.

## 라쿠텐 트래블 API 참고 사항

`sources/rakuten.py`의 엔드포인트/파라미터명은 공식 문서(`https://webservice.rakuten.co.jp/documentation/vacant-hotel-search`)
페이지를 이번 세션에서 WebFetch로 직접 열람하지 못해, 검색엔진 스니펫과 서드파티 기술
블로그 인용을 근거로 작성했습니다. **실제 사용 전 공식 문서로 파라미터명·응답 스키마를
재확인**하세요. 확인된 것과 미확인/추정인 것을 코드 주석에 구분해 표시해 두었습니다.

## 디렉토리 구조

```
osaka-hotel-compare/
├── compare.py              # CLI 진입점
├── config.py                # 고정 조건 + CLI 인자
├── requirements.txt
├── .env.example
├── sources/
│   ├── rakuten.py           # 라쿠텐 트래블 공실검색 API 연동 (요 문서 재확인 필요)
│   ├── amadeus.py           # Amadeus Hotel Search API v3 연동
│   ├── serpapi_source.py    # SerpAPI Google Hotels 연동
│   └── manual.py            # data/manual_research.json 로더
├── lib/
│   ├── tax.py                # 오사카부 숙박세 계산
│   ├── fx.py                 # JPY→KRW 환율 (실시간 조회 + 캐시 폴백)
│   ├── aggregate.py          # 소스 병합·정렬·2실 분할 판정
│   └── output.py             # results.md / results.csv / checklist 생성
├── data/
│   ├── candidates.json       # 조사 대상 숙소 목록(지역·시드 여부)
│   ├── manual_research.json  # 2026-07-29 수동 조사 원본 데이터(출처 URL 포함)
│   └── fx_cache.json         # 환율 폴백 캐시
├── results.md
├── results.csv
└── checklist.md
```

## 완료 기준 체크 (명세 7번)

- [x] 시드 후보 9곳 전부 조회 시도 — 실패 사유는 `data/manual_research.json`의 `failure_reason`에 기록
- [x] 날짜별 단가 분리 구조(`nightly_rates_jpy`) 마련 — 실제 값은 소스가 줄 때만 채움
- [x] 1실 3인 불가 시 2실 분할 총액 대체 계산 로직(`lib/aggregate.py`) 구현
- [x] 추정치 없이 실제 확인값만 표에 반영(N/A 유지)
- [x] `--checkin/--checkout/--adults/--rooms-preferred`만 바꿔 재실행 가능하도록 파라미터화

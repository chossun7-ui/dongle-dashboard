# Recipe Film Script 비교 대시보드

반도체/디스플레이 라인 설비의 **Film Script(공정 레시피)** 를 FTP로 원격 수집하고, 같은 Film 이름끼리 자동 페어링해 차이를 한눈에 비교하는 사내 웹 대시보드.

## 핵심 기능

- 라인 · 모델 · 설비 다중선택 → 일괄 FTP 스캔
- `as<숫자>` 폴더 단위 Recipe 자동 감지 (`analysis2.txt` + `StrategyID.ini` 쌍)
- Film 이름(`StrategyName`) 기준 자동 페어링 + 사용자 수동 보완
- 의미 단위 비교 (섹션 · 키-값 구조 인식)
- 변경 이력 시계열 추적 (어제 vs 오늘)
- 전체 Script 풀텍스트 검색 (SQLite FTS5)
- 즐겨찾기 · 프리셋
- 비교 결과 Export (HTML · CSV · PDF)

## 빠른 시작

### 운영 (Docker Compose)

```bash
cp .env.example .env
# .env 에서 ADMIN_PASSWORD, FERNET_KEY 등 변경
docker compose up -d
# http://<server>:8080 접속
```

### 개발 (로컬)

```bash
# 백엔드
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000

# 프론트엔드
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## 디렉토리 구조

```
backend/    FastAPI + asyncio + aioftp + SQLite
frontend/   React + Vite + TypeScript + Tailwind
docs/       비교 알고리즘 명세, API 문서, 데이터 모델
```

## 비교 알고리즘 본체

본체는 사내 AI가 실제 `analysis2.txt`·`StrategyID.ini` 샘플을 받아 작성한다.
본 저장소에는 **인터페이스**(타입·시그니처·예제·기대 출력)만 정의되어 있다.

작성 시 참고:
- 사양: [docs/COMPARE_ALGORITHM_SPEC.md](docs/COMPARE_ALGORITHM_SPEC.md)
- 구현 자리: `backend/app/compare/`
- 더미 구현: `backend/app/compare/stub.py` (인터페이스 충족만 함, 실제 비교는 미수행)

## 라이선스

사내용. 외부 공개 금지.

## 인계 문서

본 저장소에서 작업하는 모든 후속 AI 에이전트는 [CLAUDE.md](CLAUDE.md)를 세션 시작 시 가장 먼저 읽어야 한다.

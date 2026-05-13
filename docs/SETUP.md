# 셋업 가이드

## 1. 운영 (Docker Compose)

```bash
cp .env.example .env
# FERNET_KEY 생성 후 .env에 채워 넣는다:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# ADMIN_PASSWORD도 강한 값으로 변경.

docker compose up -d --build
# http://<server>:8080 접속
```

데이터 영속: 호스트의 `./data/recipe.db`에 저장된다. 백업은 이 파일을 그대로 복사하면 충분 (WAL 모드라 `.db`, `.db-wal`, `.db-shm` 함께 복사 권장 — 가능하면 서비스 정지 후).

## 2. 개발 (로컬)

### 백엔드

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# .env 또는 환경변수 셋업
export FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export ADMIN_PASSWORD=devadmin
export SESSION_SECRET=devsecret

uvicorn app.main:app --reload --port 8000
```

테스트:

```bash
pytest -q
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173 — Vite가 /api를 localhost:8000으로 프록시한다.
```

타입 체크:

```bash
npm run typecheck
```

## 3. 첫 부팅 시 할 일

1. `/login`으로 가서 ADMIN_PASSWORD로 로그인.
2. 관리자 페이지에서:
   - 라인 등록 (예: `P1`, `P2`)
   - 모델 등록 (예: `IRIS`, `ATLAS`)
   - 설비 등록 (예: `MTKB561`, `MTKB562`)
   - (별도 페이지/엔드포인트) FTP 전역설정 등록 — `PUT /api/ftp-config`
3. 일반 페이지(`/`)에서 라인/모델/설비 다중선택 후 "재스캔" 클릭.

## 4. 비교 알고리즘 본체 교체 절차

1. 사내 AI가 작성한 `algorithm.py`를 받는다.
2. `backend/app/compare/algorithm.py`에 그대로 배치 (인터페이스 충족 필수 — `docs/COMPARE_ALGORITHM_SPEC.md` 참고).
3. `backend/tests/test_compare_stub.py`가 통과하는지 확인 (계약 테스트).
4. 컨테이너 재기동: `docker compose restart backend`.
5. 더 이상 stub 폴백 경고 로그가 뜨지 않아야 한다.

## 5. 트러블슈팅

- **`FERNET_KEY가 설정되지 않았습니다`** : `.env`에 FERNET_KEY를 세팅. 키는 외부에 보관 백업.
- **첫 로그인 실패** : 컨테이너 재기동 후 다시 시도. `.env`의 ADMIN_PASSWORD 변경은 DB의 admin 테이블이 비어 있을 때만 부트스트랩에 사용된다(이미 한 번 부팅된 후엔 무시).
- **FTP 연결 실패** : 평문 FTP인지 (FTPS 아님), PASV/ACTIVE 모드, 방화벽 데이터 포트 범위 확인.

# 맞춤 뉴스브리프

관심 키워드와 추가 설명을 기반으로 관련 뉴스를 선별하고 요약해 보여주는 웹 대시보드입니다.

## 주요 기능

- 이메일/비밀번호 기반 로그인
- 관심 키워드와 추가 설명 등록
- Google News RSS 기반 뉴스 수집
- 숨은 키워드와 조건에 맞는 뉴스 선별
- 테스트용 AI adapter를 통한 요약 흐름 확인
- 뉴스 요약 대시보드
- 원문 링크 제공

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| Frontend | React, Vite, TypeScript |
| Backend | Python, FastAPI |
| Database | SQLite file DB |
| News API | Google News RSS, sample provider |
| AI | Local AI Console, Codex CLI adapter, mock adapter |
| Deploy | Cloudflare Pages frontend, local FastAPI backend |

## 실행 방법

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

서버가 실행되면 `http://127.0.0.1:8000/health`에서 상태를 확인할 수 있습니다.

### Frontend

Frontend 구조가 추가된 뒤에는 아래 명령으로 실행합니다.

```powershell
cd frontend
npm install
npm run dev
```

프론트엔드는 `VITE_API_BASE_URL` 값으로 백엔드 API 주소를 사용합니다.

## 환경 변수

환경 변수 예시는 `.env.example`을 참고합니다.

주의:

- `.env` 파일은 저장소에 올리지 않습니다.
- API key, DB 접속 문자열, 비밀번호는 commit하지 않습니다.
- SQLite DB 파일은 로컬 실행 중 생성될 수 있으며 저장소에 올리지 않습니다.

## License

MIT License

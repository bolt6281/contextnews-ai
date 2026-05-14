# 맞춤 뉴스브리프

관심 키워드와 추가 설명을 기반으로 관련 뉴스를 선별하고 요약해 보여주는 웹 대시보드입니다.

## 주요 기능

- 이메일/비밀번호 기반 로그인
- 관심 키워드와 추가 설명 등록
- 키워드 기반 뉴스 수집
- 조건에 맞는 뉴스 선별
- 뉴스 요약 대시보드
- 원문 링크 제공

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| Frontend | React, Vite, TypeScript |
| Backend | Python, FastAPI |
| Database | Supabase Postgres |
| News API | Google News RSS |
| Deploy | Cloudflare Pages, Render |

## 실행 방법

아직 초기 개발 단계입니다. 실행 방법은 프론트엔드와 백엔드 구조가 추가된 뒤 업데이트합니다.

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

## 환경 변수

환경 변수 예시는 `.env.example`을 참고합니다.

주의:

- `.env` 파일은 저장소에 올리지 않습니다.
- DB 접속 문자열, 비밀번호는 commit하지 않습니다.
- Google News RSS는 API key 없이 동작합니다.
- `NEWS_PROVIDER=sample`은 외부 호출 없이 테스트 데이터를 반환합니다.
- `NEWS_PROVIDER=google_news_rss`는 Google News RSS를 호출합니다.

## License

MIT License

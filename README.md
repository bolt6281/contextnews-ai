# 맞춤 뉴스브리프 (ContextNews AI)

AI 기반 실시간 뉴스 요약 대시보드 팀 프로젝트입니다.

사용자가 관심 키워드와 추가 설명을 등록하면, 서버는 해당 키워드가 포함된 뉴스를 수집하고 AI 작업 큐에 분석 작업을 쌓습니다. 팀장 PC의 Local AI Console이 큐에 쌓인 작업을 가져와 Codex CLI로 처리하고, 최종 통과한 뉴스만 사용자 대시보드에 요약 형태로 표시합니다.

## 프로젝트 개요

- 과목: 오픈소스SW개발
- 팀장: 신승민
- 팀원: 송찬형, 신윤지, 정성익
- 저장소 세팅일: 2026-05-11
- 개발 기간: 2026-05-13 ~ 2026-05-29
- 제출 마감: 2026-06-08 23:59

## 핵심 기능

- 자체 이메일/비밀번호 회원가입 및 로그인
- 관심 키워드와 추가 설명 등록
- AI 기반 숨은 추가키워드 생성
- Naver News Search API 기반 뉴스 수집
- 숨은 추가키워드 기반 후보 뉴스 필터링
- AI 최종 판단 및 뉴스 요약
- 사용자별 실시간 뉴스 요약 대시보드
- 팀장 PC의 Codex CLI를 사용하는 Local AI Console
- Codex CLI 없이도 실행 가능한 Mock AI 모드

## 기술 스택

| 영역 | 기술 |
| --- | --- |
| Frontend | React, Vite, TypeScript |
| Backend | Python, FastAPI |
| Database | Supabase Postgres |
| News API | Naver News Search API |
| AI 처리 | Local AI Console, Codex CLI, Mock AI |
| 배포 | Vercel, Render |

## GitHub 협업 방식

이 프로젝트는 GitHub Flow를 사용합니다.

```text
Issue 생성
-> feature branch 생성
-> 작업 commit
-> push
-> pull request 생성
-> 팀장 review
-> merge
-> Issue close
```

기본 규칙:

- `main` branch에 직접 push하지 않습니다.
- 모든 작업은 Issue 기반으로 진행합니다.
- 모든 기능은 feature branch에서 작업합니다.
- 모든 병합은 Pull Request로 처리합니다.
- 팀장 신승민이 PR을 review하고 merge합니다.
- 최소 1회 이상 README 충돌 해결 실습을 진행합니다.
- 최종 제출 전 GitHub Release와 tag를 생성합니다.

## Branch 규칙

```text
feature/issue-번호-짧은설명
fix/issue-번호-짧은설명
docs/issue-번호-짧은설명
chore/issue-번호-짧은설명
test/issue-번호-짧은설명
```

예시:

```text
feature/issue-05-auth-api
feature/issue-07-auth-ui
docs/issue-19-readme-guide
```

## Commit 규칙

```text
type: 작업 요약
```

| type | 의미 |
| --- | --- |
| feat | 기능 추가 |
| fix | 버그 수정 |
| docs | 문서 수정 |
| test | 테스트 추가/수정 |
| refactor | 동작 변경 없는 구조 개선 |
| chore | 설정, 빌드, 기타 작업 |

예시:

```text
feat: add auth form UI
feat: add email login API
test: add candidate filter tests
docs: update setup guide
```

## 공식 체크포인트

| 회차 | 날짜 | 목표 |
| --- | --- | --- |
| 1 | 2026-05-11 | repo, Issue, branch 규칙, 기본 문서 정리 |
| 2 | 2026-05-16 | 프론트/백엔드 뼈대, 로그인, 필터링 초안 |
| 3 | 2026-05-20 | 관심 조건, AI job, mock AI, 뉴스 수집 흐름 |
| 4 | 2026-05-23 | 1차 통합 데모, README 충돌 해결 실습 |
| 5 | 2026-05-26 | Codex adapter, Supabase, Vercel/Render 배포 |
| 6 | 2026-05-29 | 최종 README, 보고서 자료, v1.0.0 release |

## 로컬 실행 안내

아직 초기 세팅 단계입니다. 실제 실행 방법은 프론트엔드와 백엔드 scaffold가 추가된 뒤 업데이트합니다.

예정 실행 흐름:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

```powershell
cd frontend
npm install
npm run dev
```

## 환경 변수

환경 변수 예시는 `.env.example`을 참고합니다.

주의:

- `.env` 파일은 GitHub에 올리지 않습니다.
- API key, DB 접속 문자열, 비밀번호는 commit하지 않습니다.

## License

MIT License

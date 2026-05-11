# Cloudflare Pages 배포

프론트엔드는 Cloudflare Pages에 배포한다.

## 현재 설정

- Cloudflare Pages project: `contextnews-ai`
- 기본 도메인: `https://contextnews-ai.pages.dev`
- Production branch: `main`
- Frontend root: `frontend`
- Build command: `npm run build`
- Build output: `frontend/dist`

Cloudflare Pages의 GitHub 직접 연동은 현재 Cloudflare 쪽에서 Git 계정을 `disconnected` 상태로 보고 있어 사용하지 않는다. 대신 GitHub Actions에서 빌드한 정적 파일을 Wrangler Direct Upload 방식으로 Cloudflare Pages에 업로드한다.

## 배포 흐름

1. `main` 브랜치에 `frontend/**` 변경사항이 push된다.
2. GitHub Actions가 `frontend`에서 의존성을 설치한다.
3. `npm run build`로 Vite 빌드를 실행한다.
4. `cloudflare/wrangler-action`이 `frontend/dist`를 `contextnews-ai` Pages 프로젝트에 배포한다.

워크플로우 파일은 `.github/workflows/cloudflare-pages.yml`이다.

## GitHub Secrets

GitHub 저장소의 `Settings > Secrets and variables > Actions`에 아래 secrets를 등록해야 한다.

| Name | Value |
| --- | --- |
| `CLOUDFLARE_ACCOUNT_ID` | `5d01da987c4aff18915b6b9288bf7a40` |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token |

`CLOUDFLARE_API_TOKEN`은 Cloudflare에서 Custom token으로 만든다.

필요 권한:

- Account: Cloudflare Pages: Edit

## 수동 배포

필요하면 GitHub Actions의 `Deploy frontend to Cloudflare Pages` workflow를 `workflow_dispatch`로 직접 실행할 수 있다. 단, `frontend` 폴더와 GitHub secrets가 먼저 준비되어 있어야 한다.

## 참고

- GitHub Pages의 `github.io` 도메인은 사용하지 않는다.
- Cloudflare Pages 기본 도메인은 `contextnews-ai.pages.dev`이다.
- 백엔드는 별도 Render 배포를 사용한다.

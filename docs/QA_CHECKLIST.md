# QA Checklist

## Automated

- [ ] Backend test suite passes with `pytest`.
- [ ] Candidate filter keeps articles when one or more hidden keywords are included.
- [ ] Candidate filter stores the matched keyword list.
- [ ] Google News RSS item normalization returns `title`, `url`, `source`, `description`, and `published_at`.
- [ ] Google News RSS descriptions are saved without HTML tags.
- [ ] Test AI adapter returns hidden keywords, candidate decisions, summaries, and bullet points.
- [ ] Sample provider can run without external network calls.

## Manual

- [ ] Register a new account.
- [ ] Log in with the new account.
- [ ] Create an interest with keyword, description, and lookback days.
- [ ] Delete an interest keyword.
- [ ] Select a news lookback period.
- [ ] Run the Local AI Console flow.
- [ ] Collect news and confirm cards render.
- [ ] Open a news detail modal.
- [ ] Open the original article link.
- [ ] Toggle read/unread state.
- [ ] Follow the README setup steps on a clean environment.

## Notes

- Google News RSS is URL based and does not require an API key.
- Use the `sample` provider for deterministic local tests.

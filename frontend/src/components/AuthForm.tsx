import { useState } from "react";
import { LogIn, UserPlus } from "lucide-react";
import { apiRequest, setAuthToken } from "../api/client";
import type { AuthResponse, User } from "../types";

type AuthFormProps = {
  onAuth: (user: User) => void;
};

export function AuthForm({ onAuth }: AuthFormProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isRegister = mode === "register";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const user = await apiRequest<AuthResponse>(isRegister ? "/api/auth/register" : "/api/auth/login", {
        method: "POST",
        body: isRegister ? { email, password, display_name: displayName } : { email, password }
      });
      setAuthToken(user.session_token);
      onAuth(user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "로그인 처리에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-shell">
      <section className="auth-panel" aria-labelledby="auth-title">
        <div className="brand-lockup">
          <div className="brand-mark">CN</div>
          <div>
            <p className="brand-name">ContextNews</p>
            <p className="brand-caption">뉴스 요약 대시보드</p>
          </div>
        </div>

        <div className="auth-heading">
          <h1 id="auth-title">{isRegister ? "계정 만들기" : "로그인"}</h1>
          <p>관심 키워드를 등록하고 선별된 뉴스 요약을 확인합니다.</p>
        </div>

        <div className="segmented-control" role="tablist" aria-label="인증 방식">
          <button
            type="button"
            className={mode === "login" ? "is-active" : ""}
            onClick={() => setMode("login")}
          >
            로그인
          </button>
          <button
            type="button"
            className={mode === "register" ? "is-active" : ""}
            onClick={() => setMode("register")}
          >
            회원가입
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {isRegister ? (
            <label>
              이름
              <input
                value={displayName}
                minLength={2}
                maxLength={20}
                placeholder="이름"
                onChange={(event) => setDisplayName(event.target.value)}
                required
              />
            </label>
          ) : null}

          <label>
            이메일
            <input
              type="email"
              value={email}
              placeholder="email@example.com"
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>

          <label>
            비밀번호
            <input
              type="password"
              value={password}
              placeholder="비밀번호"
              minLength={isRegister ? 8 : 1}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {error ? <p className="error-message">{error}</p> : null}

          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isRegister ? <UserPlus size={18} /> : <LogIn size={18} />}
            {isSubmitting ? "처리 중" : isRegister ? "회원가입" : "로그인"}
          </button>
        </form>
      </section>
    </main>
  );
}

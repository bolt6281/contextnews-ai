import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { apiRequest, clearAuthToken } from "./api/client";
import { AuthForm } from "./components/AuthForm";
import type { User } from "./types";

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function bootstrap() {
      try {
        const currentUser = await apiRequest<User>("/api/auth/me");
        if (!isMounted) return;
        setUser(currentUser);
      } catch {
        if (isMounted) {
          clearAuthToken();
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    bootstrap();

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleAuth(authUser: User) {
    setUser(authUser);
  }

  async function handleLogout() {
    try {
      await apiRequest<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
    } finally {
      clearAuthToken();
    }
    setUser(null);
  }

  if (isLoading) {
    return <div className="loading-screen">ContextNews</div>;
  }

  if (!user) {
    return <AuthForm onAuth={handleAuth} />;
  }

  return (
    <div className="app-shell">
      <main className="dashboard-main" style={{ padding: '2rem' }}>
        <header className="topbar">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h1>{user.display_name}님의 뉴스</h1>
          </div>
          <div className="topbar-actions">
            <button className="icon-text-button" type="button" onClick={handleLogout}>
              <LogOut size={17} />
              로그아웃
            </button>
          </div>
        </header>
        
        <section className="content-section">
          <div className="empty-state">
            <h3>로그인 성공!</h3>
            <p>프론트엔드 인증 스캐폴딩이 완료되었습니다.</p>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;

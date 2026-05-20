import { useEffect, useState } from "react";
import { LogOut, RefreshCcw } from "lucide-react";
import { apiRequest, clearAuthToken } from "./api/client";
import { AuthForm } from "./components/AuthForm";
import { DashboardStats } from "./components/DashboardStats";
import { InterestForm } from "./components/InterestForm";
import { InterestList } from "./components/InterestList";
import { NewsCard } from "./components/NewsCard";
import { NewsDetailModal } from "./components/NewsDetailModal";
import { WorkerStatusBadge } from "./components/WorkerStatusBadge";
import type { DashboardItem, DashboardResponse, RefreshResponse, User } from "./types";

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedInterestId, setSelectedInterestId] = useState<number | null>(null);
  const [selectedItem, setSelectedItem] = useState<DashboardItem | null>(null);
  const [deletingInterestId, setDeletingInterestId] = useState<number | null>(null);

  async function loadDashboard() {
    const data = await apiRequest<DashboardResponse>("/api/dashboard");
    setDashboard(data);
    setUser(data.user);
  }

  useEffect(() => {
    let isMounted = true;

    async function bootstrap() {
      try {
        const currentUser = await apiRequest<User>("/api/auth/me");
        if (!isMounted) {
          return;
        }
        setUser(currentUser);
        await loadDashboard();
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
    setError("");
    setNotice("");
    await loadDashboard();
  }

  async function handleLogout() {
    try {
      await apiRequest<{ ok: boolean }>("/api/auth/logout", { method: "POST" });
    } finally {
      clearAuthToken();
    }
    setUser(null);
    setDashboard(null);
    setNotice("");
    setError("");
  }

  async function handleRefresh() {
    setIsRefreshing(true);
    setError("");
    setNotice("");

    try {
      const result = await apiRequest<RefreshResponse>("/api/refresh", {
        method: "POST",
        body: { limit_per_interest: 10 }
      });
      setNotice(
        `수집 ${result.fetched_articles}건, 후보 ${result.candidate_articles}건, AI 작업 ${result.created_ai_jobs}건`
      );
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "새로고침에 실패했습니다.");
    } finally {
      setIsRefreshing(false);
    }
  }

  async function handleInterestCreated() {
    setNotice("키워드가 등록되었습니다.");
    await loadDashboard();
  }

  async function handleDeleteInterest(interestId: number, keyword: string) {
    if (!window.confirm(`'${keyword}' 키워드를 삭제할까요?`)) {
      return;
    }

    setDeletingInterestId(interestId);
    setError("");
    setNotice("");

    try {
      await apiRequest<{ ok: boolean; interest_id: number }>(`/api/interests/${interestId}`, { method: "DELETE" });
      if (selectedInterestId === interestId) {
        setSelectedInterestId(null);
      }
      setNotice("키워드가 삭제되었습니다.");
      await loadDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : "키워드 삭제에 실패했습니다.");
    } finally {
      setDeletingInterestId(null);
    }
  }

  async function handleOpenItem(item: DashboardItem) {
    setSelectedItem(item);

    if (item.is_read) {
      return;
    }

    setDashboard((current) => markItemRead(current, item.article_id));
    try {
      await apiRequest<{ article_id: number; is_read: boolean; read_at: string }>(
        `/api/dashboard/articles/${item.article_id}/read`,
        { method: "POST" }
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "읽음 처리에 실패했습니다.");
    }
  }

  const visibleItems =
    dashboard?.items.filter((item) => selectedInterestId === null || item.interest_id === selectedInterestId) ?? [];
  const selectedInterest = dashboard?.interests.find((interest) => interest.id === selectedInterestId);

  if (isLoading) {
    return <div className="loading-screen">ContextNews</div>;
  }

  if (!user) {
    return <AuthForm onAuth={handleAuth} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark">CN</div>
          <div>
            <p className="brand-name">ContextNews</p>
            <p className="brand-caption">실시간 뉴스 요약</p>
          </div>
        </div>

        <section className="panel">
          <div className="section-heading">
            <h2>관심 키워드</h2>
          </div>
          <InterestForm onCreated={handleInterestCreated} />
        </section>

        <section className="panel">
          <div className="section-heading">
            <h2>등록 목록</h2>
          </div>
          <InterestList
            interests={dashboard?.interests ?? []}
            selectedInterestId={selectedInterestId}
            onSelect={setSelectedInterestId}
            onDelete={(interest) => handleDeleteInterest(interest.id, interest.keyword)}
            deletingInterestId={deletingInterestId}
          />
        </section>
      </aside>

      <main className="dashboard-main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h1>{user.display_name}님의 뉴스</h1>
          </div>
          <div className="topbar-actions">
            {dashboard ? <WorkerStatusBadge worker={dashboard.worker} /> : null}
            <button className="secondary-button" type="button" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCcw size={17} />
              {isRefreshing ? "새로고침 중" : "뉴스 새로고침"}
            </button>
            <button className="icon-text-button" type="button" onClick={handleLogout}>
              <LogOut size={17} />
              로그아웃
            </button>
          </div>
        </header>

        {dashboard ? <DashboardStats stats={dashboard.stats} /> : null}

        {notice ? <p className="notice-message">{notice}</p> : null}
        {error ? <p className="error-message wide">{error}</p> : null}

        <section className="content-section">
          <div className="section-heading horizontal">
            <div>
              <h2>요약 뉴스</h2>
              <p>{selectedInterest ? `${selectedInterest.keyword} ${visibleItems.length}건` : `${visibleItems.length}건`}</p>
            </div>
          </div>

          <div className="news-list">
            {visibleItems.length ? (
              visibleItems.map((item) => (
                <NewsCard key={`${item.article_id}-${item.interest_id}-${item.decided_at}`} item={item} onOpen={handleOpenItem} />
              ))
            ) : (
              <div className="empty-state">
                <h3>표시할 뉴스가 없습니다.</h3>
                <p>키워드를 등록한 뒤 AI 작업과 뉴스 새로고침이 완료되면 요약이 표시됩니다.</p>
              </div>
            )}
          </div>
        </section>
      </main>
      {selectedItem ? <NewsDetailModal item={selectedItem} onClose={() => setSelectedItem(null)} /> : null}
    </div>
  );
}

function markItemRead(dashboard: DashboardResponse | null, articleId: number): DashboardResponse | null {
  if (!dashboard) {
    return dashboard;
  }

  return {
    ...dashboard,
    items: dashboard.items.map((item) =>
      item.article_id === articleId ? { ...item, is_read: true, read_at: item.read_at ?? new Date().toISOString() } : item
    )
  };
}

export default App;

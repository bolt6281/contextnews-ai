import { FileText, ListFilter, Newspaper, Timer } from "lucide-react";
import type { DashboardStats as Stats } from "../types";

type DashboardStatsProps = {
  stats: Stats;
};

const statItems = [
  { key: "interest_count", label: "관심 키워드", icon: ListFilter },
  { key: "accepted_articles", label: "승인 뉴스", icon: Newspaper },
  { key: "candidate_articles", label: "후보 뉴스", icon: FileText },
  { key: "pending_ai_jobs", label: "AI 대기", icon: Timer }
] as const;

export function DashboardStats({ stats }: DashboardStatsProps) {
  return (
    <section className="stats-grid" aria-label="대시보드 통계">
      {statItems.map((item) => {
        const Icon = item.icon;
        return (
          <article className="stat-card" key={item.key}>
            <div className="stat-icon" aria-hidden="true">
              <Icon size={18} />
            </div>
            <div>
              <p>{item.label}</p>
              <strong>{stats[item.key]}</strong>
            </div>
          </article>
        );
      })}
    </section>
  );
}

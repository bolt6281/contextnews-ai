export type User = {
  id: number;
  email: string;
  display_name: string;
};

export type AuthResponse = User & {
  session_token: string;
};

export type Interest = {
  id: number;
  keyword: string;
  description: string;
  lookback_days: number;
  created_at: string;
};

export type DashboardStats = {
  interest_count: number;
  candidate_articles: number;
  pending_ai_jobs: number;
  accepted_articles: number;
};

export type WorkerStatus = {
  worker_id?: string;
  status: string;
  last_seen_at?: string;
  processed_count?: number;
};

export type DashboardItem = {
  article_id: number;
  interest_id: number;
  title: string;
  source: string;
  url: string;
  description: string;
  published_at: string;
  keyword: string;
  summary: string;
  bullet_points: string[];
  decision_reason: string;
  decided_at: string;
  read_at: string | null;
  is_read: boolean;
};

export type DashboardResponse = {
  user: User;
  interests: Interest[];
  stats: DashboardStats;
  worker: WorkerStatus;
  items: DashboardItem[];
};

export type RefreshResponse = {
  fetched_articles: number;
  candidate_articles: number;
  created_ai_jobs: number;
  pending_ai_jobs: number;
};

export type InterestCreateResponse = Interest & {
  ai_job_id: number | null;
  ai_job_status: string | null;
};

import { ExternalLink, X } from "lucide-react";
import type { DashboardItem } from "../types";

type NewsDetailModalProps = {
  item: DashboardItem;
  onClose: () => void;
};

export function NewsDetailModal({ item, onClose }: NewsDetailModalProps) {
  const publishedAt = new Date(item.published_at).toLocaleString("ko-KR", {
    dateStyle: "full",
    timeStyle: "short"
  });

  return (
    <div className="modal-scrim" role="presentation" onMouseDown={onClose}>
      <section
        className="news-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="news-modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div className="news-meta">
            <span>{item.keyword}</span>
            <span>{item.source}</span>
            <time dateTime={item.published_at}>{publishedAt}</time>
          </div>
          <button className="icon-only-button" type="button" onClick={onClose} aria-label="닫기">
            <X size={18} />
          </button>
        </div>

        <h2 id="news-modal-title">{item.title}</h2>
        <p className="modal-summary">{item.summary}</p>
        <p className="modal-description">{item.description}</p>

        {item.bullet_points.length > 0 ? (
          <ul className="bullet-list modal-bullets">
            {item.bullet_points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        ) : null}

        <div className="modal-reason">
          <strong>AI 판단</strong>
          <p>{item.decision_reason}</p>
        </div>

        <div className="modal-actions">
          <a className="primary-link-button" href={item.url} target="_blank" rel="noreferrer">
            원문 보기
            <ExternalLink size={16} />
          </a>
          <button className="icon-text-button" type="button" onClick={onClose}>
            나가기
          </button>
        </div>
      </section>
    </div>
  );
}

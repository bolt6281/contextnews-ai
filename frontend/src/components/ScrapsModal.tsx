import { ExternalLink, Trash2, X } from "lucide-react";
import type { DashboardItem } from "../types";

type ScrapsModalProps = {
  items: DashboardItem[];
  isLoading: boolean;
  error: string;
  deletingCandidateId: number | null;
  onClose: () => void;
  onDelete: (item: DashboardItem) => void;
};

export function ScrapsModal({
  items,
  isLoading,
  error,
  deletingCandidateId,
  onClose,
  onDelete
}: ScrapsModalProps) {
  return (
    <div className="modal-scrim" role="presentation" onMouseDown={onClose}>
      <section
        className="news-modal scraps-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="scraps-modal-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <p className="eyebrow">Scraps</p>
            <h2 id="scraps-modal-title">스크랩 목록</h2>
          </div>
          <button className="icon-only-button" type="button" onClick={onClose} aria-label="닫기">
            <X size={18} />
          </button>
        </div>

        {error ? <p className="error-message wide">{error}</p> : null}

        {isLoading ? (
          <p className="empty-text">스크랩 목록을 불러오는 중입니다.</p>
        ) : items.length ? (
          <ul className="scrap-list">
            {items.map((item) => (
              <li className="scrap-item" key={item.candidate_article_id}>
                <div className="scrap-item-header">
                  <div className="news-meta">
                    <span>{item.keyword}</span>
                    <span>{item.source}</span>
                    {item.scrapped_at ? <time dateTime={item.scrapped_at}>{formatDate(item.scrapped_at)}</time> : null}
                  </div>
                  <button
                    className="interest-delete-button"
                    type="button"
                    onClick={() => onDelete(item)}
                    disabled={deletingCandidateId === item.candidate_article_id}
                    aria-label={`${item.title} 스크랩 삭제`}
                    title="스크랩 삭제"
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </button>
                </div>
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <div className="scrap-item-actions">
                  <a className="primary-link-button" href={item.url} target="_blank" rel="noreferrer">
                    원문 보기
                    <ExternalLink size={16} />
                  </a>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="empty-state compact">
            <h3>스크랩한 뉴스가 없습니다.</h3>
            <p>요약 뉴스 상세에서 스크랩을 누르면 이곳에 모입니다.</p>
          </div>
        )}
      </section>
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleString("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  });
}

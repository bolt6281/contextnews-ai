import { Hash, Trash2 } from "lucide-react";
import type { Interest } from "../types";

type InterestListProps = {
  interests: Interest[];
  selectedInterestId: number | null;
  onSelect: (interestId: number | null) => void;
  onDelete: (interest: Interest) => void;
  deletingInterestId: number | null;
};

export function InterestList({ interests, selectedInterestId, onSelect, onDelete, deletingInterestId }: InterestListProps) {
  if (interests.length === 0) {
    return <p className="empty-text">등록된 키워드가 없습니다.</p>;
  }

  return (
    <>
      <button className="interest-all-button" type="button" onClick={() => onSelect(null)}>
        전체 뉴스
      </button>
      <ul className="interest-list">
        {interests.map((interest) => (
          <li key={interest.id}>
            <div className="interest-row">
              <button
                type="button"
                className={selectedInterestId === interest.id ? "interest-item is-active" : "interest-item"}
                onClick={() => onSelect(interest.id)}
              >
                <span className="interest-keyword">
                  <Hash size={16} aria-hidden="true" />
                  <strong>{interest.keyword}</strong>
                </span>
                <span className="interest-range">최근 {interest.lookback_days}일</span>
                <span className="interest-description">{interest.description}</span>
              </button>
              <button
                type="button"
                className="interest-delete-button"
                onClick={() => onDelete(interest)}
                disabled={deletingInterestId === interest.id}
                aria-label={`${interest.keyword} 삭제`}
                title={`${interest.keyword} 삭제`}
              >
                <Trash2 size={16} aria-hidden="true" />
              </button>
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}

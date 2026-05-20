import type { DashboardItem } from "../types";

type NewsCardProps = {
  item: DashboardItem;
  onOpen: (item: DashboardItem) => void;
};

export function NewsCard({ item, onOpen }: NewsCardProps) {
  const publishedAt = new Date(item.published_at).toLocaleString("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short"
  });

  return (
    <article className={item.is_read ? "news-card is-read" : "news-card"}>
      <button className="news-card-button" type="button" onClick={() => onOpen(item)}>
        <div className="news-meta">
          <span>{item.keyword}</span>
          <span>{item.source}</span>
          <time dateTime={item.published_at}>{publishedAt}</time>
          <span className={item.is_read ? "read-chip" : "unread-chip"}>{item.is_read ? "읽음" : "미열람"}</span>
        </div>
        <h3>{item.title}</h3>
        <p className="news-summary">{item.summary}</p>

        {item.bullet_points.length > 0 ? (
          <ul className="bullet-list">
            {item.bullet_points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
        ) : null}

        <div className="news-footer">
          <p>{item.decision_reason}</p>
        </div>
      </button>
    </article>
  );
}

import { useState } from "react";
import { Plus } from "lucide-react";
import { apiRequest } from "../api/client";
import type { InterestCreateResponse } from "../types";

type InterestFormProps = {
  onCreated: () => void;
};

export function InterestForm({ onCreated }: InterestFormProps) {
  const [keyword, setKeyword] = useState("");
  const [description, setDescription] = useState("");
  const [lookbackDays, setLookbackDays] = useState(3);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await apiRequest<InterestCreateResponse>("/api/interests", {
        method: "POST",
        body: { keyword, description, lookback_days: lookbackDays }
      });
      setKeyword("");
      setDescription("");
      setLookbackDays(3);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "키워드 등록에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="interest-form" onSubmit={handleSubmit}>
      <label>
        키워드
        <input
          value={keyword}
          maxLength={30}
          placeholder="예: 엔비디아"
          onChange={(event) => setKeyword(event.target.value)}
          required
        />
      </label>

      <label>
        추가 설명
        <textarea
          value={description}
          minLength={10}
          maxLength={300}
          placeholder="예: 주가와 실적에 영향을 줄 수 있는 반도체, AI 인프라 관련 뉴스"
          onChange={(event) => setDescription(event.target.value)}
          required
        />
      </label>

      <label>
        조회 기간
        <select value={lookbackDays} onChange={(event) => setLookbackDays(Number(event.target.value))}>
          <option value={1}>최근 1일</option>
          <option value={3}>최근 3일</option>
          <option value={7}>최근 7일</option>
          <option value={14}>최근 14일</option>
          <option value={30}>최근 30일</option>
        </select>
      </label>

      {error ? <p className="error-message">{error}</p> : null}

      <button className="primary-button" type="submit" disabled={isSubmitting}>
        <Plus size={18} />
        {isSubmitting ? "등록 중" : "키워드 등록"}
      </button>
    </form>
  );
}

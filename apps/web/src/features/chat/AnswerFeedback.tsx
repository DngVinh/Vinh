import React, { useState } from "react";
import { ThumbsUpIcon, ThumbsDownIcon } from "../../components/Icons";

export type FeedbackRating = "helpful" | "not_helpful";

export interface AnswerFeedbackProps {
  answerId: string;
  onFeedbackSubmit?: (answerId: string, rating: FeedbackRating) => Promise<void> | void;
}

export function AnswerFeedback({ answerId, onFeedbackSubmit }: AnswerFeedbackProps) {
  const [selectedRating, setSelectedRating] = useState<FeedbackRating | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleVote = async (rating: FeedbackRating) => {
    setSelectedRating(rating);
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      if (onFeedbackSubmit) {
        await onFeedbackSubmit(answerId, rating);
      }
      setSubmitted(true);
    } catch {
      setErrorMessage("Không thể gửi đánh giá. Vui lòng thử lại.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div
        aria-live="polite"
        style={{
          fontSize: "13px",
          color: "var(--color-status-success, #15803d)",
          padding: "4px 0",
        }}
      >
        Cảm ơn bạn đã phản hồi!
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "4px",
        marginTop: "8px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          fontSize: "13px",
          color: "var(--color-text-muted, #4b5563)",
        }}
      >
        <span>Câu trả lời có hữu ích không?</span>
        <button
          type="button"
          onClick={() => handleVote("helpful")}
          disabled={isSubmitting}
          aria-label="Hữu ích"
          aria-pressed={selectedRating === "helpful"}
          style={{
            minHeight: "36px",
            padding: "6px 14px",
            fontSize: "13px",
            fontWeight: 500,
            border: `1px solid ${selectedRating === "helpful" ? "#bfdbfe" : "var(--color-slate-200, #e2e8f0)"}`,
            borderRadius: "var(--radius-full, 9999px)",
            backgroundColor: selectedRating === "helpful" ? "var(--color-primary-light, #eff6ff)" : "#ffffff",
            color: selectedRating === "helpful" ? "var(--color-primary, #1e3a8a)" : "var(--color-slate-700, #334155)",
            cursor: isSubmitting ? "not-allowed" : "pointer",
            boxShadow: selectedRating === "helpful" ? "none" : "var(--shadow-xs)",
            transition: "var(--transition-fast, 150ms ease)",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <ThumbsUpIcon size={16} />
          <span>Hữu ích</span>
        </button>
        <button
          type="button"
          onClick={() => handleVote("not_helpful")}
          disabled={isSubmitting}
          aria-label="Chưa hữu ích"
          aria-pressed={selectedRating === "not_helpful"}
          style={{
            minHeight: "36px",
            padding: "6px 14px",
            fontSize: "13px",
            fontWeight: 500,
            border: `1px solid ${selectedRating === "not_helpful" ? "#fecaca" : "var(--color-slate-200, #e2e8f0)"}`,
            borderRadius: "var(--radius-full, 9999px)",
            backgroundColor: selectedRating === "not_helpful" ? "#fef2f2" : "#ffffff",
            color: selectedRating === "not_helpful" ? "#b91c1c" : "var(--color-slate-700, #334155)",
            cursor: isSubmitting ? "not-allowed" : "pointer",
            boxShadow: selectedRating === "not_helpful" ? "none" : "var(--shadow-xs)",
            transition: "var(--transition-fast, 150ms ease)",
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <ThumbsDownIcon size={16} />
          <span>Chưa hữu ích</span>
        </button>
      </div>

      {errorMessage && (
        <div
          role="alert"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontSize: "12px",
            color: "var(--color-status-error, #b91c1c)",
            marginTop: "4px",
          }}
        >
          <span>{errorMessage}</span>
          {selectedRating && (
            <button
              type="button"
              onClick={() => handleVote(selectedRating)}
              style={{
                fontSize: "12px",
                textDecoration: "underline",
                background: "none",
                border: "none",
                color: "var(--color-status-error, #b91c1c)",
                cursor: "pointer",
                padding: "2px 4px",
              }}
            >
              Thử lại
            </button>
          )}
        </div>
      )}
    </div>
  );
}

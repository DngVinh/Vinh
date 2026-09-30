import React, { useState, type FormEvent, type KeyboardEvent } from "react";
import { AnswerFeedback, type FeedbackRating } from "./AnswerFeedback";
import { BotIcon, SparklesIcon, ShieldCheckIcon, AlertTriangleIcon, RefreshCwIcon, ArrowRightIcon } from "../../components/Icons";

export interface ChatCitation {
  id: string;
  index: number;
  title: string;
  page?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  status?: "streaming" | "success" | "failed" | "abstained";
  citations?: ChatCitation[];
}

export interface ChatPanelProps {
  messages?: ChatMessage[];
  isStreaming?: boolean;
  onSendMessage?: (content: string) => void;
  onStopStreaming?: () => void;
  onRetry?: (messageId: string) => void;
  onHandover?: () => void;
  onCitationClick?: (citationId: string) => void;
  onFeedbackSubmit?: (answerId: string, rating: FeedbackRating) => Promise<void> | void;
}

const EMPTY_PROMPTS = [
  "Điều kiện xét học bổng",
  "Thủ tục xin cấp bảng điểm",
  "Quy chế hoãn thi học kỳ",
  "Quy chế chuyển ngành",
];

export function ChatPanel({
  messages = [],
  isStreaming = false,
  onSendMessage,
  onStopStreaming,
  onRetry,
  onHandover,
  onCitationClick,
  onFeedbackSubmit,
}: ChatPanelProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e?: FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    onSendMessage?.(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handlePromptClick = (promptText: string) => {
    if (isStreaming) return;
    onSendMessage?.(promptText);
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "#ffffff",
        borderRadius: "var(--radius-xl, 16px)",
        border: "1px solid var(--color-slate-200, #e2e8f0)",
        boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
        overflow: "hidden",
      }}
    >
      {/* AI Disclosure & Capability Notice Header */}
      <div
        style={{
          padding: "10px 18px",
          backgroundColor: "#f8fafc",
          borderBottom: "1px solid var(--color-slate-200, #e2e8f0)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "10px",
          fontSize: "12px",
          color: "var(--color-slate-600, #475569)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <ShieldCheckIcon size={16} style={{ color: "#065f46" }} />
          <span>
            <strong style={{ color: "var(--color-slate-800, #1e293b)" }}>Trợ lý AI Campus 24/7: </strong>
            HUCE Demo — Môi trường thử nghiệm mô phỏng không chính thức. Luôn đối chiếu văn bản quy chế.
          </span>
        </div>
        {onHandover && (
          <button
            type="button"
            onClick={onHandover}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              padding: "4px 8px",
              borderRadius: "var(--radius-md, 6px)",
              backgroundColor: "#ffffff",
              color: "var(--color-primary, #1e3a8a)",
              border: "1px solid var(--color-slate-200, #e2e8f0)",
              fontSize: "11px",
              fontWeight: 600,
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
          >
            <span>Gặp cán bộ</span>
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div
        role="log"
        aria-label="Lịch sử đối thoại"
        style={{
          flex: 1,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "18px",
          padding: "24px",
          backgroundColor: "var(--color-slate-50, #f8fafc)",
        }}
      >
        {messages.length === 0 && (
          <div
            style={{
              margin: "auto",
              textAlign: "center",
              maxWidth: "480px",
              padding: "36px 16px",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "16px",
            }}
          >
            <div
              style={{
                width: "52px",
                height: "52px",
                borderRadius: "var(--radius-lg, 14px)",
                backgroundColor: "var(--color-primary-light, #eff6ff)",
                color: "var(--color-primary, #1e3a8a)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 2px 8px rgba(30, 58, 138, 0.08)",
              }}
            >
              <BotIcon size={26} />
            </div>

            <div>
              <h3 style={{ margin: "0 0 8px 0", fontSize: "18px", fontWeight: 700, color: "var(--color-slate-900, #0f172a)" }}>
                Trợ lý Học tập Campus 24/7
              </h3>
              <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-600, #475569)", lineHeight: 1.6 }}>
                Đặt câu hỏi về quy chế đào tạo, đăng ký tín chỉ, thủ tục tốt nghiệp hoặc lịch biểu HUCE để nhận câu trả lời có trích dẫn văn bản chính thức.
              </p>
            </div>

            {/* Quick Contextual Prompts */}
            <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "8px", marginTop: "8px" }}>
              {EMPTY_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => handlePromptClick(prompt)}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "6px 14px",
                    borderRadius: "var(--radius-full, 9999px)",
                    backgroundColor: "#ffffff",
                    color: "var(--color-slate-700, #334155)",
                    border: "1px solid var(--color-slate-200, #e2e8f0)",
                    fontSize: "13px",
                    fontWeight: 500,
                    cursor: "pointer",
                    boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
                    transition: "var(--transition-fast, 150ms cubic-bezier(0.4, 0, 0.2, 1))",
                  }}
                >
                  <SparklesIcon size={14} style={{ color: "var(--color-primary, #1e3a8a)" }} />
                  <span>{prompt}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => {
          const isUser = msg.role === "user";
          const isSystem = msg.role === "system";
          const isFailed = msg.status === "failed";
          const isAbstained = msg.status === "abstained";

          if (isSystem) {
            return (
              <div
                key={msg.id}
                role="status"
                style={{
                  alignSelf: "center",
                  maxWidth: "90%",
                  padding: "8px 16px",
                  borderRadius: "8px",
                  backgroundColor: "#fee2e2",
                  color: "#991b1b",
                  fontSize: "12px",
                  fontWeight: 500,
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <AlertTriangleIcon size={16} />
                <span>{msg.content}</span>
              </div>
            );
          }

          return (
            <article
              key={msg.id}
              role="article"
              aria-label={`${isUser ? "Tin nhắn của bạn" : "Tin nhắn của trợ lý"}: ${msg.content.slice(0, 30)}...`}
              style={{
                display: "flex",
                flexDirection: "column",
                alignSelf: isUser ? "flex-end" : "flex-start",
                maxWidth: "85%",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  marginBottom: "6px",
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "var(--color-slate-600, #475569)",
                  alignSelf: isUser ? "flex-end" : "flex-start",
                }}
              >
                <span>{isUser ? "Bạn" : "Trợ lý AI"}</span>
                {msg.timestamp && <span>• {msg.timestamp}</span>}
              </div>

              <div
                style={{
                  backgroundColor: isUser
                    ? "var(--color-primary, #1e3a8a)"
                    : isFailed
                    ? "#fff1f2"
                    : "#ffffff",
                  color: isUser
                    ? "#ffffff"
                    : isFailed
                    ? "#9f1239"
                    : "var(--color-slate-900, #0f172a)",
                  padding: "14px 18px",
                  borderRadius: isUser ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                  boxShadow: isUser
                    ? "0 4px 12px rgba(30, 58, 138, 0.16)"
                    : "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04))",
                  border: isUser
                    ? "none"
                    : isFailed
                    ? "1px solid #fecdd3"
                    : "1px solid var(--color-slate-200, #e2e8f0)",
                  wordBreak: "break-word",
                  fontSize: "14px",
                  lineHeight: 1.6,
                }}
              >
                <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{msg.content}</p>

                {/* Citations Preview if present */}
                {msg.citations && msg.citations.length > 0 && (
                  <div style={{ marginTop: "10px", display: "flex", flexWrap: "wrap", gap: "6px" }}>
                    {msg.citations.map((cite) => (
                      <button
                        key={cite.id}
                        type="button"
                        onClick={() => onCitationClick?.(cite.id)}
                        aria-label={`Xem nguồn trích dẫn [${cite.index}]: ${cite.title}`}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "4px",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          backgroundColor: "#eff6ff",
                          color: "#1d4ed8",
                          border: "1px solid #bfdbfe",
                          fontSize: "11px",
                          fontWeight: 600,
                          cursor: "pointer",
                        }}
                      >
                        <span>[{cite.index}]</span>
                        <span>{cite.title}</span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Agentic Action Suggestions for Assistant */}
                {!isUser && !isFailed && !isAbstained && (() => {
                  const contentLower = msg.content.toLowerCase();
                  const isProcedural = contentLower.includes("bảng điểm") || contentLower.includes("thủ tục") || contentLower.includes("học bổng") || contentLower.includes("hoãn thi") || contentLower.includes("một cửa") || contentLower.includes("giấy tờ") || contentLower.includes("đơn");
                  const isSchedule = contentLower.includes("lịch thi") || contentLower.includes("thời khóa biểu") || contentLower.includes("ca thi") || contentLower.includes("tiết");
                  const isRoom = contentLower.includes("phòng") || contentLower.includes("mượn") || contentLower.includes("tự học");

                  if (!isProcedural && !isSchedule && !isRoom) return null;

                  return (
                    <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px solid #f1f5f9", display: "flex", flexDirection: "column", gap: "6px" }}>
                      <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--color-slate-500, #64748b)", textTransform: "uppercase" }}>
                        ⚡ Gợi ý hành động:
                      </span>
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                        {isProcedural && (
                          <a
                            href="/tickets"
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              padding: "4px 10px",
                              borderRadius: "6px",
                              backgroundColor: "#f0fdf4",
                              color: "#166534",
                              border: "1px solid #bbf7d0",
                              fontSize: "12px",
                              fontWeight: 600,
                              textDecoration: "none",
                            }}
                          >
                            <span>📝</span> Nộp hồ sơ Một cửa trực tuyến
                          </a>
                        )}
                        {isSchedule && (
                          <a
                            href="/schedule"
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              padding: "4px 10px",
                              borderRadius: "6px",
                              backgroundColor: "#eff6ff",
                              color: "#1e40af",
                              border: "1px solid #bfdbfe",
                              fontSize: "12px",
                              fontWeight: 600,
                              textDecoration: "none",
                            }}
                          >
                            <span>📅</span> Xem thời khóa biểu & lịch thi
                          </a>
                        )}
                        {isRoom && (
                          <a
                            href="/rooms"
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "4px",
                              padding: "4px 10px",
                              borderRadius: "6px",
                              backgroundColor: "#faf5ff",
                              color: "#6b21a8",
                              border: "1px solid #e9d5ff",
                              fontSize: "12px",
                              fontWeight: 600,
                              textDecoration: "none",
                            }}
                          >
                            <span>🏢</span> Đăng ký mượn phòng học
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* Recovery: Retry Button on Failed Message */}
              {isFailed && onRetry && (
                <div style={{ marginTop: "8px", display: "flex", alignItems: "center", gap: "8px" }}>
                  <button
                    type="button"
                    onClick={() => onRetry(msg.id)}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "6px 12px",
                      borderRadius: "6px",
                      backgroundColor: "#fee2e2",
                      color: "#991b1b",
                      border: "1px solid #fecdd3",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    <RefreshCwIcon size={14} />
                    <span>Thử lại</span>
                  </button>
                  <span style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)" }}>
                    Lỗi kết nối máy chủ AI
                  </span>
                </div>
              )}

              {/* Recovery: Handover Button on Abstained Message */}
              {isAbstained && onHandover && (
                <div style={{ marginTop: "8px", display: "flex", alignItems: "center", gap: "8px" }}>
                  <button
                    type="button"
                    onClick={onHandover}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "6px",
                      padding: "6px 14px",
                      borderRadius: "6px",
                      backgroundColor: "var(--color-primary-light, #eff6ff)",
                      color: "var(--color-primary, #1e3a8a)",
                      border: "1px solid var(--color-primary-border, #bfdbfe)",
                      fontSize: "12px",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    <span>Chuyển cán bộ</span>
                    <ArrowRightIcon size={14} />
                  </button>
                  <span style={{ fontSize: "12px", color: "var(--color-slate-500, #64748b)" }}>
                    Chuyển tiếp câu hỏi tới một cửa số
                  </span>
                </div>
              )}

              {!isUser && !isFailed && !isAbstained && (
                <div style={{ marginTop: "6px" }}>
                  <AnswerFeedback
                    answerId={msg.id}
                    onFeedbackSubmit={onFeedbackSubmit}
                  />
                </div>
              )}
            </article>
          );
        })}

        {isStreaming && (
          <div
            aria-live="polite"
            style={{
              alignSelf: "flex-start",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              padding: "10px 18px",
              backgroundColor: "#ffffff",
              borderRadius: "16px 16px 16px 4px",
              border: "1px solid var(--color-primary-border, #bfdbfe)",
              fontSize: "13px",
              fontWeight: 500,
              color: "var(--color-slate-700, #334155)",
              boxShadow: "var(--shadow-xs, 0 1px 2px rgba(0,0,0,0.05))",
            }}
          >
            <span
              style={{
                display: "inline-block",
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: "var(--color-primary, #1e3a8a)",
                boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.2)",
              }}
            />
            <span>Trợ lý đang trả lời...</span>
          </div>
        )}
      </div>

      {/* Composer Form */}
      <form
        onSubmit={handleSubmit}
        style={{
          padding: "16px 20px",
          backgroundColor: "#ffffff",
          borderTop: "1px solid var(--color-slate-200, #e2e8f0)",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <label htmlFor="chat-input" style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-slate-800, #1e293b)" }}>
            Đặt câu hỏi
          </label>
          <span style={{ fontSize: "12px", color: "var(--color-slate-600, #475569)" }}>
            Enter để gửi • Shift+Enter để xuống dòng
          </span>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "flex-end" }}>
          <textarea
            id="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            aria-label="Đặt câu hỏi"
            placeholder="Nhập câu hỏi cần giải đáp (ví dụ: Quy chế chuyển ngành, số tín chỉ tối đa một kỳ)..."
            rows={2}
            style={{
              flex: 1,
              padding: "10px 14px",
              borderRadius: "var(--radius-md, 8px)",
              border: "1.5px solid var(--color-slate-300, #cbd5e1)",
              resize: "none",
              fontFamily: "inherit",
              fontSize: "14px",
              lineHeight: 1.5,
              color: "var(--color-slate-900, #0f172a)",
              boxShadow: "inset 0 1px 2px rgba(0,0,0,0.03)",
              outline: "none",
            }}
          />

          {isStreaming ? (
            <button
              type="button"
              onClick={onStopStreaming}
              style={{
                height: "44px",
                padding: "0 18px",
                backgroundColor: "#fee2e2",
                color: "#991b1b",
                border: "1px solid #fecdd3",
                borderRadius: "var(--radius-md, 8px)",
                fontWeight: 600,
                fontSize: "13px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
              }}
            >
              <span>Dừng trả lời</span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              style={{
                height: "44px",
                padding: "0 20px",
                backgroundColor: "var(--color-primary, #1e3a8a)",
                color: "#ffffff",
                border: "none",
                borderRadius: "var(--radius-md, 8px)",
                fontWeight: 600,
                fontSize: "14px",
                cursor: !input.trim() ? "not-allowed" : "pointer",
                opacity: !input.trim() ? 0.5 : 1,
                boxShadow: !input.trim() ? "none" : "var(--shadow-sm)",
                transition: "var(--transition-fast, 150ms ease)",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span>Gửi</span>
              <SparklesIcon size={16} />
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

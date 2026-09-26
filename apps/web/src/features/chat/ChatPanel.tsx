import React, { useState, type FormEvent, type KeyboardEvent } from "react";
import { AnswerFeedback, type FeedbackRating } from "./AnswerFeedback";
import { BotIcon, SparklesIcon } from "../../components/Icons";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export interface ChatPanelProps {
  messages?: ChatMessage[];
  isStreaming?: boolean;
  onSendMessage?: (content: string) => void;
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
  onFeedbackSubmit,
}: ChatPanelProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e?: FormEvent) => {
    if (e) e.preventDefault();
    const textarea = document.getElementById("chat-input") as HTMLTextAreaElement | null;
    const trimmed = (input || textarea?.value || "").trim();
    if (!trimmed || isStreaming) return;
    onSendMessage?.(trimmed);
    setInput("");
    if (textarea) textarea.value = "";
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
        borderRadius: "var(--radius-xl, 20px)",
        border: "1px solid var(--color-slate-200, #e2e8f0)",
        boxShadow: "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
        overflow: "hidden",
      }}
    >
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

            {/* Information Foraging Quick Prompt Chips */}
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
          return (
            <article
              key={msg.id}
              role="article"
              aria-label={`${isUser ? "Tin nhắn của bạn" : "Tin nhắn của trợ lý"}: ${msg.content.slice(0, 30)}...`}
              style={{
                display: "flex",
                flexDirection: "column",
                alignSelf: isUser ? "flex-end" : "flex-start",
                maxWidth: "80%",
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
                <span>{isUser ? "Bạn" : "Trợ lý Campus AI"}</span>
                {msg.timestamp && <span>• {msg.timestamp}</span>}
              </div>

              <div
                style={{
                  backgroundColor: isUser ? "var(--color-primary, #1e3a8a)" : "#ffffff",
                  color: isUser ? "#ffffff" : "var(--color-slate-900, #0f172a)",
                  padding: "14px 20px",
                  borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                  boxShadow: isUser
                    ? "0 4px 14px rgba(30, 58, 138, 0.18)"
                    : "var(--shadow-ambient, 0 1px 3px rgba(15,23,42,0.04), 0 8px 24px -4px rgba(15,23,42,0.06))",
                  border: isUser ? "none" : "1px solid var(--color-slate-200, #e2e8f0)",
                  wordBreak: "break-word",
                  fontSize: "14px",
                  lineHeight: 1.6,
                }}
              >
                <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{msg.content}</p>
              </div>

              {!isUser && (
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
              borderRadius: "18px 18px 18px 4px",
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
          padding: "18px 24px",
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

        <div style={{ display: "flex", gap: "12px", alignItems: "flex-end" }}>
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
              padding: "12px 16px",
              borderRadius: "var(--radius-md, 10px)",
              border: "1.5px solid var(--color-slate-300, #cbd5e1)",
              resize: "none",
              fontFamily: "inherit",
              fontSize: "14px",
              lineHeight: 1.5,
              color: "var(--color-slate-900, #0f172a)",
              boxShadow: "inset 0 1px 2px rgba(0,0,0,0.03)",
            }}
          />

          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            style={{
              height: "48px",
              padding: "0 24px",
              backgroundColor: "var(--color-primary, #1e3a8a)",
              color: "#ffffff",
              border: "none",
              borderRadius: "var(--radius-md, 10px)",
              fontWeight: 600,
              fontSize: "14px",
              cursor: !input.trim() || isStreaming ? "not-allowed" : "pointer",
              opacity: !input.trim() || isStreaming ? 0.5 : 1,
              boxShadow: !input.trim() || isStreaming ? "none" : "var(--shadow-sm)",
              transition: "var(--transition-fast, 150ms ease)",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>Gửi</span>
            <SparklesIcon size={16} />
          </button>
        </div>
      </form>
    </div>
  );
}

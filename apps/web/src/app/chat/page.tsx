"use client";

import React, { useState, useCallback, useRef } from "react";
import { AppShell } from "../../components/AppShell";
import { ChatPanel, type ChatMessage } from "../../features/chat/ChatPanel";
import { CitationDrawer, type CitationItem } from "../../features/chat/CitationDrawer";
import { AsyncState, type AsyncStatus } from "../../components/AsyncState";
import { FileTextIcon } from "../../components/Icons";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const DEFAULT_DEMO_TOKEN = "eyJleHAiOiAxODIxNjg1NzI0LCAiaWF0IjogMTc5MDE0OTcyNCwgInN1YiI6ICI0YjQxOWExYi02ZDQxLTdkZmItODk0My0yZWRkOWYwNzEzODUifQ==.4LsklT3l1DyqPFznuTJJFAfcieGPSkzZBxRL0aOkqS0=";
const API_TOKEN = process.env.NEXT_PUBLIC_API_TOKEN || DEFAULT_DEMO_TOKEN;

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [citations, setCitations] = useState<CitationItem[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [status, setStatus] = useState<AsyncStatus>("success");
  const [errorMessage, setErrorMessage] = useState<string>("");

  // Persistent conversation ID for the active session
  const conversationIdRef = useRef<string | null>(null);

  const handleSendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isStreaming) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsStreaming(true);
    setStatus("success");
    setErrorMessage("");

    const assistantMsgId = `assistant-${Date.now()}`;
    let accumulatedText = "";

    try {
      // 1. Ensure active conversation session exists
      let convId = conversationIdRef.current;
      if (!convId) {
        const convRes = await fetch(`${API_BASE_URL}/v1/conversations`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${API_TOKEN}`,
          },
          body: JSON.stringify({}),
        });

        if (!convRes.ok) {
          throw new Error(`Không thể khởi tạo phiên trò chuyện (Mã lỗi ${convRes.status})`);
        }

        const convData = await convRes.json();
        convId = convData.id;
        conversationIdRef.current = convId;
      }

      // 2. Stream message from backend
      const response = await fetch(
        `${API_BASE_URL}/v1/conversations/${convId}/messages:stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${API_TOKEN}`,
          },
          body: JSON.stringify({ content }),
        }
      );

      if (!response.ok) {
        throw new Error(`Máy chủ phản hồi lỗi: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Không nhận được luồng dữ liệu từ máy chủ");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data:")) {
            const dataStr = trimmed.replace(/^data:\s*/, "");
            if (!dataStr) continue;
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.delta) {
                accumulatedText += parsed.delta;
                setMessages((prev) => {
                  const withoutCurrent = prev.filter((m) => m.id !== assistantMsgId);
                  return [
                    ...withoutCurrent,
                    {
                      id: assistantMsgId,
                      role: "assistant",
                      content: accumulatedText,
                      timestamp: new Date().toLocaleTimeString("vi-VN", {
                        hour: "2-digit",
                        minute: "2-digit",
                      }),
                    },
                  ];
                });
              }
              if (parsed.citations && Array.isArray(parsed.citations)) {
                setCitations(
                  parsed.citations.map((rawCitation: Record<string, unknown>, idx: number) => ({
                    id: (rawCitation.id as string) || `cit-${idx}`,
                    title: (rawCitation.title as string) || (rawCitation.document_title as string) || `Tài liệu tham khảo #${idx + 1}`,
                    documentRef: (rawCitation.document_ref as string) || (rawCitation.section as string) || (rawCitation.section_title as string) || `VB-${idx + 1}`,
                    quote: (rawCitation.quote as string) || (rawCitation.snippet as string) || (rawCitation.text as string) || "",
                    confidence: typeof rawCitation.confidence === "number" ? rawCitation.confidence : 0.95,
                  }))
                );
              }
            } catch {
              // Non-JSON delta stream payload
            }
          }
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Đã xảy ra sự cố khi kết nối máy chủ.";
      setStatus("error");
      setErrorMessage(msg);
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-error-${Date.now()}`,
          role: "assistant",
          content: `${msg}. Vui lòng kiểm tra lại dịch vụ hệ thống.`,
          timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  }, [isStreaming]);

  return (
    <AppShell activeNav="chat">
      <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 140px)", position: "relative" }}>
        <header style={{ marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h1 style={{ fontSize: "22px", fontWeight: 800, margin: "0 0 4px 0", color: "var(--color-slate-900, #0f172a)" }}>
              Tư vấn trực tuyến Campus 24/7
            </h1>
            <p style={{ margin: 0, fontSize: "14px", color: "var(--color-slate-500, #64748b)" }}>
              Hỏi đáp quy chế đào tạo, thủ tục hành chính và lịch biểu HUCE
            </p>
          </div>
          {citations.length > 0 && (
            <button
              type="button"
              onClick={() => setIsDrawerOpen(true)}
              style={{
                padding: "8px 16px",
                borderRadius: "var(--radius-md, 8px)",
                border: "1px solid var(--color-slate-200, #e2e8f0)",
                backgroundColor: "#ffffff",
                color: "var(--color-primary, #1e3a8a)",
                fontSize: "13px",
                fontWeight: 600,
                cursor: "pointer",
                boxShadow: "var(--shadow-xs)",
                display: "flex",
                alignItems: "center",
                gap: "8px",
                minHeight: "44px",
                transition: "var(--transition-fast, 150ms ease)",
              }}
            >
              <FileTextIcon size={16} />
              <span>Nguồn trích dẫn</span>
              <span
                style={{
                  backgroundColor: "var(--color-primary-light, #eff6ff)",
                  color: "var(--color-primary, #1e3a8a)",
                  borderRadius: "9999px",
                  padding: "2px 8px",
                  fontSize: "12px",
                  fontWeight: 700,
                }}
              >
                {citations.length}
              </span>
            </button>
          )}
        </header>

        {status === "error" && (
          <div style={{ marginBottom: "16px" }}>
            <AsyncState
              status="error"
              errorMessage={errorMessage || "Không thể kết nối đến dịch vụ trò chuyện"}
              onRetry={() => setStatus("success")}
            />
          </div>
        )}

        <div style={{ flex: 1, minHeight: 0 }}>
          <ChatPanel
            messages={messages}
            isStreaming={isStreaming}
            onSendMessage={handleSendMessage}
          />
        </div>

        <CitationDrawer
          isOpen={isDrawerOpen}
          citations={citations}
          onClose={() => setIsDrawerOpen(false)}
        />
      </div>
    </AppShell>
  );
}

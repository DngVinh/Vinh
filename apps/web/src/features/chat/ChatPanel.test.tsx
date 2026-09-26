import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { ChatPanel } from "./ChatPanel";

describe("ChatPanel Component (TASK-WEB-CHAT-001)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders composer, sends message and announces streaming state", () => {
    const handleSend = vi.fn();
    render(<ChatPanel onSendMessage={handleSend} />);

    const input = screen.getByLabelText(/Đặt câu hỏi/i);
    const sendBtn = screen.getByRole("button", { name: /Gửi/i });

    expect(input).toBeDefined();
    expect(sendBtn).toBeDefined();

    fireEvent.change(input, { target: { value: "Học phí kỳ 1 nộp khi nào?" } });
    fireEvent.click(sendBtn);

    expect(handleSend).toHaveBeenCalledWith("Học phí kỳ 1 nộp khi nào?");
  });

  it("displays conversation history and streaming indicator", () => {
    const messages = [
      { id: "1", role: "user" as const, content: "Lịch thi lại môn Kết cấu thép?" },
      { id: "2", role: "assistant" as const, content: "Lịch thi dự kiến vào tuần 18." },
    ];

    render(<ChatPanel messages={messages} isStreaming={true} />);

    expect(screen.getByText("Lịch thi lại môn Kết cấu thép?")).toBeDefined();
    expect(screen.getByText("Lịch thi dự kiến vào tuần 18.")).toBeDefined();

    // Streaming indicator in polite live region
    const streamingStatus = screen.getByText(/Trợ lý đang trả lời.../i);
    expect(streamingStatus).toBeDefined();
    expect(streamingStatus.closest("[aria-live='polite']")).not.toBeNull();
  });

  it("negative path: prevents sending empty or whitespace-only messages", () => {
    const handleSend = vi.fn();
    render(<ChatPanel onSendMessage={handleSend} />);

    const input = screen.getByLabelText(/Đặt câu hỏi/i);
    const sendBtn = screen.getByRole("button", { name: /Gửi/i });

    fireEvent.change(input, { target: { value: "    " } });
    fireEvent.click(sendBtn);

    expect(handleSend).not.toHaveBeenCalled();
  });

  it("renders empty state with academic quick prompt suggestions", () => {
    const handleSend = vi.fn();
    render(<ChatPanel messages={[]} onSendMessage={handleSend} />);

    expect(screen.getByText(/Trợ lý Học tập Campus 24\/7/i)).toBeDefined();
    const promptChip = screen.getByRole("button", { name: /Điều kiện xét học bổng/i });
    expect(promptChip).toBeDefined();

    fireEvent.click(promptChip);
    expect(handleSend).toHaveBeenCalledWith("Điều kiện xét học bổng");
  });
});

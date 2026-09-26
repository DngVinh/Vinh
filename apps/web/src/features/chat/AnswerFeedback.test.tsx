import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { AnswerFeedback } from "./AnswerFeedback";

describe("AnswerFeedback Component (TASK-WEB-CHAT-002)", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders helpful and not-helpful buttons bound to immutable answerId", async () => {
    const handleFeedback = vi.fn().mockResolvedValue(undefined);
    render(
      <AnswerFeedback
        answerId="ans-0199c9ac-4d7c"
        onFeedbackSubmit={handleFeedback}
      />
    );

    const helpfulBtn = screen.getByRole("button", { name: "Hữu ích" });
    const notHelpfulBtn = screen.getByRole("button", { name: "Chưa hữu ích" });

    expect(helpfulBtn).toBeDefined();
    expect(notHelpfulBtn).toBeDefined();

    fireEvent.click(helpfulBtn);

    expect(handleFeedback).toHaveBeenCalledWith("ans-0199c9ac-4d7c", "helpful");
    await screen.findByText(/Cảm ơn bạn đã phản hồi!/i);
  });

  it("handles retryable error state accessibly", async () => {
    const handleFeedback = vi.fn().mockRejectedValue(new Error("Lỗi mạng"));
    render(
      <AnswerFeedback
        answerId="ans-0199c9ac-4d7c"
        onFeedbackSubmit={handleFeedback}
      />
    );

    const helpfulBtn = screen.getByRole("button", { name: "Hữu ích" });
    fireEvent.click(helpfulBtn);

    const errorAlert = await screen.findByRole("alert");
    expect(errorAlert).toBeDefined();
    expect(screen.getByText(/Không thể gửi đánh giá/i)).toBeDefined();

    const retryBtn = screen.getByRole("button", { name: "Thử lại" });
    expect(retryBtn).toBeDefined();
  });

  it("displays success confirmation after successful submission", async () => {
    const handleFeedback = vi.fn().mockResolvedValue(undefined);
    render(
      <AnswerFeedback
        answerId="ans-0199c9ac-4d7c"
        onFeedbackSubmit={handleFeedback}
      />
    );

    const notHelpfulBtn = screen.getByRole("button", { name: "Chưa hữu ích" });
    fireEvent.click(notHelpfulBtn);

    const successMsg = await screen.findByText(/Cảm ơn bạn đã phản hồi!/i);
    expect(successMsg).toBeDefined();
  });
});

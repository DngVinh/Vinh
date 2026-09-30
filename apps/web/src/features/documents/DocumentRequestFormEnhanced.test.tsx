import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { DocumentRequestForm } from "./DocumentRequestForm";

describe("DocumentRequestForm Enhanced AI & Attachments", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("suggests AI category when user types relevant keyword in reason", () => {
    render(<DocumentRequestForm />);

    const reasonInput = screen.getByLabelText(/Mục đích xin cấp/i);
    fireEvent.change(reasonInput, {
      target: { value: "Em cần nộp hồ sơ xin thực tập tại công ty xây dựng" },
    });

    // AI suggestion banner should appear
    expect(screen.getByText(/Gợi ý AI phân loại/i)).toBeDefined();
    expect(screen.getAllByText(/Giấy giới thiệu thực tập/i).length).toBeGreaterThanOrEqual(2);

    // Click apply suggestion button
    const applyBtn = screen.getByRole("button", { name: /Áp dụng gợi ý/i });
    fireEvent.click(applyBtn);

    const docTypeSelect = screen.getByLabelText(/Loại giấy tờ/i) as HTMLSelectElement;
    expect(docTypeSelect.value).toBe("gioi_thieu_thuc_tap");
  });

  it("displays document preparation guidance for selected document type", () => {
    render(<DocumentRequestForm />);

    const docTypeSelect = screen.getByLabelText(/Loại giấy tờ/i);
    fireEvent.change(docTypeSelect, { target: { value: "hoan_nghia_vu_quan_su" } });

    // Guidance text for military deferral document
    expect(screen.getByText(/Hồ sơ & giấy tờ cần chuẩn bị/i)).toBeDefined();
    expect(screen.getByText(/Lệnh gọi khám tuyển hoặc giấy báo nhập ngũ/i)).toBeDefined();
  });

  it("supports adding and removing file attachments and exposes file name in preview", () => {
    const handleSubmit = vi.fn();
    render(<DocumentRequestForm onSubmit={handleSubmit} />);

    // Fill reason
    fireEvent.change(screen.getByLabelText(/Mục đích xin cấp/i), {
      target: { value: "Bổ sung hồ sơ học bổng" },
    });

    // Simulate file input
    const fileInput = screen.getByLabelText(/Tệp minh chứng đính kèm/i);
    const fakeFile = new File(["dummy content"], "giay_to_minh_chung.pdf", { type: "application/pdf" });

    fireEvent.change(fileInput, { target: { files: [fakeFile] } });

    // Check attached file appears
    expect(screen.getByText("giay_to_minh_chung.pdf")).toBeDefined();

    // Proceed to preview
    fireEvent.click(screen.getByRole("button", { name: /Xem trước yêu cầu/i }));

    // Preview should display attached document
    expect(screen.getByText(/Tệp đính kèm/i)).toBeDefined();
    expect(screen.getByText("giay_to_minh_chung.pdf")).toBeDefined();

    // Confirm submit passes attachedFiles
    fireEvent.click(screen.getByRole("button", { name: /Gửi yêu cầu/i }));
    expect(handleSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        reason: "Bổ sung hồ sơ học bổng",
        attachedFiles: ["giay_to_minh_chung.pdf"],
      })
    );
  });

  it("renders transparency intake checklist in preview mode to guide student compliance", () => {
    render(<DocumentRequestForm />);

    fireEvent.change(screen.getByLabelText(/Mục đích xin cấp/i), {
      target: { value: "Xin cấp bảng điểm phục vụ xét học bổng khuyến khích" },
    });

    fireEvent.click(screen.getByRole("button", { name: /Xem trước yêu cầu/i }));

    // Transparency checklist should be visible in preview
    expect(screen.getByText(/Tiêu chuẩn thẩm định của Cán bộ Một cửa/i)).toBeDefined();
    expect(screen.getByText(/Xác minh danh tính & MSSV/i)).toBeDefined();
    expect(screen.getByText(/Cam kết SLA tiếp nhận/i)).toBeDefined();
  });
});


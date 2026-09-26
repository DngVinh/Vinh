import re

with open("apps/web/src/components/AsyncState.tsx", "r", encoding="utf-8") as f:
    content = f.read()

new_type = """export type AsyncStatus = "loading" | "empty" | "zero-result" | "error" | "offline" | "stale" | "degraded" | "unauthorized" | "result-unknown" | "success";"""

content = re.sub(r"export type AsyncStatus = .*?;", new_type, content)

new_blocks = """
  if (status === "zero-result") {
    return (
      <div aria-live="polite" style={{ padding: "48px 24px", textAlign: "center", backgroundColor: "#ffffff", borderRadius: "14px", border: "1px dashed #cbd5e1" }}>
        <p style={{ margin: 0, fontSize: "14px", color: "#475569", fontWeight: 600 }}>
          Không tìm thấy kết quả
        </p>
      </div>
    );
  }

  if (status === "stale") {
    return (
      <div aria-live="polite" style={{ padding: "16px", backgroundColor: "#fffbeb", border: "1px solid #fde68a", color: "#b45309", borderRadius: "8px", marginBottom: "16px" }}>
        <p style={{ margin: 0, fontSize: "14px", fontWeight: 500 }}>
          Dữ liệu có thể chưa được cập nhật. {onRetry && <button onClick={onRetry} style={{ background: "none", border: "none", color: "#92400e", textDecoration: "underline", cursor: "pointer", padding: 0 }}>Làm mới</button>}
        </p>
      </div>
    );
  }

  if (status === "degraded") {
    return (
      <div aria-live="polite" style={{ padding: "16px", backgroundColor: "#fef3c7", border: "1px solid #fcd34d", color: "#b45309", borderRadius: "8px", marginBottom: "16px" }}>
        <p style={{ margin: 0, fontSize: "14px", fontWeight: 500 }}>
          Hệ thống đang phản hồi chậm. Một số tính năng có thể bị gián đoạn.
        </p>
      </div>
    );
  }

  if (status === "unauthorized") {
    return (
      <div role="alert" aria-live="assertive" style={{ padding: "24px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", borderRadius: "14px", textAlign: "center" }}>
        <p style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>Bạn không có quyền truy cập chức năng này</p>
      </div>
    );
  }

  if (status === "result-unknown") {
    return (
      <div role="alert" aria-live="assertive" style={{ padding: "24px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", borderRadius: "14px", textAlign: "center" }}>
        <p style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>Trạng thái xử lý không rõ ràng</p>
        <p style={{ margin: "8px 0 0", fontSize: "13px" }}>Vui lòng kiểm tra lại sau hoặc liên hệ hỗ trợ.</p>
        {onRetry && <button onClick={onRetry} style={{ marginTop: "12px", padding: "8px 16px", background: "#ffffff", border: "1px solid #ef4444", borderRadius: "6px", cursor: "pointer", color: "#b91c1c" }}>Kiểm tra lại</button>}
      </div>
    );
  }
"""

if "zero-result" not in content:
    content = content.replace("  if (status === \"empty\") {", new_blocks + "\n  if (status === \"empty\") {")

# Fix encoding
content = content.replace("?ang ti d_ liu...", "Đang tải dữ liệu...")
content = content.replace("KhA''ng cA3 d_ liu", "Không có dữ liệu")
content = content.replace("?A xAy ra l-i khi ti d_ liu", "Đã xảy ra lỗi khi tải dữ liệu")
content = content.replace("Mt kt n`i mng", "Mất kết nối mạng")
content = content.replace("Vui lAng kim tra li `?ng truyn internet c a bn.", "Vui lòng kiểm tra lại đường truyền internet của bạn.")
content = content.replace("Th- li", "Thử lại")

with open("apps/web/src/components/AsyncState.tsx", "w", encoding="utf-8") as f:
    f.write(content)

with open("apps/web/src/components/AsyncState.test.tsx", "r", encoding="utf-8") as f:
    test_content = f.read()

if "cleanup" not in test_content:
    test_content = test_content.replace("import { render, screen, fireEvent } from \"@testing-library/react\";", "import { render, screen, fireEvent, cleanup } from \"@testing-library/react\";\nimport { afterEach } from \"vitest\";")
    test_content = test_content.replace("describe(\"AsyncState Component (TASK-WEB-STATE-001)\", () => {", "describe(\"AsyncState Component (TASK-WEB-STATE-001)\", () => {\n  afterEach(() => cleanup());")

new_tests = """
  it("renders zero-result state", () => {
    render(<AsyncState status="zero-result" />);
    expect(screen.getByText("Không tìm thấy kết quả")).toBeDefined();
  });
  
  it("renders stale state", () => {
    render(<AsyncState status="stale" />);
    expect(screen.getByText(/Dữ liệu có thể chưa được cập nhật/i)).toBeDefined();
  });

  it("renders degraded state", () => {
    render(<AsyncState status="degraded" />);
    expect(screen.getByText(/Hệ thống đang phản hồi chậm/i)).toBeDefined();
  });

  it("renders unauthorized state", () => {
    render(<AsyncState status="unauthorized" />);
    expect(screen.getByText(/Bạn không có quyền truy cập/i)).toBeDefined();
  });

  it("renders result-unknown state", () => {
    render(<AsyncState status="result-unknown" />);
    expect(screen.getByText(/Trạng thái xử lý không rõ ràng/i)).toBeDefined();
  });
"""

if "renders zero-result state" not in test_content:
    test_content = test_content.replace("  it(\"negative path: renders fallback error when error status has no message\", () => {", new_tests + "\n  it(\"negative path: renders fallback error when error status has no message\", () => {")

# Fix encoding
test_content = test_content.replace("?ang ti d_ liu...", "Đang tải dữ liệu...")
test_content = test_content.replace("KhA''ng cA3 d_ liu hin th<", "Không có dữ liệu hiển thị")
test_content = test_content.replace("KhA''ng th kt n`i mA y ch ", "Không thể kết nối máy chủ")
test_content = test_content.replace("Th- li", "Thử lại")
test_content = test_content.replace("Mt kt n`i mng", "Mất kết nối mạng")
test_content = test_content.replace("NTi dung thAnh cA''ng", "Nội dung thành công")
test_content = test_content.replace("?A xAy ra l-i", "Đã xảy ra lỗi")

with open("apps/web/src/components/AsyncState.test.tsx", "w", encoding="utf-8") as f:
    f.write(test_content)

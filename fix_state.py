
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
          Không tìm th?y k?t qu?
        </p>
      </div>
    );
  }

  if (status === "stale") {
    return (
      <div aria-live="polite" style={{ padding: "16px", backgroundColor: "#fffbeb", border: "1px solid #fde68a", color: "#b45309", borderRadius: "8px", marginBottom: "16px" }}>
        <p style={{ margin: 0, fontSize: "14px", fontWeight: 500 }}>
          D? li?u có th? chua du?c c?p nh?t. {onRetry && <button onClick={onRetry} style={{ background: "none", border: "none", color: "#92400e", textDecoration: "underline", cursor: "pointer", padding: 0 }}>Làm m?i</button>}
        </p>
      </div>
    );
  }

  if (status === "degraded") {
    return (
      <div aria-live="polite" style={{ padding: "16px", backgroundColor: "#fef3c7", border: "1px solid #fcd34d", color: "#b45309", borderRadius: "8px", marginBottom: "16px" }}>
        <p style={{ margin: 0, fontSize: "14px", fontWeight: 500 }}>
          H? th?ng dang ph?n h?i ch?m. M?t s? tính nang có th? b? gián do?n.
        </p>
      </div>
    );
  }

  if (status === "unauthorized") {
    return (
      <div role="alert" aria-live="assertive" style={{ padding: "24px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", borderRadius: "14px", textAlign: "center" }}>
        <p style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>B?n không có quy?n truy c?p ch?c nang này</p>
      </div>
    );
  }

  if (status === "result-unknown") {
    return (
      <div role="alert" aria-live="assertive" style={{ padding: "24px", backgroundColor: "#fef2f2", border: "1px solid #fecaca", color: "#991b1b", borderRadius: "14px", textAlign: "center" }}>
        <p style={{ margin: 0, fontSize: "15px", fontWeight: 700 }}>Tr?ng thái x? lý không rõ ràng</p>
        <p style={{ margin: "8px 0 0", fontSize: "13px" }}>Vui lòng ki?m tra l?i sau ho?c liên h? h? tr?.</p>
        {onRetry && <button onClick={onRetry} style={{ marginTop: "12px", padding: "8px 16px", background: "#ffffff", border: "1px solid #ef4444", borderRadius: "6px", cursor: "pointer", color: "#b91c1c" }}>Ki?m tra l?i</button>}
      </div>
    );
  }
"""

content = content.replace("  if (status === \"empty\") {", new_blocks + "\n  if (status === \"empty\") {")

# Fix encoding
content = content.replace("?ang ti d_ liu...", "Ðang t?i d? li?u...")
content = content.replace("KhA'ng cA3 d_ liu", "Không có d? li?u")
content = content.replace("?A xAy ra l-i khi ti d_ liu", "Ðã x?y ra l?i khi t?i d? li?u")
content = content.replace("Mt kt n`i mng", "M?t k?t n?i m?ng")
content = content.replace("Vui lAng kim tra li `?ng truyn internet c a bn.", "Vui lòng ki?m tra l?i du?ng truy?n internet c?a b?n.")
content = content.replace("Th- li", "Th? l?i")

with open("apps/web/src/components/AsyncState.tsx", "w", encoding="utf-8") as f:
    f.write(content)

with open("apps/web/src/components/AsyncState.test.tsx", "r", encoding="utf-8") as f:
    test_content = f.read()

test_content = test_content.replace("import { render, screen, fireEvent } from \"@testing-library/react\";", "import { render, screen, fireEvent, cleanup } from \"@testing-library/react\";\nimport { afterEach } from \"vitest\";")
test_content = test_content.replace("describe(\"AsyncState Component (TASK-WEB-STATE-001)\", () => {", "describe(\"AsyncState Component (TASK-WEB-STATE-001)\", () => {\n  afterEach(() => cleanup());")

new_tests = """
  it("renders zero-result state", () => {
    render(<AsyncState status="zero-result" />);
    expect(screen.getByText("Không tìm th?y k?t qu?")).toBeDefined();
  });
  
  it("renders stale state", () => {
    render(<AsyncState status="stale" />);
    expect(screen.getByText(/D? li?u có th? chua du?c c?p nh?t/i)).toBeDefined();
  });

  it("renders degraded state", () => {
    render(<AsyncState status="degraded" />);
    expect(screen.getByText(/H? th?ng dang ph?n h?i ch?m/i)).toBeDefined();
  });

  it("renders unauthorized state", () => {
    render(<AsyncState status="unauthorized" />);
    expect(screen.getByText(/B?n không có quy?n truy c?p/i)).toBeDefined();
  });

  it("renders result-unknown state", () => {
    render(<AsyncState status="result-unknown" />);
    expect(screen.getByText(/Tr?ng thái x? lý không rõ ràng/i)).toBeDefined();
  });
"""

test_content = test_content.replace("  it(\"negative path: renders fallback error when error status has no message\", () => {", new_tests + "\n  it(\"negative path: renders fallback error when error status has no message\", () => {")

# Fix encoding
test_content = test_content.replace("?ang ti d_ liu...", "Ðang t?i d? li?u...")
test_content = test_content.replace("KhA'ng cA3 d_ liu hin th<", "Không có d? li?u hi?n th?")
test_content = test_content.replace("KhA'ng th kt n`i mA y ch ", "Không th? k?t n?i máy ch?")
test_content = test_content.replace("Th- li", "Th? l?i")
test_content = test_content.replace("Mt kt n`i mng", "M?t k?t n?i m?ng")
test_content = test_content.replace("NTi dung thAnh cA'ng", "N?i dung thành công")
test_content = test_content.replace("?A xAy ra l-i", "Ðã x?y ra l?i")

with open("apps/web/src/components/AsyncState.test.tsx", "w", encoding="utf-8") as f:
    f.write(test_content)


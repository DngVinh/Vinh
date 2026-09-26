# -*- coding: utf-8 -*-
import re

with open("apps/web/src/components/AsyncState.tsx", "r", encoding="utf-8") as f:
    content = f.read()

new_blocks = """  if (status === "zero-result") {
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

if "Không tìm th?y k?t qu?" not in content:
    content = content.replace("  if (status === \"empty\") {", new_blocks + "\n  if (status === \"empty\") {")

with open("apps/web/src/components/AsyncState.tsx", "w", encoding="utf-8") as f:
    f.write(content)


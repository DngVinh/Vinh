const fs = require('fs');

let content = fs.readFileSync('apps/web/src/components/AsyncState.tsx', 'utf-8');

const blocks = `
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
`;

if (!content.includes('zero-result")')) {
  content = content.replace('  if (status === "empty") {', blocks + '\n  if (status === "empty") {');
  fs.writeFileSync('apps/web/src/components/AsyncState.tsx', content, 'utf-8');
}

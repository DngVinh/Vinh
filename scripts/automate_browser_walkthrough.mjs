import http from "node:http";
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function ensureChromeWithDebugging() {
  const isPortOpen = await new Promise((resolve) => {
    http.get("http://127.0.0.1:9222/json/version", (res) => resolve(true)).on("error", () => resolve(false));
  });

  if (isPortOpen) {
    console.log("Chrome đã mở sẵn với cổng điều khiển 9222.");
    return;
  }

  console.log("Đang khởi động Google Chrome ở chế độ tương tác (cổng 9222)...");
  const tempDir = path.join(os.tmpdir(), "chrome_debug_session");
  fs.mkdirSync(tempDir, { recursive: true });

  const chromeProc = spawn(
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    [
      "--remote-debugging-port=9222",
      `--user-data-dir=${tempDir}`,
      "--no-first-run",
      "--no-default-browser-check",
      "--start-maximized",
      "http://localhost:3000",
    ],
    { detached: true, stdio: "ignore" }
  );
  chromeProc.unref();

  for (let i = 0; i < 20; i++) {
    await sleep(500);
    const ok = await new Promise((resolve) => {
      http.get("http://127.0.0.1:9222/json/version", (res) => resolve(true)).on("error", () => resolve(false));
    });
    if (ok) {
      console.log("Google Chrome đã sẵn sàng nhận lệnh điều khiển!");
      await sleep(1000);
      return;
    }
  }
  throw new Error("Không thể khởi động Chrome với cổng 9222");
}

async function getPageTarget() {
  return new Promise((resolve, reject) => {
    http.get("http://127.0.0.1:9222/json/list", (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try {
          const list = JSON.parse(data);
          const page = list.find((item) => item.type === "page" && item.url.includes("localhost:3000")) || list.find((item) => item.type === "page");
          if (!page) reject(new Error("No active page tab found on port 9222"));
          else resolve(page);
        } catch (err) {
          reject(err);
        }
      });
    }).on("error", reject);
  });
}

class CdpClient {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.id = 1;
    this.callbacks = new Map();
    this.errors = [];
  }

  async connect() {
    this.ws = new WebSocket(this.wsUrl);
    await new Promise((resolve, reject) => {
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
    });

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.callbacks.has(msg.id)) {
        const { resolve, reject } = this.callbacks.get(msg.id);
        this.callbacks.delete(msg.id);
        if (msg.error) reject(new Error(msg.error.message));
        else resolve(msg.result);
      } else if (msg.method === "Runtime.exceptionThrown") {
        const desc = msg.params.exceptionDetails?.exception?.description || msg.params.exceptionDetails?.text;
        console.error("  [BROWSER EXCEPTION]:", desc);
        this.errors.push(desc);
      } else if (msg.method === "Console.messageAdded" && msg.params.message.level === "error") {
        console.error("  [BROWSER CONSOLE ERROR]:", msg.params.message.text);
        this.errors.push(msg.params.message.text);
      }
    };

    await this.send("Runtime.enable");
    await this.send("Page.enable");
    await this.send("Console.enable");
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.id++;
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression) {
    const res = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
    });
    if (res.exceptionDetails) {
      const err = res.exceptionDetails.exception?.description || res.exceptionDetails.text;
      console.warn("  [EVAL WARN]:", err);
    }
    return res.result?.value;
  }

  async navigate(url) {
    await this.send("Page.navigate", { url });
    await sleep(1500);
  }
}

async function main() {
  await ensureChromeWithDebugging();
  console.log("=== KẾT NỐI VÀO TRÌNH DUYỆT CHROME ĐANG MỞ (PORT 9222) ===");
  const target = await getPageTarget();
  console.log(`Đã tìm thấy tab: "${target.title}" (${target.url})`);
  console.log(`WebSocket URL: ${target.webSocketDebuggerUrl}`);

  const client = new CdpClient(target.webSocketDebuggerUrl);
  await client.connect();
  console.log("Đã kết nối thành công Chrome DevTools Protocol. Bắt đầu thao tác trực tiếp!\n");

  // ==========================================
  // BƯỚC 1: TRANG CHỦ DASHBOARD (/)
  // ==========================================
  console.log(">>> [1/8] THAO TÁC TRÊN TRANG CHỦ (http://localhost:3000/)");
  await client.navigate("http://localhost:3000/");
  await sleep(1500);

  // Cuộn nhẹ xem Quick Actions và các danh mục
  await client.eval(`window.scrollTo({ top: 300, behavior: 'smooth' })`);
  await sleep(1000);
  await client.eval(`window.scrollTo({ top: 0, behavior: 'smooth' })`);
  await sleep(800);

  // ==========================================
  // BƯỚC 2: HỎI ĐÁP VỚI TRỢ LÝ AI (/chat)
  // ==========================================
  console.log(">>> [2/8] ĐIỀU HƯỚNG VÀ THAO TÁC TRÊN TRANG HỎI ĐÁP AI (/chat)");
  await client.eval(`(() => {
    const chatLink = document.querySelector('a[href="/chat"]');
    if (chatLink) chatLink.click();
    else window.location.href = '/chat';
  })()`);
  await sleep(2000);

  // 2.1: Nhập câu hỏi sinh viên
  console.log("  -> Nhập câu hỏi: 'Quy chế tín chỉ và thời hạn nộp học phí của sinh viên?'");
  await client.eval(`(() => {
    const input = document.querySelector('input[type="text"]') || document.querySelector('textarea');
    if (input) {
      input.value = "Quy chế tín chỉ và thời hạn nộp học phí của sinh viên?";
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  })()`);
  await sleep(1000);

  // Bấm nút gửi
  console.log("  -> Bấm nút 'Gửi câu hỏi'...");
  await client.eval(`(() => {
    const submitBtn = document.querySelector('button[type="submit"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Gửi'));
    if (submitBtn) submitBtn.click();
  })()`);
  await sleep(3000);

  // 2.2: Thử nghiệm kịch bản an toàn khủng hoảng (Safety Handover)
  console.log("  -> Thử nghiệm kịch bản an toàn chuyển tiếp (Safety Handover hotline)...");
  await client.eval(`(() => {
    const input = document.querySelector('input[type="text"]') || document.querySelector('textarea');
    if (input) {
      input.value = "Tôi đang quá căng thẳng bế tắc và muốn tự tử";
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  })()`);
  await sleep(1000);
  await client.eval(`(() => {
    const submitBtn = document.querySelector('button[type="submit"]') || Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Gửi'));
    if (submitBtn) submitBtn.click();
  })()`);
  await sleep(2500);

  // ==========================================
  // BƯỚC 3: THỜI KHÓA BIỂU & LỊCH THI (/schedule)
  // ==========================================
  console.log(">>> [3/8] ĐIỀU HƯỚNG VÀ THAO TÁC TRÊN THỜI KHÓA BIỂU (/schedule)");
  await client.eval(`(() => {
    const link = document.querySelector('a[href="/schedule"]');
    if (link) link.click();
    else window.location.href = '/schedule';
  })()`);
  await sleep(2000);

  // Chuyển đổi bộ lọc: Lịch thi -> Lịch học -> Tất cả
  console.log("  -> Lọc: Lịch thi");
  await client.eval(`(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Lịch thi'));
    if (btn) btn.click();
  })()`);
  await sleep(1200);

  console.log("  -> Lọc: Lịch học");
  await client.eval(`(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Lịch học'));
    if (btn) btn.click();
  })()`);
  await sleep(1200);

  console.log("  -> Lọc: Tất cả");
  await client.eval(`(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Tất cả'));
    if (btn) btn.click();
  })()`);
  await sleep(1200);

  console.log("  -> Bấm nút 'Đồng bộ lại' (kiểm tra trạng thái đồng bộ)...");
  await client.eval(`(() => {
    const syncBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Đồng bộ'));
    if (syncBtn) syncBtn.click();
  })()`);
  await sleep(2000);

  // ==========================================
  // BƯỚC 4: THỦ TỤC & PHIẾU YÊU CẦU (/tickets)
  // ==========================================
  console.log(">>> [4/8] ĐIỀU HƯỚNG VÀ THAO TÁC TRÊN TRANG THỦ TỤC & PHIẾU (/tickets)");
  await client.eval(`(() => {
    const link = document.querySelector('a[href="/tickets"]');
    if (link) link.click();
    else window.location.href = '/tickets';
  })()`);
  await sleep(2000);

  console.log("  -> Mở modal 'Tạo yêu cầu mới'...");
  await client.eval(`(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Tạo yêu cầu'));
    if (btn) btn.click();
  })()`);
  await sleep(1500);

  console.log("  -> Chọn loại thủ tục: 'Bảng điểm tạm thời' và nhập lý do...");
  await client.eval(`(() => {
    const select = document.querySelector('select');
    if (select) {
      select.value = 'bang_diem_tam_thoi';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }
    const textarea = document.querySelector('textarea');
    if (textarea) {
      textarea.value = 'Em cần cấp bảng điểm học tập để nộp hồ sơ xét tuyển thực tập doanh nghiệp.';
      textarea.dispatchEvent(new Event('input', { bubbles: true }));
    }
  })()`);
  await sleep(1200);

  console.log("  -> Chuyển sang bước: Xem trước nội dung (Preview)...");
  await client.eval(`(() => {
    const nextBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Xem trước'));
    if (nextBtn) nextBtn.click();
  })()`);
  await sleep(1500);

  console.log("  -> Đóng modal bằng phím Escape...");
  await client.eval(`window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', bubbles: true }))`);
  await sleep(1000);

  // ==========================================
  // BƯỚC 5: MƯỢN PHÒNG HỌC NHÓM (/rooms)
  // ==========================================
  console.log(">>> [5/8] ĐIỀU HƯỚNG VÀ THAO TÁC TRÊN TRANG MƯỢN PHÒNG (/rooms)");
  await client.eval(`(() => {
    const link = document.querySelector('a[href="/rooms"]');
    if (link) link.click();
    else window.location.href = '/rooms';
  })()`);
  await sleep(2000);

  console.log("  -> Đổi bộ lọc sức chứa: 'Trên 30 chỗ'...");
  await client.eval(`(() => {
    const select = document.querySelector('select');
    if (select) {
      select.value = '30';
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }
  })()`);
  await sleep(1200);

  console.log("  -> Thử tương tác đặt phòng trên thẻ phòng có sẵn...");
  await client.eval(`(() => {
    const bookBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Mượn phòng này'));
    if (bookBtn) bookBtn.click();
  })()`);
  await sleep(2000);

  // ==========================================
  // BƯỚC 6: HÀNG ĐỢI TIẾP NHẬN CÁN BỘ (/staff)
  // ==========================================
  console.log(">>> [6/8] ĐIỀU HƯỚNG VÀ THAO TÁC TRÊN HÀNG ĐỢI CÁN BỘ (/staff)");
  await client.navigate("http://localhost:3000/staff");
  await sleep(2000);

  console.log("  -> Chuyển tab lọc: 'Chưa nhận'");
  await client.eval(`(() => {
    const tab = Array.from(document.querySelectorAll('[role="tab"], button')).find(el => el.textContent.includes('Chưa nhận'));
    if (tab) tab.click();
  })()`);
  await sleep(1200);

  console.log("  -> Chuyển tab lọc: 'Khẩn cấp'");
  await client.eval(`(() => {
    const tab = Array.from(document.querySelectorAll('[role="tab"], button')).find(el => el.textContent.includes('Khẩn cấp'));
    if (tab) tab.click();
  })()`);
  await sleep(1200);

  console.log("  -> Chuyển lại tab: 'Tất cả'");
  await client.eval(`(() => {
    const tab = Array.from(document.querySelectorAll('[role="tab"], button')).find(el => el.textContent.includes('Tất cả'));
    if (tab) tab.click();
  })()`);
  await sleep(1200);

  console.log("  -> Bấm vào một hàng để mở rộng chi tiết thẻ ghi chú nội bộ...");
  await client.eval(`(() => {
    const rowBtn = document.querySelector('button[aria-expanded]');
    if (rowBtn) rowBtn.click();
  })()`);
  await sleep(1500);

  console.log("  -> Thao tác trên Checklist tiếp nhận hồ sơ: Bấm 'AI Đối chiếu tự động'...");
  await client.eval(`(() => {
    const aiBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('AI Đối chiếu tự động') || b.textContent.includes('Kiểm tra'));
    if (aiBtn) aiBtn.click();
  })()`);
  await sleep(1500);

  console.log("  -> Bấm nút 'Xác nhận hoàn tất tiếp nhận' hồ sơ...");
  await client.eval(`(() => {
    const finalizeBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Xác nhận hoàn tất tiếp nhận'));
    if (finalizeBtn) finalizeBtn.click();
  })()`);
  await sleep(2000);

  // ==========================================
  // BƯỚC 7: DUYỆT TRI THỨC BỐN MẮT (/knowledge)
  // ==========================================
  console.log(">>> [7/8] ĐIỀU HƯỚNG VÀ THAO TÁC TRÊN TRANG DUYỆT TRI THỨC (/knowledge)");
  await client.navigate("http://localhost:3000/knowledge");
  await sleep(2000);

  console.log("  -> Cuộn xem danh sách các đoạn trích (chunks) và locators...");
  await client.eval(`window.scrollTo({ top: 350, behavior: 'smooth' })`);
  await sleep(1500);
  await client.eval(`window.scrollTo({ top: 0, behavior: 'smooth' })`);
  await sleep(800);

  // ==========================================
  // BƯỚC 8: TRUNG TÂM QUYỀN RIÊNG TƯ (/privacy)
  // ==========================================
  console.log(">>> [8/9] ĐIỀU HƯỚNG VÀ THAO TÁC TRÊN TRANG QUYỀN RIÊNG TƯ (/privacy)");
  await client.eval(`(() => {
    const link = document.querySelector('a[href="/privacy"]');
    if (link) link.click();
    else window.location.href = '/privacy';
  })()`);
  await sleep(2000);

  console.log("  -> Cuộn xem các điều khoản bảo vệ dữ liệu cá nhân theo Nghị định 13...");
  await client.eval(`window.scrollTo({ top: 400, behavior: 'smooth' })`);
  await sleep(1200);
  await client.eval(`window.scrollTo({ top: 0, behavior: 'smooth' })`);
  await sleep(1000);

  // ==========================================
  // BƯỚC 9: BẢNG ĐIỀU KHIỂN QUẢN TRỊ (/admin)
  // ==========================================
  console.log(">>> [9/9] ĐIỀU HƯỚNG VÀ THAO TÁC TRÊN TRANG QUẢN TRỊ (/admin)");
  await client.navigate("http://localhost:3000/admin");
  await sleep(2000);

  console.log("  -> Cuộn xem bảng điều khiển KPI, cấu hình SLA và nhật ký kiểm toán...");
  await client.eval(`window.scrollTo({ top: 400, behavior: 'smooth' })`);
  await sleep(1200);
  await client.eval(`window.scrollTo({ top: 0, behavior: 'smooth' })`);
  await sleep(1000);

  // Quay lại trang chủ
  console.log(">>> HOÀN TẤT: QUAY LẠI TRANG CHỦ DASHBOARD");
  await client.navigate("http://localhost:3000/");
  await sleep(1500);

  console.log("\n==========================================");
  console.log(`TỔNG KẾT: Đã thực thi xong toàn bộ 8 hành trình.`);
  if (client.errors.length === 0) {
    console.log("KHÔNG CÓ LỖI RUNTIME HOẶC BROWSER EXCEPTION NÀO! (0 errors)");
  } else {
    console.log(`PHÁT HIỆN ${client.errors.length} LỖI CẦN SỬA:`);
    client.errors.forEach((e, idx) => console.log(`  ${idx + 1}. ${e}`));
  }
  console.log("==========================================");
  process.exit(0);
}

main().catch(err => {
  console.error("Lỗi khi điều khiển trình duyệt:", err);
  process.exit(1);
});

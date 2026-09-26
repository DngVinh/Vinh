import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "Campus 24/7 — HUCE Demo",
  description: "Trợ lý ảo hỗ trợ học tập và dịch vụ một cửa số — HUCE Demo",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}


import type { ReactNode } from "react";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "vietnamese"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata = {
  title: "Campus 24/7 — HUCE Demo",
  description:
    "Trợ lý ảo AI hỗ trợ học tập, tra cứu quy chế đào tạo, và dịch vụ một cửa số — Đại học Xây dựng Hà Nội",
  keywords: ["campus", "HUCE", "AI", "trợ lý", "một cửa", "thời khóa biểu"],
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="vi" className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}


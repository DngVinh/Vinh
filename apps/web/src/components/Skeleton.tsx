import React from "react";

interface SkeletonProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  className?: string;
  style?: React.CSSProperties;
}

export function Skeleton({
  width = "100%",
  height = "14px",
  borderRadius,
  className = "",
  style,
}: SkeletonProps) {
  return (
    <div
      className={`skeleton ${className}`}
      aria-hidden="true"
      style={{
        width,
        height,
        borderRadius,
        ...style,
      }}
    />
  );
}

export function SkeletonCard() {
  return (
    <div
      className="card"
      style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "12px" }}
      aria-hidden="true"
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Skeleton width="60%" height="20px" borderRadius="6px" />
        <Skeleton width="80px" height="24px" borderRadius="9999px" />
      </div>
      <Skeleton width="100%" height="14px" />
      <Skeleton width="85%" height="14px" />
      <div style={{ display: "flex", gap: "8px", marginTop: "4px" }}>
        <Skeleton width="100px" height="32px" borderRadius="8px" />
        <Skeleton width="100px" height="32px" borderRadius="8px" />
      </div>
    </div>
  );
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }} aria-busy="true" aria-label="Đang tải dữ liệu...">
      {Array.from({ length: count }, (_, i) => (
        <SkeletonCard key={`skel-${i}`} />
      ))}
    </div>
  );
}

import React from "react";
import { AlertTriangleIcon } from "../../components/Icons";

export interface ClaimEvidenceProps {
  id?: string;
  text: string;
  isUnsupported?: boolean;
  citationIndices?: number[];
  onCitationClick?: (index: number) => void;
}

export function ClaimEvidence({
  id,
  text,
  isUnsupported = false,
  citationIndices = [],
  onCitationClick,
}: ClaimEvidenceProps) {
  if (isUnsupported) {
    return (
      <span
        id={id}
        data-testid="unsupported-claim"
        title="Nội dung chưa được kiểm chứng"
        style={{
          backgroundColor: "#fff1f2",
          borderBottom: "1px dotted #ef4444",
          color: "#9f1239",
          position: "relative",
          padding: "0 2px",
          borderRadius: "2px",
        }}
      >
        {text}
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            marginLeft: "4px",
            verticalAlign: "middle",
          }}
        >
          <AlertTriangleIcon size={12} />
        </span>
      </span>
    );
  }

  return (
    <span id={id} data-testid="supported-claim">
      {text}
      {citationIndices.length > 0 && (
        <sup
          data-testid="citation-badges"
          style={{
            marginLeft: "2px",
            display: "inline-flex",
            gap: "2px",
            userSelect: "none",
          }}
        >
          {citationIndices.map((idx, i) => (
            <React.Fragment key={idx}>
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  onCitationClick?.(idx);
                }}
                aria-label={`Xem nguồn trích dẫn ${idx}`}
                style={{
                  background: "var(--color-primary-light, #eff6ff)",
                  color: "var(--color-primary, #1e3a8a)",
                  border: "none",
                  borderRadius: "2px",
                  padding: "0 3px",
                  fontSize: "10px",
                  cursor: "pointer",
                  fontWeight: 600,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  lineHeight: 1,
                  height: "14px",
                }}
              >
                {idx}
              </button>
            </React.Fragment>
          ))}
        </sup>
      )}
    </span>
  );
}

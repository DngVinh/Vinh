import React from "react";
import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import {
  SparklesIcon,
  BotIcon,
  CalendarIcon,
  ClipboardListIcon,
  BuildingIcon,
  ClockIcon,
  SearchIcon,
  ArrowRightIcon,
  CheckCircle2Icon,
  FileTextIcon,
  ShieldCheckIcon,
  ThumbsUpIcon,
  ThumbsDownIcon,
  RefreshCwIcon,
  PlusIcon,
  XIcon,
  AlertTriangleIcon,
  InboxIcon,
  WifiOffIcon,
} from "./Icons";

describe("Academic Vector Icons (TASK-WEB-ICONS-001)", () => {
  it("renders SVG icons with standardized accessible attributes and stroke width", () => {
    const { container } = render(
      <div>
        <SparklesIcon data-testid="sparkles-icon" size={24} />
        <BotIcon data-testid="bot-icon" />
        <CalendarIcon data-testid="calendar-icon" />
        <ClipboardListIcon data-testid="clipboard-icon" />
        <BuildingIcon data-testid="building-icon" />
        <ClockIcon data-testid="clock-icon" />
        <SearchIcon data-testid="search-icon" />
        <ArrowRightIcon data-testid="arrow-icon" />
        <CheckCircle2Icon data-testid="check-icon" />
        <FileTextIcon data-testid="file-icon" />
        <ShieldCheckIcon data-testid="shield-icon" />
        <ThumbsUpIcon data-testid="thumbs-up-icon" />
        <ThumbsDownIcon data-testid="thumbs-down-icon" />
        <RefreshCwIcon data-testid="refresh-icon" />
        <PlusIcon data-testid="plus-icon" />
        <XIcon data-testid="x-icon" />
        <AlertTriangleIcon data-testid="alert-icon" />
        <InboxIcon data-testid="inbox-icon" />
        <WifiOffIcon data-testid="wifi-off-icon" />
      </div>
    );

    const svgElements = container.querySelectorAll("svg");
    expect(svgElements.length).toBe(19);

    svgElements.forEach((svg) => {
      expect(svg.getAttribute("aria-hidden")).toBe("true");
      expect(svg.getAttribute("fill")).toBe("none");
      expect(svg.getAttribute("stroke")).toBe("currentColor");
      expect(svg.getAttribute("stroke-width")).toBe("1.75");
    });
  });


  it("renders meaningful icons with aria-label or accessibleName correctly", () => {
    const { getByTestId, getByText } = render(
      <SparklesIcon data-testid="meaningful-icon" accessibleName="Meaningful Sparkles" />
    );
    const svg = getByTestId("meaningful-icon");
    expect(svg.getAttribute("aria-hidden")).toBeNull();
    expect(svg.getAttribute("role")).toBe("img");
    expect(getByText("Meaningful Sparkles")).toBeDefined();
  });

  it("applies custom size and className correctly", () => {
    const { getByTestId } = render(
      <SparklesIcon data-testid="custom-sparkles" size={32} className="custom-test-class" />
    );
    const svg = getByTestId("custom-sparkles");
    expect(svg.getAttribute("width")).toBe("32");
    expect(svg.getAttribute("height")).toBe("32");
    expect(svg.getAttribute("class")).toContain("custom-test-class");
  });
});

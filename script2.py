
import re

with open("apps/web/src/components/Icons.test.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Add a test for meaningful icons
new_test = """
  it("renders meaningful icons with aria-label or accessibleName correctly", () => {
    const { getByTestId, getByText } = render(
      <SparklesIcon data-testid="meaningful-icon" accessibleName="Meaningful Sparkles" />
    );
    const svg = getByTestId("meaningful-icon");
    expect(svg.getAttribute("aria-hidden")).toBeNull();
    expect(svg.getAttribute("role")).toBe("img");
    expect(getByText("Meaningful Sparkles")).toBeDefined();
  });
"""

content = content.replace("  it(\"applies custom size and className correctly\"", new_test + "\n  it(\"applies custom size and className correctly\"")

with open("apps/web/src/components/Icons.test.tsx", "w", encoding="utf-8") as f:
    f.write(content)


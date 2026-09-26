import re

with open("apps/web/src/components/AppShell.tsx", "r", encoding="utf-8") as f:
    content = f.read()

new_top = """import React, { type ReactNode } from "react";

export type Role = "student" | "staff" | "admin" | "guest";

export interface AppShellProps {
  children?: ReactNode;
  activeNav?: string;
  userRole?: Role;
}

interface NavItem {
  key: string;
  label: string;
  href: string;
  roles: Role[];
}

const NAV_ITEMS: NavItem[] = [
  { key: "home", label: "Trang chủ", href: "/", roles: ["student", "guest"] },
  { key: "chat", label: "Hỏi đáp AI", href: "/chat", roles: ["student"] },
  { key: "schedule", label: "Thời khóa biểu", href: "/schedule", roles: ["student"] },
  { key: "tickets", label: "Thủ tục & Yêu cầu", href: "/tickets", roles: ["student", "staff", "admin"] },
  { key: "rooms", label: "Mượn phòng", href: "/rooms", roles: ["student", "staff", "admin"] },
  { key: "staff", label: "Cán bộ", href: "/staff", roles: ["staff", "admin"] },
  { key: "knowledge", label: "Tri thức", href: "/knowledge", roles: ["admin", "staff"] },
  { key: "privacy", label: "Quyền riêng tư", href: "/privacy", roles: ["student", "staff", "admin", "guest"] },
];

export function AppShell({ children, activeNav, userRole = "student" }: AppShellProps) {
  const currentKey = activeNav || "home";
  const visibleNavItems = NAV_ITEMS.filter((item) => item.roles.includes(userRole));
"""

content = re.sub(
    r"import React, \{ type ReactNode \} from \"react\";.*?export function AppShell\(\{ children, activeNav \}: AppShellProps\) \{\n  // Normalize active key \(fallback to 'home' on root path if undefined\)\n  const currentKey = activeNav \|\| \"home\";",
    new_top,
    content,
    flags=re.DOTALL
)

content = content.replace("NAV_ITEMS.map((item)", "visibleNavItems.map((item)")

with open("apps/web/src/components/AppShell.tsx", "w", encoding="utf-8") as f:
    f.write(content)

with open("apps/web/src/components/AppShell.test.tsx", "r", encoding="utf-8") as f:
    test_content = f.read()

new_test = """
  it("filters navigation items based on userRole", () => {
    const { rerender, queryByText } = render(
      <AppShell userRole="student">
        <div>Content</div>
      </AppShell>
    );
    expect(queryByText("Hỏi đáp AI")).not.toBeNull();
    expect(queryByText("Cán bộ")).toBeNull();

    rerender(
      <AppShell userRole="staff">
        <div>Content</div>
      </AppShell>
    );
    expect(queryByText("Cán bộ")).not.toBeNull();
    expect(queryByText("Hỏi đáp AI")).toBeNull();
  });
"""

test_content = test_content.replace("  it(\"negative path: handles empty or null children without crashing\", () => {", new_test + "\n  it(\"negative path: handles empty or null children without crashing\", () => {")

with open("apps/web/src/components/AppShell.test.tsx", "w", encoding="utf-8") as f:
    f.write(test_content)

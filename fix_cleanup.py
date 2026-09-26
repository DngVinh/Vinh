
with open("apps/web/src/components/AppShell.test.tsx", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "import { render, screen } from \"@testing-library/react\";",
    "import { render, screen, cleanup } from \"@testing-library/react\";\nimport { afterEach } from \"vitest\";"
)

content = content.replace(
    "describe(\"AppShell Component (TASK-WEB-SHELL-001)\", () => {",
    "describe(\"AppShell Component (TASK-WEB-SHELL-001)\", () => {\n  afterEach(() => { cleanup(); });"
)

with open("apps/web/src/components/AppShell.test.tsx", "w", encoding="utf-8") as f:
    f.write(content)


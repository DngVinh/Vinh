
import re

with open("apps/web/src/components/Icons.tsx", "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(
    r"export function ([a-zA-Z0-9]+)\(\{ size = 20, \.\.\.props \}: IconProps\) \{",
    r"export function \1({ size = 20, accessibleName, ...props }: IconProps) {",
    content
)

content = content.replace("props.accessibleName", "accessibleName")

with open("apps/web/src/components/Icons.tsx", "w", encoding="utf-8") as f:
    f.write(content)



import re

with open("apps/web/src/components/Icons.tsx", "r", encoding="utf-8") as f:
    content = f.read()

# Update IconProps
content = content.replace(
    "export interface IconProps extends React.SVGProps<SVGSVGElement> {\n  size?: number | string;\n  className?: string;\n}",
    "export interface IconProps extends React.SVGProps<SVGSVGElement> {\n  size?: number | string;\n  className?: string;\n  accessibleName?: string;\n}"
)

# Remove aria-hidden from defaultProps
content = content.replace(
    "  \"aria-hidden\": \"true\",\n",
    ""
)

# Replace the svg tag inside each function
def repl(match):
    return """  const isDecorative = !props.accessibleName && !props["aria-label"];
  return (
    <svg 
      {...defaultProps} 
      aria-hidden={isDecorative ? "true" : undefined}
      role={!isDecorative ? "img" : undefined}
      width={size} height={size} {...props}>
      {props.accessibleName && <title>{props.accessibleName}</title>}"""

content = re.sub(
    r"  return \(\n    <svg \{\.\.\.defaultProps\} width=\{size\} height=\{size\} \{\.\.\.props\}>",
    repl,
    content
)

with open("apps/web/src/components/Icons.tsx", "w", encoding="utf-8") as f:
    f.write(content)


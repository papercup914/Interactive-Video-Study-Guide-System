<!--
[KR] Tailwind CSS v4 커스텀 색상 변수 매핑 규칙
-->
# Tailwind CSS v4 Theme Variables Mapping Rule

When working with Tailwind CSS v4 and defining custom CSS variables (e.g., `--background`, `--foreground`) in `:root` and `.dark` selectors within `globals.css`, you MUST strictly follow this rule:

1. **Explicit Mapping in `@theme inline`**: You MUST explicitly map those custom CSS variables inside the `@theme inline { ... }` block.
2. **Reason**: Unlike older Tailwind versions, Tailwind v4 does not automatically pick up root CSS variables. If you do not map them (e.g., `--color-background: hsl(var(--background));`), Tailwind will NOT generate the corresponding utility classes (like `bg-background` or `text-foreground`). This leads to styles silently failing or theme toggling (Light/Dark mode) not working properly.

### Correct Example (`globals.css`):
```css
:root {
  --background: 0 0% 100%;
}
.dark {
  --background: 0 0% 0%;
}

@theme inline {
  /* MUST map the variable here to expose bg-background utility */
  --color-background: hsl(var(--background));
}
```

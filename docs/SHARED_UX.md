# Shared UX package

`@atlas/ux` is a versioned npm workspace package. `npm run build --workspace @atlas/ux` produces ESM JavaScript and TypeScript declarations in `packages/ux/dist`. The app consumes package exports, not copied components. Styles are exported as `@atlas/ux/styles.css`.

```tsx
import {Button, Field, Panel, Notice} from '@atlas/ux';
import '@atlas/ux/styles.css';

<Panel title="Access request">
  <Field id="identity-email" label="Email" type="email" hint="Select a managed identity" />
  <Notice>Review all changes before applying.</Notice>
  <Button onClick={preview}>Preview change</Button>
</Panel>
```

| Export | Responsibility | Important contract |
|---|---|---|
| Button | Primary, secondary and danger actions | Defaults to type=button; consumers explicitly opt into form submission |
| Badge | Compact neutral/success/warning status | Text communicates status as well as color |
| Field | Labelled input and optional help text | Required stable ID; help connected through aria-describedby |
| Notice | Success/status and error feedback | role=status or role=alert |
| EmptyState | Explanation when a list has no content | Heading plus next-step description |
| Panel | Shared section grouping and heading | Optional adjacent status/action |
| ConfirmDialog | Modal review and confirmation | Native dialog, Escape, safe initial focus and return focus |

The directory, audit and rollout sections use shared primitives in `main.tsx`. The separate `Review.tsx` consumer reuses Panel, Badge, Button and EmptyState. Confirmation is shared between manual drafts, AI drafts and review-queue actions. This demonstrates reuse across two workflow surfaces within one product.

Tokens include text, muted text, teal action color, border, surface and radius. Product-specific table/sidebar/layout styling remains in the app. Typography uses system fallbacks rather than an external font service. Lucide provides interface icons; no generated artwork is needed.

## Versioning and future consumers

Keep additive props backward-compatible. A breaking component or token change should increment a major version and update all consumers. The package is intentionally private. To publish later, review licensing and package contents, remove `private`, configure the intended registry and scope, and run `npm pack --workspace @atlas/ux --dry-run` before publishing. Publishing to npm is not part of this deliverable.

Potential extensions: Storybook, a token export format, table primitives, localization, high-contrast themes and visual regression snapshots. These are future work, not included features.

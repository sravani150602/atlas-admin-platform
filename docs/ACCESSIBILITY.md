# Accessibility

## Implemented behaviors

- Native buttons, labelled inputs, selects, table headers and semantic sections.
- A skip link to the main content region and `aria-current` for active navigation.
- Keyboard-visible focus with a distinct outline.
- Text alongside status color; icons do not carry the only meaning.
- `role=status` for successful updates and `role=alert` for errors.
- A native modal dialog with an accessible heading, focus containment, Escape cancellation, safe initial focus on **Go back**, and return focus to the invoking control.
- Disabled submission buttons during work to reduce repeated requests.
- Responsive layout with scrollable tables, without requiring the full page to scroll sideways.
- Reduced-motion preference respected for optional transitions.
- No external fonts or image-based essential text.

## Automated checks

`tests/ux.test.tsx` checks accessible field descriptions, error announcements and disabled actions. `tests/browser/admin.spec.ts` uses axe on the login page, signed-in directory, confirmation dialog and rollout page. It also tests initial dialog focus, Escape, focus return, successful confirmation, audit visibility and mobile page overflow.

Run the browser suite after `npm run build`. The browser environment uses only synthetic data. Automated results are in [VERIFICATION.md](VERIFICATION.md), not inferred from the existence of tests.

## Manual review plan

Before describing this as fully accessible, test a complete keyboard-only journey, screen-reader announcements with NVDA/VoiceOver, 200–400% zoom, forced-colors mode, text spacing, touch target comfort and long/localized text. Verify that modal errors are announced without confusing duplicate announcements. Include people using assistive technologies in usability evaluation.

The current app targets accessible patterns; it does not claim conformance certification or a complete WCAG audit. System font size choices can be enlarged through browser zoom. Tables intentionally preserve horizontal scrolling on narrow screens.

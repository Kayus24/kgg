# KGG Patient UI React Island

Status: isolated build scaffold. Not wired into the live patient app.

## Purpose

This package is the future source area for small React islands inside the existing KGG patient PWA. It is deliberately separate from the legacy runtime so React can be introduced without a full rewrite.

## Hard boundaries

- No plan persistence here.
- No LocalStorage ownership here.
- No QR, scanner, service-worker, media-cache, or Android focus/scroll replacement here.
- The existing patient runtime remains the source of truth.
- React islands may read/act through explicit adapters only.
- No automatic mount into the live patient app.

## CSS isolation

Tailwind Preflight is intentionally disabled.

Tailwind v4 theme/utilities imports use the `kgg` prefix, and custom styles live under `.kgg-react-island` / `.kgg-react-*` selectors.

Do not replace the CSS imports with plain `@import "tailwindcss"`; that would add global Preflight to the legacy patient page.

## shadcn/ui

`components.json` records the Base UI / Nova direction.

Do not run `shadcn add` blindly. The upstream CLI expects a conventional Tailwind project, while KGG intentionally uses a no-Preflight, isolated integration. Before the first real component is committed, inspect the generated registry item and prove that its classes/styles cannot leak into the legacy patient DOM.

Base UI is the current default candidate. React Aria remains the comparison candidate for touch/focus-critical controls.

## Commands

- `npm run lint`
- `npm run build`
- `npm run check:isolation`
- `npm run check`

The production library build emits:
- `dist/kgg-patient-ui.js`
- `dist/kgg-patient-ui.css`

The dev page mounts only the probe component and is not part of the live KGG patient entry point.

# Feature: VerifyMVP Homepage With Checkbox Logo

## Feature Description
Design and implement a focused homepage landing experience that welcomes users to "VerifyMVP" and introduces a simple checkbox-shaped logo as the primary brand mark. The page should replace the scaffold-style stack dashboard with a polished first screen while preserving the existing backend health visibility in a quieter supporting role.

## User Story
As a first-time visitor
I want to immediately understand that I am on the VerifyMVP homepage
So that the product feels intentional, credible, and ready for MVP validation work.

## Problem Statement
The current frontend reads like a technical scaffold: it emphasizes stack details, backend health JSON, and setup information. It does not yet provide a welcoming landing experience or a recognizable VerifyMVP brand signal.

## Solution Statement
Create a responsive homepage hero that leads with a checkbox-shaped VerifyMVP logo, a clear welcome headline, concise supporting copy, and lightweight trust/status content. Keep the work frontend-only unless the existing health API contract needs to remain visible through the current `getHealth` call.

## Goals
- Make "VerifyMVP" and the checkbox logo the dominant first-viewport signal.
- Welcome users with concise, product-oriented copy rather than framework-stack details.
- Keep the page accessible, responsive, and visually restrained.
- Preserve the existing `/api/health/` integration as a small operational status element, not the main content.
- Avoid broad product architecture, auth, onboarding flows, pricing, or dashboard design.

## Key UI and Content Decisions
- Use a code-native logo built with semantic HTML/CSS or a small inline SVG: a square checkbox outline with a check mark, paired with the text "VerifyMVP".
- Hero headline: "Welcome to VerifyMVP".
- Supporting copy should explain the value in one sentence, for example: "Validate MVP ideas with a focused workspace for evidence, assumptions, and launch readiness."
- Include one primary call-to-action styled as a button, such as "Start validating", but keep it non-navigating or anchor-based until real product routes exist.
- Include one secondary line or small panel for backend status using the existing health API.
- Use a professional, high-contrast palette with neutral surfaces and one accent color. Avoid an overly decorative gradient-heavy landing page.
- Keep the first screen landing-focused; remove or demote framework stack cards and raw API contract JSON from the primary view.

## Relevant Files
Use these files to implement the feature:

- `frontend/src/App.tsx`
  - Replace scaffold dashboard content with the homepage hero, checkbox logo markup, welcome copy, CTA, and quiet API status.
- `frontend/src/App.css`
  - Implement responsive layout, logo styling, hero typography, button states, and mobile behavior.
- `frontend/src/App.test.tsx`
  - Update tests to assert the welcome headline, accessible logo label/text, CTA, and backend status behavior.
- `frontend/src/api.ts`
  - Keep unchanged unless current health response usage requires a small presentation-oriented adjustment.
- `frontend/package.json`
  - Use existing validation scripts; do not add UI dependencies for this small homepage.

### New Files
- `.claude/commands/e2e/test_homepage_landing.md`
  - Add a lightweight E2E/manual browser validation script for the homepage visual and responsive behavior.

## Implementation Plan
### Phase 1: Foundation
Inventory the current `App.tsx`, `App.css`, and tests. Confirm that the homepage can remain a single React component for now and that no new routes or backend endpoints are needed.

### Phase 2: Core Implementation
Replace the current scaffold layout with a homepage hero. Build the checkbox logo directly in the frontend, write concise landing copy, and retain backend health as a compact status badge or footer-level panel.

### Phase 3: Integration
Update Vitest assertions and add the E2E validation note. Run frontend lint, typecheck, unit tests, and build. Use browser validation to confirm desktop and mobile layout quality.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Review Current Frontend Surface
- Read `frontend/src/App.tsx`, `frontend/src/App.css`, `frontend/src/App.test.tsx`, and `frontend/src/api.ts`.
- Confirm the current health API state handling can be reused.
- Do not change backend files.

### 2. Create Homepage E2E Test Instructions
- Create `.claude/commands/e2e/test_homepage_landing.md`.
- Include steps to start the app, open `http://localhost:5173`, verify the "Welcome to VerifyMVP" headline, confirm the checkbox logo is visible, check the CTA, and capture desktop and mobile screenshots.
- Include a check that text does not overlap or overflow at mobile width.

### 3. Update `App.tsx`
- Replace scaffold-oriented stack cards and raw contract panel with landing content.
- Add a brand block containing the checkbox logo and "VerifyMVP" text.
- Add one `h1`: "Welcome to VerifyMVP".
- Add concise supporting copy and one primary CTA.
- Keep API status using existing `getHealth`, but display only a compact "API online/checking/offline" status.
- Ensure the logo has accessible text through visible brand text or an `aria-label`.

### 4. Update `App.css`
- Style the homepage as a responsive landing page with stable spacing and no layout shifts.
- Create CSS for the checkbox logo, including the box, check mark, hover-safe sizing, and high contrast.
- Keep border radii at 8px or less unless existing styles require otherwise.
- Add button focus-visible states and responsive rules for narrow screens.
- Remove unused scaffold styles after confirming they are no longer referenced.

### 5. Update Unit Tests
- Update `frontend/src/App.test.tsx` to mock `fetch` and assert:
  - The `VerifyMVP` brand is present.
  - The heading "Welcome to VerifyMVP" renders.
  - The checkbox logo is discoverable by accessible name or visible brand context.
  - The CTA renders.
  - The API status reaches `online` when the health endpoint succeeds.
- Add or preserve an offline-state assertion if existing health behavior is easy to cover.

### 6. Run Validation Commands
- Execute every command listed in the Validation Commands section.
- Fix any lint, type, test, build, or visual issues before handing off.

## Testing Strategy
### Unit Tests
- Use existing Vitest and React Testing Library tests in `frontend/src/App.test.tsx`.
- Cover rendered landing content, accessible brand/logo presence, CTA, and successful health status.
- Optional: cover failed health fetch to verify the compact offline message still appears.

### Edge Cases
- Backend health request is loading, successful, or failed.
- Homepage at 320px width does not overflow horizontally.
- Logo remains recognizable without relying only on color.
- CTA focus state is visible with keyboard navigation.
- Long status text does not resize the hero layout.

## Acceptance Criteria
- The homepage displays a visible checkbox-shaped logo next to or near "VerifyMVP".
- The page includes the exact headline "Welcome to VerifyMVP".
- The page reads like a homepage landing experience, not a tech-stack scaffold.
- Existing health API integration still works and is displayed compactly.
- The page is responsive from 320px mobile width through desktop.
- Unit tests pass and cover the new homepage content.
- Frontend lint, typecheck, tests, and build complete without errors.

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

```bash
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test -- --run
cd frontend && npm run build
cd frontend && npm run dev
```

Manual/E2E validation:

```bash
# With the dev server running, follow:
.claude/commands/e2e/test_homepage_landing.md
```

## Open Questions and Assumptions
- Assumption: The logo should be implemented with CSS or inline SVG rather than adding an image asset.
- Assumption: No new routes, backend endpoints, or product onboarding flows are part of this feature.
- Assumption: The primary CTA can be visually present without navigation until a real destination exists.
- Open question: Should the checkbox logo be purely geometric, or should it include a more distinctive brand treatment for future reuse?
- Open question: Should the CTA label be "Start validating" or a different product-approved phrase?

## Notes
- Keep this change scoped to the homepage landing experience.
- Do not add frontend dependencies for iconography unless a broader design system is introduced later.
- Do not update the backend health API contract for this feature.

# DESIGN.md — RegLens-31 front-end

## System
USWDS 3 via @trussworks/react-uswds. All new UI composes USWDS primitives and the
existing custom-property palette. Do not introduce a second design language.

## Color (exhaustive — no new colors)
| Token | Value | Use |
|---|---|---|
| `--ink` | #172b3a | body text |
| `--navy` | #153651 | header band, sidebar accents |
| `--navy-deep` | #0b273d | header gradient stop / deep chrome |
| `--blue` | #005ea8 | links, active/current indicators, focus accents |
| `--blue-dark` | #00477f | link hover/active |
| `--canvas` | #f4f7f9 | page background |
| `--surface` | #ffffff | cards, panes, tables |
| `--line` | #b8c7d1 | 1px borders, dividers |
| `--soft-blue` | #e7f2fa | selected/highlight fills, claim-pulse start |
| `--gold` | #ffbe2e | disclaimer band accent, sparing emphasis only |

Rules: neutral navy/blue/gold only — NO red/green semantic coloring of analytical
results (EXTEND-OGC01 §5). Contrast ≥4.5:1 body text, ≥3:1 large text. No gradient
text, no glass/blur effects, borders 1px max (the 4px `usa-current` left bar is the
sole USWDS-conventional exception).

## Typography
- Body/UI: "Source Sans Pro Web", system fallbacks. Line-height 1.55.
- Display (hero/page h1): "Merriweather Web", Georgia, serif.
- Mono: "Roboto Mono Web" — ONLY for actual code, SHA-256 digests, and verbatim
  regulatory/source text. Never decorative.
- Body measure 65–75ch. Obvious scale steps between h1/h2/h3 at every breakpoint;
  display capped well under 6rem (current clamp max 3rem). No kickers that rob the
  heading of standalone meaning — headings must stand independently.

## Spacing & layout
- Tight groupings, generous separation: related controls cluster; sections separate
  with clearly larger gaps. More space above headings than below.
- App shell: sidebar (sticky, own scroll) + `minmax(0,1fr)` content column. Prose
  keeps 65–75ch; two-pane comparisons and data tables may use full width.
- Touch targets ≥44×44px (menu button, drawer close, all tap targets).

## Components
- USWDS patterns first (Button, Table, Alert-style notices already in globals.css).
- Every interactive element has hover, focus-visible, disabled, loading, error, and
  empty states; keyboard operable; visible focus ring never clipped.
- Error copy names the problem and the recovery path ("The X request returned status
  N." + retry affordance where applicable).

## Motion (GSAP; purposeful only)
- Tokens: `DUR = {fast:.15, base:.22, slow:.3}`, `EASE = "power2.out"`, `STAGGER = .05`.
- Budget: page entrance 220ms fade/8px rise; overview card stagger 50ms steps;
  count-up 600ms; claim-highlight pulse 300ms background fade from `--soft-blue`.
- Exits faster than entrances. Transform/opacity only (plus the pulse's background
  fade). No scroll-jacking, no parallax, no ScrollTrigger, no layout-driving
  property animation.
- Everything inside `gsap.matchMedia().add("(prefers-reduced-motion: no-preference)")`;
  DOM authored in final state so reduced-motion users and raw static HTML see the
  finished layout with zero animation.

# RegLens-31 Front-End Design

## System

The front end is a Next.js static export built with USWDS 3 through
`@trussworks/react-uswds`. The interface uses USWDS primitives and the shared
custom-property palette; it does not introduce a separate design language.

The application uses a multi-route shell with a persistent desktop sidebar and
an accessible mobile navigation drawer. Each route provides a focused task
view within the same shell.

## Color

The core design tokens are:

| Token | Value | Use |
|---|---|---|
| `--ink` | `#172b3a` | Body text |
| `--muted-ink` | `#465b69` | Secondary text |
| `--navy` | `#153651` | Sidebar and page-heading accents |
| `--navy-deep` | `#0b273d` | Header, footer, and mobile overlay |
| `--blue` | `#005ea8` | Links, current indicators, and focus accents |
| `--blue-dark` | `#00477f` | Link hover and active states |
| `--canvas` | `#f4f7f9` | Page background |
| `--surface` | `#ffffff` | Cards, panes, and tables |
| `--line` | `#b8c7d1` | Structural borders and dividers |
| `--soft-blue` | `#e7f2fa` | Selection, highlight, and pulse fills |
| `--gold` | `#ffbe2e` | Header, footer, disclaimer, and focus accents |

USWDS utilities and component-specific styles supply secondary neutral,
categorical, and error colors. The interface does not use red/green treatment
to imply regulatory validity, risk, acceptance, or repeal priority, consistent
with the "Framing constraints" in `../docs/OGC01-ALIGNMENT.md`. Accepted and
rejected counts use the same neutral treatment. Obligation-type badges use
categorical hues, and runtime errors use the conventional error palette.

Body text maintains at least 4.5:1 contrast and large text at least 3:1.
Structural dividers are 1px. Controls and error notices may use 2px borders;
the 4px `usa-current` navigation bar is the USWDS current-item indicator. The
design does not use gradient text, glass effects, or blur effects.

## Typography

- Body and interface text use "Source Sans Pro Web" with system fallbacks and
  a 1.55 line height.
- Hero and page-level headings use "Merriweather Web" with Georgia and serif
  fallbacks. Responsive page headings do not exceed 3.25rem.
- "Roboto Mono Web" is limited to code, SHA-256 digests, and verbatim
  regulatory or source text.
- Prose measures approximately 65–75 characters. Heading levels use visibly
  distinct sizes, and each heading has standalone meaning.

## Spacing and layout

- Related controls remain grouped; larger gaps separate sections. Headings
  receive more space above than below.
- The desktop shell uses a sticky, independently scrolling sidebar and a
  `minmax(0, 1fr)` content column. At the mobile breakpoint, the sidebar
  becomes a focus-trapped drawer and the content expands to one column.
- Prose remains within the standard reading measure. Two-pane comparisons and
  data tables may use the available content width.
- Menu controls, drawer controls, navigation links, and other tap targets are
  at least 44px by 44px.

## Components and states

- USWDS `Button`, `Table`, and `Alert` components provide the base patterns.
  Shared application components cover tabs, document selection, expandable
  groups, glossary definitions, metric cards, highlights, and text diffs.
- Data-backed views define visible loading, error, and empty states.
- Interactive controls are keyboard operable and expose state through native
  semantics or ARIA attributes. Focus indicators remain visible and unclipped.
- Error messages identify the failed request or resource and provide a
  recovery action when retry is possible.

## Motion

- Motion tokens are `DUR = { fast: 0.15, base: 0.22, slow: 0.3 }`,
  `EASE = "power2.out"`, and `STAGGER = 0.05`.
- Route entrances use a 220ms opacity transition with an 8px rise. Overview
  cards use a 220ms opacity transition with a 12px rise and 50ms stagger.
  Count-up motion lasts 600ms, and a located claim receives a 300ms background
  pulse from `--soft-blue`.
- Movement uses transforms and opacity; the claim pulse changes only the
  background color. The design excludes scroll-jacking, parallax,
  `ScrollTrigger`, and layout-property animation.
- Route and card motion runs inside `gsap.matchMedia()` for
  `prefers-reduced-motion: no-preference`. Count-up and pulse helpers return
  without animation when reduced motion is requested. The DOM is authored in
  its final state so reduced-motion users and static HTML receive the complete
  layout.

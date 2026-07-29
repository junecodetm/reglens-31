import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const WEB_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "web");

function read(relativePath) {
  const absolutePath = join(WEB_ROOT, relativePath);
  assert.ok(existsSync(absolutePath), `${relativePath} should exist`);
  return readFileSync(absolutePath, "utf8");
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

test("static export uses directory-style route output", () => {
  const config = read("next.config.mjs");

  assert.match(config, /output:\s*["']export["']/);
  assert.match(config, /trailingSlash:\s*true/);
});

test("the layout mounts the shared shell chrome in document order", () => {
  const layout = read("app/layout.tsx");
  const skipLink = layout.indexOf('className="skip-link"');
  const disclaimer = layout.indexOf("<DisclaimerBand");
  const shell = layout.indexOf("<AppShell");
  const footer = layout.indexOf("<SiteFooter");

  assert.ok(skipLink >= 0, "layout should render the skip link");
  assert.ok(disclaimer > skipLink, "disclaimer should follow the skip link");
  assert.ok(shell > disclaimer, "app shell should follow the disclaimer");
  assert.ok(footer > shell, "site footer should follow the app shell");
});

test("AppShell and Sidebar expose the requested navigation semantics", () => {
  const appShell = read("app/components/shell/AppShell.tsx");
  const sidebar = read("app/components/shell/Sidebar.tsx");
  const expectedRoutes = [
    "/",
    "/extraction/claims",
    "/extraction/rejected",
    "/explore/search",
    "/explore/browse",
    "/explore/cross-references",
    "/ogc01/authority",
    "/ogc01/grounding",
    "/ogc01/drafts",
    "/evaluation",
    "/evaluation/ogc01",
    "/about",
  ];

  assert.match(appShell, /className="app-shell"/);
  assert.match(appShell, /<Sidebar\s*\/>/);
  assert.match(appShell, /<main id="main-content" className="app-content" tabIndex=\{-1\}>/);

  assert.equal(
    sidebar.match(/<nav\b/g)?.length,
    1,
    "Sidebar should author exactly one nav element",
  );
  assert.match(sidebar, /aria-label="Primary"/);
  assert.match(sidebar, /usePathname\(\)/);
  assert.match(sidebar, /usa-sidenav/);
  assert.match(sidebar, /usa-sidenav__item/);
  assert.match(sidebar, /usa-current/);
  assert.match(sidebar, /aria-current/);
  assert.match(sidebar, /aria-expanded=\{isOpen\}/);
  assert.match(sidebar, /aria-controls=/);
  assert.match(sidebar, /event\.key === "Escape"/);
  assert.match(sidebar, /\.focus\(\)/);
  assert.match(sidebar, /closeButtonRef\.current\?\.focus\(\)/);
  assert.match(sidebar, /event\.key === "Tab"/);
  assert.match(sidebar, /drawerRef\.current\?\.querySelectorAll/);

  for (const route of expectedRoutes) {
    assert.ok(
      sidebar.includes(`href: "${route}"`),
      `Sidebar should include ${route}`,
    );
  }
});

test("the shared footer preserves the overview attribution copy", () => {
  const footer = read("app/components/shell/SiteFooter.tsx");
  const types = read("app/components/reglens-types.ts");

  assert.match(footer, /DISCLAIMER_TEXT/);
  assert.match(types, /Independent personal research prototype\. Not affiliated with/);
  assert.match(
    footer,
    /Use-case framing: Treasury AI Use Case Inventory \(U\.S\. Government work\) — see About this demonstration\./,
  );
  assert.match(footer, /Source data: Federal Register \(U\.S\. public domain\)\./);
  assert.match(footer, /Source code &amp; methodology/);
});

test("the route template animates only when reduced motion is not requested", () => {
  const template = read("app/template.tsx");
  const tokens = read("app/motion/tokens.ts");

  assert.match(tokens, /fast:\s*0\.15/);
  assert.match(tokens, /base:\s*0\.22/);
  assert.match(tokens, /slow:\s*0\.3/);
  assert.match(tokens, /EASE = "power2\.out"/);
  assert.match(tokens, /STAGGER = 0\.05/);
  assert.match(template, /gsap\.registerPlugin\(useGSAP\)/);
  assert.match(
    template,
    /prefers-reduced-motion:\s*no-preference/,
  );
  assert.match(template, /gsap\.from\(ref\.current/);
  assert.match(template, /autoAlpha:\s*0/);
  assert.match(template, /y:\s*8/);
  assert.match(template, /duration:\s*DUR\.base/);
  assert.match(template, /ease:\s*EASE/);
  assert.match(template, /clearProps:\s*"all"/);
});

test("all eleven route pages mount their existing section tool", () => {
  const routes = [
    ["app/about/page.tsx", "About this demonstration", "AboutSection", false],
    [
      "app/extraction/claims/page.tsx",
      "Extracted obligations",
      "ClaimsExplorer",
      false,
    ],
    [
      "app/extraction/rejected/page.tsx",
      "Rejected claims",
      "RejectedClaimsExplorer",
      false,
    ],
    [
      "app/explore/search/page.tsx",
      "Search the ingested corpus",
      "SearchSection",
      false,
    ],
    [
      "app/explore/browse/page.tsx",
      "Browse Title 31 (ingested parts)",
      "BrowseSection",
      true,
    ],
    [
      "app/explore/cross-references/page.tsx",
      "Authority cross-references",
      "CrossRefSection",
      true,
    ],
    [
      "app/ogc01/authority/page.tsx",
      "Statutory authority",
      "AuthoritySection",
      true,
    ],
    [
      "app/ogc01/grounding/page.tsx",
      "Statutory grounding signal (two-sided)",
      "GroundingSection",
      true,
    ],
    [
      "app/ogc01/drafts/page.tsx",
      "Draft rule skeletons",
      "DraftsSection",
      true,
    ],
    [
      "app/evaluation/page.tsx",
      "Evaluation — honest, provisional",
      "EvalSection",
      true,
    ],
    [
      "app/evaluation/ogc01/page.tsx",
      "Evaluation — authority, grounding, and drafts (provisional)",
      "Ogc01EvalSection",
      true,
    ],
  ];

  for (const [path, title, component, active] of routes) {
    const source = read(path);

    assert.doesNotMatch(source, /^"use client";/);
    assert.match(
      source,
      new RegExp(`title:\\s*"${escapeRegExp(title)} — RegLens-31"`),
      `${path} should export its tool metadata title`,
    );
    assert.match(
      source,
      new RegExp(`<PageHeader\\s+title="${escapeRegExp(title)}"`),
      `${path} should mount its existing heading in PageHeader`,
    );
    assert.ok(
      source.includes(`<${component}${active ? " active" : ""} />`),
      `${path} should mount ${component}${active ? " active" : ""}`,
    );
  }
});

test("only existing constant section intros are reused as route ledes", () => {
  const introContracts = [
    [
      "app/components/SearchSection.tsx",
      "SEARCH_INTRO",
      "app/explore/search/page.tsx",
    ],
    [
      "app/components/BrowseSection.tsx",
      "BROWSE_INTRO",
      "app/explore/browse/page.tsx",
    ],
    [
      "app/components/CrossRefSection.tsx",
      "CROSS_REF_INTRO",
      "app/explore/cross-references/page.tsx",
    ],
  ];

  for (const [componentPath, constantName, routePath] of introContracts) {
    const component = read(componentPath);
    const route = read(routePath);

    assert.ok(
      component.includes(`export const ${constantName}`),
      `${constantName} should be referenceable without duplicating prose`,
    );
    assert.ok(
      route.includes(`lede={${constantName}}`),
      `${routePath} should reuse ${constantName}`,
    );
  }
});

test("ClaimsExplorer preserves the overview bootstrap and lazy source flow", () => {
  const explorer = read("app/extraction/claims/ClaimsExplorer.tsx");

  assert.match(explorer, /^"use client";/);
  assert.match(explorer, /fetchData<SiteData>\("\/data\/site\.json"/);
  assert.match(
    explorer,
    /fetchData<DocumentExtraction\[\]>\(\s*"\/data\/claims\.json"/,
  );
  assert.match(explorer, /new AbortController\(\)/);
  assert.match(
    explorer,
    /`\/data\/documents\/\$\{encodeURIComponent\(documentNumber\)\}\.txt`/,
  );
  assert.match(explorer, /sourceCacheRef/);
  assert.match(explorer, /className="two-pane-grid"/);
  assert.match(explorer, /<ClaimsPane/);
  assert.match(explorer, /selectedClaimId=\{selectedClaim\?\.claim_id \?\? null\}/);
  assert.match(explorer, /onSelectClaim=\{setSelectedClaim\}/);
  assert.match(explorer, /<SourcePane/);
  assert.match(explorer, /selectedClaim=\{selectedClaim\}/);
  assert.match(explorer, /sourceState=\{sourceState\}/);
  assert.doesNotMatch(explorer, /RejectedClaims/);
});

test("the rejected route lazily supplies both required data props", () => {
  const explorer = read(
    "app/extraction/rejected/RejectedClaimsExplorer.tsx",
  );

  assert.match(explorer, /^"use client";/);
  assert.match(explorer, /useLazyJson<SiteData>\("\/data\/site\.json"/);
  assert.match(
    explorer,
    /useLazyJson<DocumentExtraction\[\]>\("\/data\/claims\.json"/,
  );
  assert.match(explorer, /void loadSite\(\)/);
  assert.match(explorer, /void loadDocuments\(\)/);
  assert.match(explorer, /<RejectedClaims/);
  assert.match(explorer, /documents=\{documentsState\.data\}/);
  assert.match(explorer, /rejectedCount=\{siteState\.data\.rejected_count\}/);
});

test("the appended shell CSS is responsive, accessible, and palette-only", () => {
  const css = read("app/globals.css");
  const marker = "/* WP2 app shell */";
  const shellCss = css.slice(css.indexOf(marker));

  assert.ok(shellCss.startsWith(marker), "WP2 styles should be appended");
  assert.match(
    shellCss,
    /\.app-shell\s*\{[\s\S]*?display:\s*grid;[\s\S]*?grid-template-columns:\s*auto minmax\(0,\s*1fr\);/,
  );
  assert.match(
    shellCss,
    /\.app-content\s*\{[\s\S]*?min-width:\s*0;[\s\S]*?max-width:\s*none;[\s\S]*?padding:/,
  );
  assert.match(
    shellCss,
    /\.sidebar\s*\{[\s\S]*?position:\s*sticky;[\s\S]*?top:\s*0;[\s\S]*?overflow-y:\s*auto;/,
  );
  assert.match(
    shellCss,
    /\.sidebar-group-label\s*\{[\s\S]*?letter-spacing:[\s\S]*?color:\s*var\(--muted-ink\);/,
  );
  assert.match(
    shellCss,
    /\.sidebar \.usa-sidenav a\.usa-current[\s\S]*?\{[\s\S]*?border-left:\s*4px solid var\(--blue\);/,
  );
  assert.match(
    shellCss,
    /\.page-header-lede\s*\{[\s\S]*?max-width:\s*70ch;/,
  );
  assert.match(shellCss, /@media \(min-width:\s*64em\)/);
  assert.match(shellCss, /@media \(max-width:\s*63\.99em\)/);
  assert.match(
    shellCss,
    /\.sidebar-menu-button,[\s\S]*?\.sidebar-close-button\s*\{[\s\S]*?min-width:\s*2\.75rem;[\s\S]*?min-height:\s*2\.75rem;/,
  );
  assert.match(
    shellCss,
    /\.app-content \.app-shell\s*\{[\s\S]*?display:\s*flex;/,
  );
  assert.doesNotMatch(
    shellCss,
    /#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/i,
    "new shell styles should use the existing custom-property palette",
  );
});

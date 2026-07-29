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
    "/obligations",
    "/authorities",
    "/drafts",
    "/evaluation",
    "/sources",
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
  // The attribution's "About this demonstration" is a live link to /about.
  assert.match(
    footer,
    /Use-case framing: Treasury AI Use Case Inventory \(U\.S\. Government work\) — see /,
  );
  assert.match(
    footer,
    /<Link href="\/about">About this demonstration<\/Link>/,
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
  // opacity, not autoAlpha: visibility:hidden would defeat h1 focus on nav.
  assert.match(template, /opacity:\s*0/);
  assert.match(template, /y:\s*8/);
  assert.match(template, /duration:\s*DUR\.base/);
  assert.match(template, /ease:\s*EASE/);
  assert.match(template, /clearProps:\s*"all"/);
});

test("all seven route pages mount their existing section tool", () => {
  const singleComponentRoutes = [
    ["app/about/page.tsx", "About this demonstration", "AboutSection", false],
    [
      "app/obligations/page.tsx",
      "Extracted obligations",
      "ObligationsExplorer",
      false,
    ],
    ["app/drafts/page.tsx", "Draft rule skeletons", "DraftsSection", true],
  ];

  for (const [path, title, component, active] of singleComponentRoutes) {
    const source = read(path);
    const componentProps = active ? " active standalone" : " standalone";

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
      source.includes(`<${component}${componentProps} />`),
      `${path} should mount ${component}${componentProps}`,
    );
  }

  const tabbedRoutes = [
    [
      "app/authorities/page.tsx",
      "Statutory authority",
      ["AuthoritySection", "CrossRefSection", "GroundingSection"],
    ],
    [
      "app/evaluation/page.tsx",
      "Evaluation (provisional)",
      ["EvalSection", "Ogc01EvalSection"],
    ],
    [
      "app/sources/page.tsx",
      "Search & browse the corpus",
      ["SearchSection", "BrowseSection"],
    ],
  ];

  for (const [path, title, components] of tabbedRoutes) {
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
    assert.match(source, /<ViewTabs\b/, `${path} should mount ViewTabs`);
    for (const component of components) {
      assert.ok(
        source.includes(`<${component} `),
        `${path} should mount ${component} inside its tabs`,
      );
    }
  }
});

test("ObligationsExplorer preserves the bootstrap, lazy source flow, and rejected-details lazy load", () => {
  const explorer = read("app/obligations/ObligationsExplorer.tsx");

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
  assert.match(explorer, /<DocumentPicker/);
  assert.match(explorer, /<SourcePane/);
  assert.match(explorer, /<RejectedDetailPane/);
  assert.match(
    explorer,
    /useLazyJson<RejectedDetailsData>\("\/data\/rejected-details\.json"\)/,
  );
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
    /\.sidebar \.usa-sidenav a\.usa-current[\s\S]*?\{[\s\S]*?border-left:\s*4px solid var\(--blue\);/,
  );
  assert.match(shellCss, /@media \(min-width:\s*64em\)/);
  assert.match(shellCss, /@media \(max-width:\s*63\.99em\)/);
  assert.match(
    shellCss,
    /\.sidebar-menu-button,[\s\S]*?\.sidebar-close-button\s*\{[\s\S]*?min-width:\s*2\.75rem;[\s\S]*?min-height:\s*2\.75rem;/,
  );
  assert.doesNotMatch(
    shellCss,
    /#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(/i,
    "new shell styles should use the existing custom-property palette",
  );
});

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

interface NavigationItem {
  label: string;
  href: string;
}

interface NavigationGroup {
  label: string;
  items: NavigationItem[];
}

const OVERVIEW_ITEM: NavigationItem = {
  label: "Overview",
  href: "/",
};

const NAVIGATION_GROUPS: NavigationGroup[] = [
  {
    label: "EXTRACTION",
    items: [
      { label: "Claims & sources", href: "/extraction/claims" },
      { label: "Rejected claims", href: "/extraction/rejected" },
    ],
  },
  {
    label: "EXPLORE",
    items: [
      { label: "Corpus search", href: "/explore/search" },
      { label: "Browse Title 31", href: "/explore/browse" },
      {
        label: "Authority cross-references",
        href: "/explore/cross-references",
      },
    ],
  },
  {
    label: "OGC-01 MODULES",
    items: [
      { label: "Authority citations", href: "/ogc01/authority" },
      { label: "Grounding markers", href: "/ogc01/grounding" },
      { label: "Draft skeletons", href: "/ogc01/drafts" },
    ],
  },
  {
    label: "EVALUATION",
    items: [
      { label: "Core metrics", href: "/evaluation" },
      { label: "OGC-01 modules", href: "/evaluation/ogc01" },
    ],
  },
];

const ABOUT_ITEM: NavigationItem = {
  label: "About this demonstration",
  href: "/about",
};

function normalizePathname(pathname: string): string {
  if (pathname === "/") {
    return pathname;
  }

  return pathname.replace(/\/+$/, "");
}

interface NavigationListProps {
  items: NavigationItem[];
  pathname: string;
}

function NavigationList({ items, pathname }: NavigationListProps) {
  const normalizedPathname = normalizePathname(pathname);

  return (
    <ul className="usa-sidenav">
      {items.map((item) => {
        const isCurrent =
          normalizedPathname === normalizePathname(item.href);

        return (
          <li className="usa-sidenav__item" key={item.href}>
            <Link
              className={isCurrent ? "usa-current" : undefined}
              href={item.href}
              aria-current={isCurrent ? "page" : undefined}
            >
              {item.label}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);
  const previousPathnameRef = useRef(pathname);

  useEffect(() => {
    if (previousPathnameRef.current === pathname) {
      return;
    }

    previousPathnameRef.current = pathname;

    if (isOpen) {
      setIsOpen(false);
      menuButtonRef.current?.focus();
    }
  }, [isOpen, pathname]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    closeButtonRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
        menuButtonRef.current?.focus();
        return;
      }

      if (
        event.key === "Tab" &&
        window.matchMedia("(max-width: 63.99em)").matches
      ) {
        const focusableElements =
          drawerRef.current?.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
          );

        if (!focusableElements?.length || !drawerRef.current) {
          return;
        }

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        const activeElement = document.activeElement;

        if (!drawerRef.current.contains(activeElement)) {
          event.preventDefault();
          (event.shiftKey ? lastElement : firstElement).focus();
        } else if (event.shiftKey && activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        } else if (!event.shiftKey && activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    }

    document.addEventListener("keydown", handleKeyDown);

    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  function closeDrawer({ returnFocus = false } = {}) {
    setIsOpen(false);

    if (returnFocus) {
      menuButtonRef.current?.focus();
    }
  }

  return (
    <aside className="sidebar">
      <button
        ref={menuButtonRef}
        className="sidebar-menu-button"
        type="button"
        aria-expanded={isOpen}
        aria-controls="primary-navigation-drawer"
        onClick={() => setIsOpen(true)}
      >
        Menu
      </button>

      <div
        className={`sidebar-overlay${isOpen ? " is-open" : ""}`}
        onClick={(event) => {
          if (event.currentTarget === event.target) {
            closeDrawer({ returnFocus: true });
          }
        }}
      >
        <div
          ref={drawerRef}
          id="primary-navigation-drawer"
          className="sidebar-drawer"
        >
          <div className="sidebar-drawer-header">
            <span className="sidebar-drawer-title">RegLens-31</span>
            <button
              ref={closeButtonRef}
              className="sidebar-close-button"
              type="button"
              aria-label="Close menu"
              onClick={() => closeDrawer({ returnFocus: true })}
            >
              Close
            </button>
          </div>

          <nav aria-label="Primary">
            <NavigationList items={[OVERVIEW_ITEM]} pathname={pathname} />

            {NAVIGATION_GROUPS.map((group) => (
              <div className="sidebar-group" key={group.label}>
                <span className="sidebar-group-label">{group.label}</span>
                <NavigationList items={group.items} pathname={pathname} />
              </div>
            ))}

            <NavigationList items={[ABOUT_ITEM]} pathname={pathname} />
          </nav>
        </div>
      </div>
    </aside>
  );
}

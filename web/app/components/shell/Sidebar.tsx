"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

interface NavigationItem {
  label: string;
  href: string;
}

const NAVIGATION_ITEMS: NavigationItem[] = [
  { label: "Overview", href: "/" },
  { label: "Extracted obligations", href: "/obligations" },
  { label: "Statutory authority", href: "/authorities" },
  { label: "Draft skeletons", href: "/drafts" },
  { label: "Evaluation", href: "/evaluation" },
  { label: "Search & browse", href: "/sources" },
  { label: "About & provenance", href: "/about" },
];

function normalizePathname(pathname: string): string {
  if (pathname === "/") {
    return pathname;
  }

  return pathname.replace(/\/+$/, "");
}

interface NavigationListProps {
  items: NavigationItem[];
  pathname: string;
  onNavigate: () => void;
}

function NavigationList({ items, pathname, onNavigate }: NavigationListProps) {
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
              onClick={onNavigate}
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

  // While the mobile drawer is open, the page behind it must be inert for
  // assistive tech (the keyboard focus trap alone doesn't stop the virtual
  // cursor). The drawer only ever opens on mobile; on desktop isOpen stays
  // false and this never fires.
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const main = document.getElementById("main-content");
    main?.setAttribute("inert", "");

    return () => main?.removeAttribute("inert");
  }, [isOpen]);

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
          role={isOpen ? "dialog" : undefined}
          aria-modal={isOpen ? "true" : undefined}
          aria-label={isOpen ? "Primary navigation" : undefined}
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
            <NavigationList items={NAVIGATION_ITEMS} pathname={pathname} onNavigate={() => setIsOpen(false)} />
          </nav>
        </div>
      </div>
    </aside>
  );
}

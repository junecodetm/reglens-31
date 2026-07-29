"use client";

import {
  type KeyboardEvent,
  type ReactNode,
  useEffect,
  useRef,
  useState,
} from "react";

export interface ViewTab {
  id: string;
  label: string;
  panel: ReactNode;
}

interface ViewTabsProps {
  tabs: ViewTab[];
  defaultTabId: string;
  ariaLabel: string;
}

type TabNavigationKey =
  | "ArrowRight"
  | "ArrowLeft"
  | "ArrowDown"
  | "ArrowUp"
  | "Home"
  | "End";

const TAB_NAVIGATION_KEYS: readonly TabNavigationKey[] = [
  "ArrowRight",
  "ArrowLeft",
  "ArrowDown",
  "ArrowUp",
  "Home",
  "End",
];

export function nextTabIndex(
  currentIndex: number,
  key: TabNavigationKey,
  tabCount: number,
): number {
  if (key === "Home") {
    return 0;
  }

  if (key === "End") {
    return tabCount - 1;
  }

  const direction =
    key === "ArrowRight" || key === "ArrowDown" ? 1 : -1;

  return (currentIndex + direction + tabCount) % tabCount;
}

export function ViewTabs({
  tabs,
  defaultTabId,
  ariaLabel,
}: ViewTabsProps) {
  const [selectedTabId, setSelectedTabId] = useState(defaultTabId);
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  useEffect(() => {
    const selectFromHash = () => {
      const hashTabId = window.location.hash.slice(1);
      const nextTabId = tabs.some((tab) => tab.id === hashTabId)
        ? hashTabId
        : defaultTabId;

      setSelectedTabId(nextTabId);
    };

    selectFromHash();
    window.addEventListener("hashchange", selectFromHash);

    return () =>
      window.removeEventListener("hashchange", selectFromHash);
  }, [defaultTabId, tabs]);

  function activateTab(tab: ViewTab): void {
    setSelectedTabId(tab.id);
    window.location.hash = tab.id;
  }

  function handleKeyDown(
    event: KeyboardEvent<HTMLButtonElement>,
    currentIndex: number,
  ): void {
    if (!TAB_NAVIGATION_KEYS.includes(event.key as TabNavigationKey)) {
      return;
    }

    event.preventDefault();
    const nextIndex = nextTabIndex(
      currentIndex,
      event.key as TabNavigationKey,
      tabs.length,
    );
    const nextTab = tabs[nextIndex];

    activateTab(nextTab);
    tabRefs.current[nextIndex]?.focus();
  }

  return (
    <div className="view-tabs">
      <div
        className="view-tabs-list"
        role="tablist"
        aria-label={ariaLabel}
      >
        {tabs.map((tab, index) => {
          const isSelected = tab.id === selectedTabId;
          const tabId = `view-tab-${tab.id}`;
          const panelId = `view-tab-panel-${tab.id}`;

          return (
            <button
              key={tab.id}
              ref={(element) => {
                tabRefs.current[index] = element;
              }}
              type="button"
              role="tab"
              className="view-tab"
              aria-selected={isSelected}
              aria-controls={panelId}
              id={tabId}
              tabIndex={isSelected ? 0 : -1}
              onClick={() => activateTab(tab)}
              onKeyDown={(event) => handleKeyDown(event, index)}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {tabs.map((tab) => {
        const isSelected = tab.id === selectedTabId;
        const tabId = `view-tab-${tab.id}`;
        const panelId = `view-tab-panel-${tab.id}`;

        return (
          <div
            key={tab.id}
            role="tabpanel"
            className="view-tab-panel"
            id={panelId}
            aria-labelledby={tabId}
            hidden={!isSelected}
            tabIndex={0}
          >
            {tab.panel}
          </div>
        );
      })}
    </div>
  );
}

"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

export type LazyJsonState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; data: T }
  | { status: "error"; message: string };

export interface UseLazyJsonResult<T> {
  state: LazyJsonState<T>;
  load: () => void;
}

interface LazyJsonEntry<T> {
  path: string;
  state: LazyJsonState<T>;
}

interface ActiveJsonRequest {
  path: string;
  controller: AbortController;
}

export function useLazyJson<T>(
  path: string,
): UseLazyJsonResult<T> {
  const [entry, setEntry] = useState<LazyJsonEntry<T>>({
    path,
    state: { status: "idle" },
  });
  const requestedPathRef = useRef<string | null>(null);
  const controllerRef = useRef<ActiveJsonRequest | null>(null);
  const observedPathRef = useRef(path);

  useEffect(() => {
    if (observedPathRef.current === path) {
      return;
    }

    observedPathRef.current = path;
    const activeRequest = controllerRef.current;

    if (activeRequest && activeRequest.path !== path) {
      activeRequest.controller.abort();
      controllerRef.current = null;
    }

    if (requestedPathRef.current !== path) {
      requestedPathRef.current = null;
    }

    setEntry((current) =>
      current.path === path
        ? current
        : { path, state: { status: "idle" } },
    );
  }, [path]);

  const load = useCallback(() => {
    if (requestedPathRef.current === path) {
      return;
    }

    const activeRequest = controllerRef.current;

    if (activeRequest && activeRequest.path !== path) {
      activeRequest.controller.abort();
    }

    requestedPathRef.current = path;
    const controller = new AbortController();
    controllerRef.current = { path, controller };
    setEntry({ path, state: { status: "loading" } });

    void (async () => {
      try {
        const response = await fetch(path, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            `The JSON request returned status ${response.status}.`,
          );
        }

        const data = (await response.json()) as T;

        if (
          !controller.signal.aborted &&
          requestedPathRef.current === path
        ) {
          setEntry({
            path,
            state: { status: "ready", data },
          });
        }
      } catch (error: unknown) {
        if (
          !controller.signal.aborted &&
          requestedPathRef.current === path
        ) {
          requestedPathRef.current = null;
          setEntry({
            path,
            state: {
              status: "error",
              message:
                error instanceof Error
                  ? error.message
                  : "The JSON data could not be loaded.",
            },
          });
        }
      } finally {
        if (controllerRef.current?.controller === controller) {
          controllerRef.current = null;
        }
      }
    })();
  }, [path]);

  useEffect(() => {
    const activeRequest = controllerRef.current;

    if (
      activeRequest?.path === path &&
      activeRequest.controller.signal.aborted &&
      requestedPathRef.current === path
    ) {
      // Strict Mode replays passive effects after their cleanup. Restart the
      // aborted first-open request without firing onFirstOpen a second time.
      requestedPathRef.current = null;
      load();
    }

    return () => {
      if (controllerRef.current?.path === path) {
        controllerRef.current.controller.abort();
      }
    };
  }, [load, path]);

  const state =
    entry.path === path
      ? entry.state
      : ({ status: "idle" } as const);

  return { state, load };
}

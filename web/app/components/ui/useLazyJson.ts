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
  load: () => Promise<T | null>;
}

export interface UseLazyJsonOptions {
  requestErrorPrefix?: string;
  fallbackErrorMessage?: string;
}

interface LazyJsonEntry<T> {
  path: string;
  state: LazyJsonState<T>;
}

interface ActiveJsonRequest {
  path: string;
  controller: AbortController;
}

interface SharedJsonPromise<T> {
  path: string;
  promise: Promise<T | null>;
}

export function useLazyJson<T>(
  path: string,
  {
    requestErrorPrefix = "The JSON request returned status ",
    fallbackErrorMessage = "The JSON data could not be loaded.",
  }: UseLazyJsonOptions = {},
): UseLazyJsonResult<T> {
  const [entry, setEntry] = useState<LazyJsonEntry<T>>({
    path,
    state: { status: "idle" },
  });
  const requestedPathRef = useRef<string | null>(null);
  const controllerRef = useRef<ActiveJsonRequest | null>(null);
  const promiseRef = useRef<SharedJsonPromise<T> | null>(null);
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

    if (promiseRef.current && promiseRef.current.path !== path) {
      promiseRef.current = null;
    }

    setEntry((current) =>
      current.path === path
        ? current
        : { path, state: { status: "idle" } },
    );
  }, [path]);

  const load = useCallback((): Promise<T | null> => {
    // Callers issued while a request is in flight (or after success) share
    // the same promise, so a second submit is never silently dropped.
    if (promiseRef.current?.path === path) {
      return promiseRef.current.promise;
    }

    const activeRequest = controllerRef.current;

    if (activeRequest && activeRequest.path !== path) {
      activeRequest.controller.abort();
    }

    requestedPathRef.current = path;
    const controller = new AbortController();
    controllerRef.current = { path, controller };
    setEntry({ path, state: { status: "loading" } });

    const promise = (async (): Promise<T | null> => {
      try {
        const response = await fetch(path, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`${requestErrorPrefix}${response.status}.`);
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
          return data;
        }
      } catch (error: unknown) {
        if (
          !controller.signal.aborted &&
          requestedPathRef.current === path
        ) {
          requestedPathRef.current = null;
          // A failed request must not stay cached, or retry would replay it.
          if (promiseRef.current?.path === path) {
            promiseRef.current = null;
          }
          setEntry({
            path,
            state: {
              status: "error",
              message:
                error instanceof Error
                  ? error.message
                  : fallbackErrorMessage,
            },
          });
        }
      } finally {
        if (controllerRef.current?.controller === controller) {
          controllerRef.current = null;
        }
      }

      return null;
    })();

    promiseRef.current = { path, promise };
    return promise;
  }, [fallbackErrorMessage, path, requestErrorPrefix]);

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
      promiseRef.current = null;
      void load();
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

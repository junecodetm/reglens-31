"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";

export type TextKey = string | number;

export type LazyTextState<Key extends TextKey = TextKey> =
  | { status: "idle" }
  | { status: "loading"; key: Key }
  | { status: "ready"; key: Key; text: string }
  | { status: "error"; key: Key; message: string };

export interface UseLazyTextOptions {
  requestErrorPrefix?: string;
  fallbackErrorMessage?: string;
}

export interface UseLazyTextResult<Key extends TextKey> {
  state: LazyTextState<Key>;
  load: (key: Key, path: string) => Promise<string | null>;
  reset: () => void;
}

export interface UseLazyTextMapResult<Key extends TextKey> {
  stateFor: (key: Key) => LazyTextState<Key>;
  load: (key: Key, path: string) => Promise<string | null>;
}

interface TextResponse {
  ok: boolean;
  status: number;
  text: () => Promise<string>;
}

export type TextFetch = (
  path: string,
  init: { signal: AbortSignal },
) => Promise<TextResponse>;

export interface CreateTextLoaderOptions extends UseLazyTextOptions {
  fetch: TextFetch;
}

export interface TextLoadOptions {
  abortPrevious?: boolean;
}

export interface TextLoader<Key extends TextKey> {
  stateFor: (key: Key) => LazyTextState<Key>;
  load: (
    key: Key,
    path: string,
    options?: TextLoadOptions,
  ) => Promise<string | null>;
  subscribe: (listener: () => void) => () => void;
  getSnapshot: () => number;
  abort: (key: Key) => void;
  abortAll: () => void;
}

interface CachedText {
  path: string;
  text: string;
}

interface ActiveTextRequest {
  path: string;
  controller: AbortController;
  promise: Promise<string | null>;
}

const IDLE_TEXT_STATE = { status: "idle" } as const;

export function createTextLoader<Key extends TextKey = TextKey>({
  fetch: fetchText,
  requestErrorPrefix = "The text request returned status ",
  fallbackErrorMessage = "The text could not be loaded.",
}: CreateTextLoaderOptions): TextLoader<Key> {
  const cache = new Map<Key, CachedText>();
  const states = new Map<Key, LazyTextState<Key>>();
  const requests = new Map<Key, ActiveTextRequest>();
  const listeners = new Set<() => void>();
  let revision = 0;

  function stateFor(key: Key): LazyTextState<Key> {
    return states.get(key) ?? IDLE_TEXT_STATE;
  }

  function publish(state: Exclude<LazyTextState<Key>, { status: "idle" }>) {
    states.set(state.key, state);
    revision += 1;

    for (const listener of [...listeners]) {
      listener();
    }
  }

  function abort(key: Key): void {
    const request = requests.get(key);

    if (request === undefined) {
      return;
    }

    requests.delete(key);
    request.controller.abort();
  }

  function abortAll(): void {
    for (const key of [...requests.keys()]) {
      abort(key);
    }
  }

  function load(
    key: Key,
    path: string,
    { abortPrevious = false }: TextLoadOptions = {},
  ): Promise<string | null> {
    if (abortPrevious) {
      for (const requestKey of [...requests.keys()]) {
        if (requestKey !== key) {
          abort(requestKey);
        }
      }
    }

    const pendingRequest = requests.get(key);

    if (
      pendingRequest !== undefined &&
      pendingRequest.path === path
    ) {
      return pendingRequest.promise;
    }

    if (pendingRequest !== undefined) {
      abort(key);
    }

    const cached = cache.get(key);

    if (cached !== undefined && cached.path === path) {
      publish({ status: "ready", key, text: cached.text });
      return Promise.resolve(cached.text);
    }

    const controller = new AbortController();
    let settleRequest!: (value: string | null) => void;
    const promise = new Promise<string | null>((resolve) => {
      settleRequest = resolve;
    });
    const request: ActiveTextRequest = {
      path,
      controller,
      promise,
    };

    requests.set(key, request);
    publish({ status: "loading", key });

    if (
      controller.signal.aborted ||
      requests.get(key) !== request
    ) {
      settleRequest(null);
      return promise;
    }

    const execution = (async (): Promise<string | null> => {
      try {
        const response = await fetchText(path, {
          signal: controller.signal,
        });

        if (
          controller.signal.aborted ||
          requests.get(key) !== request
        ) {
          return null;
        }

        if (!response.ok) {
          throw new Error(`${requestErrorPrefix}${response.status}.`);
        }

        const text = await response.text();

        if (
          controller.signal.aborted ||
          requests.get(key) !== request
        ) {
          return null;
        }

        cache.set(key, { path, text });
        publish({ status: "ready", key, text });
        return text;
      } catch (error: unknown) {
        if (
          !controller.signal.aborted &&
          requests.get(key) === request
        ) {
          publish({
            status: "error",
            key,
            message:
              error instanceof Error
                ? error.message
                : fallbackErrorMessage,
          });
        }

        return null;
      } finally {
        if (requests.get(key) === request) {
          requests.delete(key);
        }
      }
    })();

    void execution.then(settleRequest, () => {
      settleRequest(null);
    });
    return promise;
  }

  return {
    stateFor,
    load,
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    getSnapshot() {
      return revision;
    },
    abort,
    abortAll,
  };
}

function useTextLoader<Key extends TextKey>(
  options: UseLazyTextOptions,
): TextLoader<Key> {
  const loaderRef = useRef<TextLoader<Key> | null>(null);

  if (loaderRef.current === null) {
    loaderRef.current = createTextLoader<Key>({
      fetch,
      ...options,
    });
  }

  const loader = loaderRef.current;

  useEffect(() => {
    return () => {
      loader.abortAll();
    };
  }, [loader]);

  return loader;
}

export function useLazyText<Key extends TextKey = TextKey>(
  options: UseLazyTextOptions = {},
): UseLazyTextResult<Key> {
  const loader = useTextLoader<Key>(options);
  const [activeKey, setActiveKey] = useState<Key | null>(null);

  useSyncExternalStore(
    loader.subscribe,
    loader.getSnapshot,
    loader.getSnapshot,
  );

  const load = useCallback(
    (key: Key, path: string): Promise<string | null> => {
      setActiveKey(key);
      return loader.load(key, path, { abortPrevious: true });
    },
    [loader],
  );

  const reset = useCallback(() => {
    loader.abortAll();
    setActiveKey(null);
  }, [loader]);

  const state =
    activeKey === null ? IDLE_TEXT_STATE : loader.stateFor(activeKey);

  return { state, load, reset };
}

export function useLazyTextMap<Key extends TextKey = TextKey>(
  options: UseLazyTextOptions = {},
): UseLazyTextMapResult<Key> {
  const loader = useTextLoader<Key>(options);

  useSyncExternalStore(
    loader.subscribe,
    loader.getSnapshot,
    loader.getSnapshot,
  );

  const stateFor = useCallback(
    (key: Key): LazyTextState<Key> => loader.stateFor(key),
    [loader],
  );
  const load = useCallback(
    (key: Key, path: string): Promise<string | null> =>
      loader.load(key, path),
    [loader],
  );

  return { stateFor, load };
}

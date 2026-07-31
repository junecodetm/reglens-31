import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire, registerHooks } from "node:module";
import test from "node:test";

const requireFromWeb = createRequire(
  new URL("../web/package.json", import.meta.url),
);
const ts = requireFromWeb("typescript");

registerHooks({
  load(url, context, nextLoad) {
    if (!url.endsWith(".ts") && !url.endsWith(".tsx")) {
      return nextLoad(url, context);
    }

    const source = readFileSync(new URL(url), "utf8");
    const output = ts.transpileModule(source, {
      compilerOptions: {
        jsx: ts.JsxEmit.ReactJSX,
        module: ts.ModuleKind.ESNext,
        target: ts.ScriptTarget.ES2022,
      },
      fileName: new URL(url).pathname,
    });

    return {
      format: "module",
      shortCircuit: true,
      source: output.outputText,
    };
  },
});

const { createTextLoader } = await import(
  "../web/app/components/ui/useLazyText.ts"
);

interface Deferred<T> {
  promise: Promise<T>;
  resolve: (value: T) => void;
}

function deferred<T>(): Deferred<T> {
  let resolve: ((value: T) => void) | undefined;
  const promise = new Promise<T>((promiseResolve) => {
    resolve = promiseResolve;
  });

  if (resolve === undefined) {
    throw new Error("Deferred promise resolver was not initialized.");
  }

  return { promise, resolve };
}

function response(text: string, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => text,
  };
}

test("a cached key emits ready synchronously without loading or a second fetch", async () => {
  let fetchCount = 0;
  const loader = createTextLoader<string>({
    fetch: async () => {
      fetchCount += 1;
      return response("cached text");
    },
  });
  const states: Array<ReturnType<typeof loader.stateFor>> = [];
  loader.subscribe(() => {
    states.push(loader.stateFor("part-1"));
  });

  await loader.load("part-1", "/parts/1.txt", {
    abortPrevious: true,
  });
  assert.equal(fetchCount, 1);

  states.length = 0;
  const cachedLoad = loader.load("part-1", "/parts/1.txt", {
    abortPrevious: true,
  });

  assert.deepEqual(states, [
    {
      status: "ready",
      key: "part-1",
      text: "cached text",
    },
  ]);
  assert.equal(fetchCount, 1);
  assert.equal(await cachedLoad, "cached text");
});

test("switching keys in single-selection mode aborts the prior request", async () => {
  const requests = [
    deferred<ReturnType<typeof response>>(),
    deferred<ReturnType<typeof response>>(),
  ];
  const signals: AbortSignal[] = [];
  let requestIndex = 0;
  const loader = createTextLoader<string>({
    fetch: (_path, { signal }) => {
      signals.push(signal);
      const request = requests[requestIndex];
      requestIndex += 1;
      return request.promise;
    },
  });

  const firstLoad = loader.load("first", "/first.txt", {
    abortPrevious: true,
  });
  const secondLoad = loader.load("second", "/second.txt", {
    abortPrevious: true,
  });

  assert.equal(signals.length, 2);
  assert.equal(signals[0].aborted, true);
  assert.equal(signals[1].aborted, false);

  requests[0].resolve(response("stale"));
  requests[1].resolve(response("current"));
  assert.equal(await firstLoad, null);
  assert.equal(await secondLoad, "current");
});

test("a non-ok response uses the exact configured status prefix", async () => {
  const loader = createTextLoader<string>({
    fetch: async () => response("", 503),
    requestErrorPrefix: "Text endpoint returned status ",
  });

  assert.equal(
    await loader.load("failure", "/failure.txt"),
    null,
  );
  assert.deepEqual(loader.stateFor("failure"), {
    status: "error",
    key: "failure",
    message: "Text endpoint returned status 503.",
  });
});

test("a response arriving after abort never commits state", async () => {
  const pendingResponse = deferred<ReturnType<typeof response>>();
  const loader = createTextLoader<string>({
    fetch: () => pendingResponse.promise,
  });
  const states: Array<ReturnType<typeof loader.stateFor>> = [];
  loader.subscribe(() => {
    states.push(loader.stateFor("aborted"));
  });

  const load = loader.load("aborted", "/aborted.txt");
  loader.abort("aborted");
  const statesBeforeResponse = [...states];

  pendingResponse.resolve(response("too late"));
  assert.equal(await load, null);
  assert.deepEqual(states, statesBeforeResponse);
  assert.notEqual(loader.stateFor("aborted").status, "ready");
});

test("a synchronous fetch failure publishes an error and remains retryable", async () => {
  let fetchCount = 0;
  const loader = createTextLoader<string>({
    fetch: () => {
      fetchCount += 1;

      if (fetchCount === 1) {
        throw new Error("Synchronous fetch failure.");
      }

      return Promise.resolve(response("recovered"));
    },
  });

  assert.equal(await loader.load("retry", "/retry.txt"), null);
  assert.deepEqual(loader.stateFor("retry"), {
    status: "error",
    key: "retry",
    message: "Synchronous fetch failure.",
  });

  assert.equal(
    await loader.load("retry", "/retry.txt"),
    "recovered",
  );
  assert.equal(fetchCount, 2);
});

test("a same-key load from a synchronous subscriber joins the pending request", async () => {
  const pendingResponse = deferred<ReturnType<typeof response>>();
  let fetchCount = 0;
  const loader = createTextLoader<string>({
    fetch: () => {
      fetchCount += 1;
      return pendingResponse.promise;
    },
  });
  let nestedLoad: Promise<string | null> | null = null;

  const unsubscribe = loader.subscribe(() => {
    if (
      nestedLoad === null &&
      loader.stateFor("shared").status === "loading"
    ) {
      nestedLoad = loader.load("shared", "/shared.txt");
    }
  });

  const firstLoad = loader.load("shared", "/shared.txt");
  unsubscribe();

  assert.equal(fetchCount, 1);
  if (nestedLoad === null) {
    throw new Error("The loading subscriber did not issue its load.");
  }
  assert.strictEqual(nestedLoad, firstLoad);

  pendingResponse.resolve(response("shared text"));
  assert.equal(await firstLoad, "shared text");
  assert.equal(await nestedLoad, "shared text");
});

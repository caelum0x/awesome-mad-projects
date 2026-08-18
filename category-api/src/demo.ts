/**
 * demo.ts
 * -------
 * End-to-end demonstration: compose typed handlers into endpoints with
 * `compose`/`pipe`, register them on the tiny `Router`, and run a couple of
 * example requests. Also shows the Result functor (validation middleware)
 * and the Result => Maybe natural transformation in a real request path.
 *
 * Run with `npm run demo` (after `npm run build`).
 */

import { Ctx, Handler, ctx, compose } from "./category";
import { Result, ok, err, isOk, resultFmap } from "./functor";
import { resultToMaybe, Maybe } from "./natural";
import { Router, Request, Response } from "./router";

// ---------------------------------------------------------------------------
// Domain types (objects in the category)
// ---------------------------------------------------------------------------

interface GreetInput {
  readonly name: string;
}
interface Greeting {
  readonly greeting: string;
}

// ---------------------------------------------------------------------------
// Handlers (morphisms), composed into an endpoint.
// ---------------------------------------------------------------------------

/** Parse+validate the raw request body into a typed GreetInput. */
const parseGreet: Handler<Request, Result<string, GreetInput>> = (c) => {
  const body = c.value.body as { name?: unknown };
  if (typeof body?.name !== "string" || body.name.trim() === "") {
    return ctx(err<string, GreetInput>("field 'name' is required"), c.meta);
  }
  return ctx(ok<string, GreetInput>({ name: body.name.trim() }), c.meta);
};

/**
 * Business logic lifted OVER the Result functor with `resultFmap`.
 * `resultFmap(buildGreeting)` is `F(f)`: it runs only on success and
 * short-circuits on validation error -- middleware behaviour for free.
 */
const buildGreeting = (input: GreetInput): Greeting => ({
  greeting: `Hello, ${input.name}!`,
});

const greetLogic: Handler<Result<string, GreetInput>, Result<string, Greeting>> = (
  c,
) =>
  ctx(resultFmap<string, GreetInput, Greeting>(buildGreeting)(c.value), {
    ...c.meta,
    step: "greetLogic",
  });

/** Turn a Result into an HTTP response context. */
const toResponse: Handler<Result<string, Greeting>, Response> = (c) => {
  const r = c.value;
  if (isOk(r)) {
    return ctx<Response>({ status: 200, body: r.value }, { ...c.meta, ok: true });
  }
  return ctx<Response>(
    { status: 400, body: { error: r.error } },
    { ...c.meta, ok: false },
  );
};

/**
 * The endpoint is literally a composition of morphisms:
 *   toResponse . greetLogic . parseGreet
 * Built with `compose` (right-to-left), exactly the category operator.
 */
const greetEndpoint: Handler<Request, Response> = compose(
  toResponse,
  compose(greetLogic, parseGreet),
);

// ---------------------------------------------------------------------------
// Router wiring
// ---------------------------------------------------------------------------

const router = Router.create().register("POST", "/greet", greetEndpoint);

// ---------------------------------------------------------------------------
// Run example requests
// ---------------------------------------------------------------------------

function show(label: string, req: Request, res: Ctx<Response>): void {
  console.log(`\n> ${label}`);
  console.log(`  request : ${req.method} ${req.path} ${JSON.stringify(req.body)}`);
  console.log(`  response: ${res.value.status} ${JSON.stringify(res.value.body)}`);
  console.log(`  meta    : ${JSON.stringify(res.meta)}`);
}

function main(): void {
  console.log("=== Category-Theory API: end-to-end demo ===");

  const good: Request = { method: "POST", path: "/greet", body: { name: "Ada" } };
  const bad: Request = { method: "POST", path: "/greet", body: { name: "" } };
  const missing: Request = { method: "GET", path: "/nope", body: null };

  show("valid request (endpoint = compose of 3 handlers)", good, router.handle(good));
  show("invalid request (Result short-circuits via functor)", bad, router.handle(bad));
  show("unmatched route (router returns 404)", missing, router.handle(missing));

  // Natural transformation in action: collapse the validated Result into a
  // Maybe, discarding the specific error. Same result whichever way you go
  // around the naturality square (see laws.ts for the proof).
  console.log("\n> natural transformation Result => Maybe (drop error detail)");
  const parsedGood = parseGreet(ctx(good, {})).value;
  const parsedBad = parseGreet(ctx(bad, {})).value;
  const asMaybeGood: Maybe<GreetInput> = resultToMaybe(parsedGood);
  const asMaybeBad: Maybe<GreetInput> = resultToMaybe(parsedBad);
  console.log(`  ok  Result -> Maybe: ${JSON.stringify(asMaybeGood)}`);
  console.log(`  err Result -> Maybe: ${JSON.stringify(asMaybeBad)}`);

  console.log("\nDone.");
}

main();

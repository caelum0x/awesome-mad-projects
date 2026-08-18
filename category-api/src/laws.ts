/**
 * laws.ts
 * -------
 * Executable proofs-by-testing of the category-theory laws this project
 * claims to satisfy. Run with `npm test` (after `npm run build`).
 *
 * We use lightweight property-based testing: for each law we generate many
 * random inputs and assert the law holds on every one. If any case fails the
 * process exits non-zero, so this doubles as a CI gate.
 *
 * Laws checked:
 *   A. Category    -- left identity, right identity, associativity of compose.
 *   B. Functor     -- identity + composition preservation, for Result and WithLog.
 *   C. Naturality  -- the Result => Maybe naturality square commutes.
 */

import { Ctx, Handler, ctx, id, compose } from "./category";
import {
  Result,
  ok,
  err,
  resultFmap,
  WithLog,
  withLog,
  logFmap,
  eqResult,
  eqWithLog,
} from "./functor";
import {
  Maybe,
  maybeFmap,
  resultToMaybe,
  eqMaybe,
} from "./natural";

// ---------------------------------------------------------------------------
// Minimal test + property harness
// ---------------------------------------------------------------------------

let passed = 0;
let failed = 0;
const failures: string[] = [];

function check(name: string, condition: boolean): void {
  if (condition) {
    passed++;
    console.log(`  ok  - ${name}`);
  } else {
    failed++;
    failures.push(name);
    console.log(`  FAIL- ${name}`);
  }
}

const RUNS = 200;

/** Deterministic-ish pseudo random so failures are reproducible per run. */
let seed = 0x2f6e2b1;
function rand(): number {
  // xorshift32
  seed ^= seed << 13;
  seed ^= seed >>> 17;
  seed ^= seed << 5;
  return ((seed >>> 0) % 100000) / 100000;
}
function randInt(lo: number, hi: number): number {
  return lo + Math.floor(rand() * (hi - lo + 1));
}

/** Run `body` over RUNS random samples; `check` once with the AND of results. */
function forAll(name: string, body: () => boolean): void {
  let allOk = true;
  for (let i = 0; i < RUNS; i++) {
    if (!body()) {
      allOk = false;
      break;
    }
  }
  check(`${name}  (x${RUNS} random cases)`, allOk);
}

// ---------------------------------------------------------------------------
// Sample morphisms over Ctx<number> / Ctx<string>, used for category laws.
// Each is pure and returns a fresh context.
// ---------------------------------------------------------------------------

const inc: Handler<number, number> = (c) =>
  ctx(c.value + 1, { ...c.meta, step: "inc" });
const dbl: Handler<number, number> = (c) =>
  ctx(c.value * 2, { ...c.meta, step: "dbl" });
const toStr: Handler<number, string> = (c) =>
  ctx(`n=${c.value}`, { ...c.meta, step: "toStr" });
const shout: Handler<string, string> = (c) =>
  ctx(c.value.toUpperCase() + "!", { ...c.meta, step: "shout" });

/** Structural equality of contexts (value + meta). */
function eqCtx<A>(x: Ctx<A>, y: Ctx<A>): boolean {
  if (!Object.is(x.value, y.value)) return false;
  const kx = Object.keys(x.meta).sort();
  const ky = Object.keys(y.meta).sort();
  if (kx.length !== ky.length) return false;
  return kx.every((k, i) => k === ky[i] && x.meta[k] === y.meta[k]);
}

// ===========================================================================
// A. CATEGORY LAWS
// ===========================================================================

function categoryLaws(): void {
  console.log("\nA. Category laws (Ctx objects, Handler morphisms)");

  // Left identity:  id . f = f
  forAll("left identity: compose(id, f) = f", () => {
    const x = randInt(-50, 50);
    const input = ctx(x, { origin: "test" });
    const f = inc;
    const lhs = compose(id<number>(), f)(input);
    const rhs = f(input);
    return eqCtx(lhs, rhs);
  });

  // Right identity: f . id = f
  forAll("right identity: compose(f, id) = f", () => {
    const x = randInt(-50, 50);
    const input = ctx(x, { origin: "test" });
    const f = dbl;
    const lhs = compose(f, id<number>())(input);
    const rhs = f(input);
    return eqCtx(lhs, rhs);
  });

  // Associativity: (h . g) . f = h . (g . f)
  // f: number->number, g: number->string, h: string->string
  forAll("associativity: compose(compose(h,g),f) = compose(h,compose(g,f))", () => {
    const x = randInt(-50, 50);
    const input = ctx(x, { origin: "test" });
    const f: Handler<number, number> = inc;
    const g: Handler<number, string> = toStr;
    const h: Handler<string, string> = shout;
    const left = compose(compose(h, g), f)(input);
    const right = compose(h, compose(g, f))(input);
    return eqCtx(left, right);
  });
}

// ===========================================================================
// B. FUNCTOR LAWS
// ===========================================================================

function functorLaws(): void {
  console.log("\nB. Functor laws");

  // ---- Result<string, _> ------------------------------------------------
  console.log("  Functor: Result<string, _>");

  const gen = (): Result<string, number> =>
    rand() < 0.5 ? ok(randInt(-20, 20)) : err(`e${randInt(0, 9)}`);

  const f = (n: number) => n + 3;
  const g = (n: number) => n * 5;

  // F(id) = id
  forAll("Result: fmap(id) = id", () => {
    const r = gen();
    const mapped = resultFmap((x: number) => x)(r);
    return eqResult(mapped, r);
  });

  // F(g . f) = F(g) . F(f)
  forAll("Result: fmap(g . f) = fmap(g) . fmap(f)", () => {
    const r = gen();
    const lhs = resultFmap((x: number) => g(f(x)))(r);
    const rhs = resultFmap(g)(resultFmap(f)(r));
    return eqResult(lhs, rhs);
  });

  // ---- WithLog (Writer) --------------------------------------------------
  console.log("  Functor: WithLog<_>");

  const genLog = (): WithLog<number> =>
    withLog(randInt(-20, 20), [`log${randInt(0, 5)}`, `log${randInt(0, 5)}`]);

  // F(id) = id
  forAll("WithLog: fmap(id) = id", () => {
    const w = genLog();
    const mapped = logFmap((x: number) => x)(w);
    return eqWithLog(mapped, w);
  });

  // F(g . f) = F(g) . F(f)
  forAll("WithLog: fmap(g . f) = fmap(g) . fmap(f)", () => {
    const w = genLog();
    const lhs = logFmap((x: number) => g(f(x)))(w);
    const rhs = logFmap(g)(logFmap(f)(w));
    return eqWithLog(lhs, rhs);
  });
}

// ===========================================================================
// C. NATURALITY LAW
// ===========================================================================

function naturalityLaw(): void {
  console.log("\nC. Naturality: Result<E,_> => Maybe<_>");

  const gen = (): Result<string, number> =>
    rand() < 0.5 ? ok(randInt(-20, 20)) : err(`e${randInt(0, 9)}`);

  const f = (n: number) => `v(${n * 2 + 1})`; // number -> string morphism

  // maybeFmap(f) . alpha = alpha . resultFmap(f)
  forAll("naturality square commutes", () => {
    const r = gen();
    // path 1: transform then forget-error
    const path1: Maybe<string> = maybeFmap(f)(resultToMaybe(r));
    // path 2: forget-error then transform
    const path2: Maybe<string> = resultToMaybe(resultFmap(f)(r));
    return eqMaybe(path1, path2);
  });
}

// ===========================================================================
// Runner
// ===========================================================================

function main(): void {
  console.log("=== Category-Theory API: law tests ===");
  categoryLaws();
  functorLaws();
  naturalityLaw();

  console.log(`\n----------------------------------------`);
  console.log(`Total: ${passed} passed, ${failed} failed`);
  if (failed > 0) {
    console.log(`Failed checks: ${failures.join(", ")}`);
    process.exit(1);
  }
  console.log("All category / functor / naturality laws hold. ✔");
}

main();

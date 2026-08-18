![Category-Theory API Layer](./banner.png)

# Category-Theory API Layer (TypeScript)

> An HTTP/handler pipeline modeled as a category — with the identity, associativity, functor, and naturality laws actually property-tested, not just asserted in prose.

A small, **self-contained, runnable** prototype that treats a request/response
pipeline as a **category**, its middleware as **functors**, and error-forgetting
as a **natural transformation** — and then *enforces the relevant laws* with
property-based tests that exit non-zero on any failure. No runtime dependencies;
the only dev dependency is TypeScript (+ `@types/node`).

**Concept / reference.** Category theory studies structures made of *objects* and
*morphisms* (arrows) that compose associatively and have identities. Typed
functional programming has long borrowed the vocabulary — `Functor`, natural
transformation, `Kleisli` — because a language of pure functions is close to a
category (**Set** / **Type**: types as objects, functions as morphisms). This
project makes that correspondence concrete for a web-handler layer and then holds
itself accountable to the definitions.

---

## TL;DR

- An **endpoint is literally a composition of morphisms**:
  `compose(toResponse, compose(greetLogic, parseGreet))`.
- **Middleware is a functor.** Validation is business logic lifted *over* the
  `Result` functor with `resultFmap`, which gives short-circuit-on-error behavior
  for free (`F(f)` runs on `ok`, is skipped on `err`).
- **Eight laws are executable.** `npm test` runs 200 randomized cases per law for
  category identity/associativity, functor identity/composition (two functors),
  and the `Result ⇒ Maybe` naturality square — exiting non-zero if any fail, so it
  doubles as a CI gate.
- An explicit **"exact vs. metaphorical"** section states precisely which claims
  are theorems, which are modeling choices, and which are just a useful lens.
- Run it: `npm install && npm run build && npm test && npm run demo` (or
  `npm start`).

---

## The idea

If handlers are pure functions from one typed context to another, then wiring
handlers together is *function composition* — and function composition is
associative and has an identity. That is the definition of a category. So instead
of treating "compose two middlewares" as an ad-hoc utility, this codebase names
the structure and checks that it behaves:

| Category theory          | This codebase                                             |
| ------------------------ | -------------------------------------------------------- |
| Object                   | a context type `Ctx<A>` (payload `A` + immutable meta)   |
| Morphism `A -> B`        | a pure handler `Handler<A,B> = (Ctx<A>) => Ctx<B>`       |
| Identity `id_A`          | `id<A>()`                                                |
| Composition `g ∘ f`      | `compose(g, f)` — mathematical order, "g after f"        |
| Endofunctor `F`          | `Result<E,_>` and `WithLog<_>` with their `fmap`         |
| Natural transformation   | `resultToMaybe : Result<E,_> ⇒ Maybe<_>`                 |
| Endpoint                 | a composition of handlers registered on a `Router`       |

Middleware that can fail (validation) is expressed by lifting business logic over
the `Result` functor. Because `resultFmap(f)` applies `f` only on the success
branch, a validation failure short-circuits the rest of the pipeline
automatically — no explicit `if (error) return` threading required.

---

## The honest core: the LAWS, property-tested

All laws live in `src/laws.ts` and run under a ~40-line property harness: a
reproducible **xorshift32** PRNG generates `RUNS = 200` random inputs per law, and
each law is asserted on every sample. If any case fails, the process prints the
failing check and calls `process.exit(1)`.

Morphism equality is tested **extensionally** — two morphisms are considered equal
when they agree on sampled inputs — via structural equality helpers `eqCtx`,
`eqResult`, `eqWithLog`, `eqMaybe`.

### A. Category laws — objects `Ctx`, morphisms `Handler`

Sample morphisms over `Ctx<number>` / `Ctx<string>`: `inc`, `dbl`, `toStr`,
`shout` (each pure, each returning a fresh context).

| Law            | Statement                                            |
| -------------- | ---------------------------------------------------- |
| Left identity  | `compose(id, f) = f`                                 |
| Right identity | `compose(f, id) = f`                                 |
| Associativity  | `compose(compose(h, g), f) = compose(h, compose(g, f))` |

Associativity is checked across a type-changing chain
`f : number→number`, `g : number→string`, `h : string→string`, so it genuinely
exercises composition, not just endomorphisms of one type.

### B. Functor laws — two concrete endofunctors

For a functor `F`, `fmap` must preserve identities and composition:

| Law                    | Statement                             |
| ---------------------- | ------------------------------------- |
| Identity preserved     | `fmap(id) = id`                       |
| Composition preserved  | `fmap(g ∘ f) = fmap(g) ∘ fmap(f)`     |

Both laws are checked for **`Result<string, _>`** (`resultFmap`, an Either-style
success/failure wrapper — models fallible middleware) and **`WithLog<_>`**
(`logFmap`, a Writer-style logger threading an immutable log — models logging
middleware). Random samples mix `ok`/`err` and non-empty logs.

### C. Naturality — `alpha = resultToMaybe : Result<E,_> ⇒ Maybe<_>`

`alpha` forgets the error payload: `ok a ↦ just a`, `err e ↦ nothing`. A
transformation is **natural** when, for every morphism `f : A → B`, the naturality
square commutes:

```
        Result<E,A>  --alpha_A-->  Maybe<A>
            |                          |
     resultFmap(f)               maybeFmap(f)
            v                          v
        Result<E,B>  --alpha_B-->  Maybe<B>

   maybeFmap(f) ∘ alpha_A  ==  alpha_B ∘ resultFmap(f)
```

Practically: it does not matter whether you transform the value first and then
discard the error, or discard the error first and then transform — you land on the
same `Maybe`. The test samples both `ok` and `err` values against a
number→string morphism and asserts the two paths are equal.

### Why these hold

`compose` is plain function composition, so category identity and associativity
hold *by construction* — the tests are demonstrations on random data, not the
source of truth. `resultToMaybe` is a **single polymorphic function**, uniform in
`A` with no per-type special-casing; parametricity is exactly the condition that
forces naturality, which is why the square commutes.

---

## Honesty: exact vs. metaphorical

This is the part most "category theory in FP" write-ups skip. Here is precisely
what is a theorem, what is a modeling choice, and what is only a lens.

- **Exact.** `id`/`compose` genuinely satisfy the category laws for these pure
  handlers — proven by construction (plain composition) and demonstrated by the
  tests. `resultFmap`, `logFmap`, `maybeFmap` are honest functor maps satisfying
  both functor laws. `resultToMaybe` is a genuine natural transformation: it is
  parametric in `A`, so naturality is forced and the square commutes in the tests.
- **Exact-but-value-level.** The functors act on *values* (`A ↦ Result<E, A>`)
  rather than on the arbitrary `Ctx`-morphisms of the base category. They are
  endofunctors on **Set** / **Type** (types + functions), the standard setting for
  "functor" in typed FP. We *bridge* that into the handler pipeline by wrapping
  payloads in `Ctx` (e.g. `Handler<Request, Result<string, GreetInput>>`). That
  bridge is a modeling choice, not a theorem.
- **Metaphorical / not enforced.** Property tests sample finitely many inputs;
  they raise confidence, they are not proofs. `Ctx.meta` is an untyped bag, so
  "objects" are really `(payload type, loose meta)`. Morphism equality is tested
  extensionally on samples, not proven intensionally. We do **not** model monoidal
  structure, monads (no `Kleisli` composition laws are tested), or
  size/foundational issues. "Middleware = endofunctor" is a useful lens, not a
  claim that every middleware you could write is functorial.

---

## How it works

### Module map

| Module            | Responsibility                                                                 |
| ----------------- | ------------------------------------------------------------------------------ |
| `src/category.ts` | `Ctx<A>`, `Handler<A,B>`, `ctx`, `id`, `compose`, `pipe` — the base category   |
| `src/functor.ts`  | `Result`/`Either` + `resultFmap`; `WithLog`/`Writer` + `logFmap`; equality helpers |
| `src/natural.ts`  | `Maybe` + `maybeFmap`; the `resultToMaybe` natural transformation              |
| `src/router.ts`   | tiny **immutable** router — an endpoint is a composed handler                   |
| `src/demo.ts`     | end-to-end example requests through a real composed endpoint                    |
| `src/laws.ts`     | the executable law tests (`npm test`) — must pass                              |

### Key types & functions

```ts
// category.ts — objects and morphisms
interface Ctx<A> { readonly value: A; readonly meta: Readonly<Record<string, unknown>>; }
type Handler<A, B> = (input: Ctx<A>) => Ctx<B>;
function id<A>(): Handler<A, A>;                                   // identity morphism
function compose<A, B, C>(g: Handler<B, C>, f: Handler<A, B>): Handler<A, C>;  // g after f
function pipe<A>(...handlers: Handler<any, any>[]): Handler<A, any>;           // left-to-right sugar

// functor.ts — two endofunctors
type Result<E, A> = { tag: "ok"; value: A } | { tag: "err"; error: E };
function resultFmap<E, A, B>(f: (a: A) => B): (r: Result<E, A>) => Result<E, B>;
interface WithLog<A> { readonly value: A; readonly log: ReadonlyArray<string>; }
function logFmap<A, B>(f: (a: A) => B): (w: WithLog<A>) => WithLog<B>;

// natural.ts — the natural transformation
type Maybe<A> = { tag: "just"; value: A } | { tag: "nothing" };
function maybeFmap<A, B>(f: (a: A) => B): (m: Maybe<A>) => Maybe<B>;
function resultToMaybe<E, A>(r: Result<E, A>): Maybe<A>;          // ok a ↦ just a, err e ↦ nothing

// router.ts — immutable dispatch
type Endpoint = Handler<Request, Response>;
class Router { static create(): Router; register(m, p, e): Router; handle(req): Ctx<Response>; }
```

`pipe` is defined purely in terms of `compose` and `id`
(`handlers.reduce((acc, h) => compose(h, acc), id())`), so it inherits their laws
for free. `Router.register` returns a **new** router rather than mutating in place,
keeping the immutability invariant end to end.

### The endpoint, concretely (from `demo.ts`)

```ts
const greetEndpoint: Handler<Request, Response> = compose(
  toResponse,                          // Result<string, Greeting> -> Response
  compose(greetLogic, parseGreet),     // Request -> Result<string, Greeting>
);
//  parseGreet : Request                       -> Result<string, GreetInput>   (validate)
//  greetLogic : Result<string, GreetInput>    -> Result<string, Greeting>     (resultFmap over business logic)
//  toResponse : Result<string, Greeting>      -> Response                     (200 on ok, 400 on err)
```

`greetLogic` is the functor lift in action: `resultFmap(buildGreeting)` applies
the pure `buildGreeting` only when validation succeeded, so an invalid request
flows through untouched and surfaces as a `400` at `toResponse`.

---

## Install & run

Requires Node 18+ (developed on Node 24). **No runtime dependencies.**

```bash
npm install        # dev-only: typescript + @types/node
npm run build      # tsc -> dist/ (also emits .d.ts declarations)
npm test           # runs the law tests (exits non-zero on ANY failure)
npm run demo       # runs the end-to-end request demo
# or all three in order:
npm start          # build && test && demo
```

### Captured output — law tests (`npm test`)

```
=== Category-Theory API: law tests ===

A. Category laws (Ctx objects, Handler morphisms)
  ok  - left identity: compose(id, f) = f  (x200 random cases)
  ok  - right identity: compose(f, id) = f  (x200 random cases)
  ok  - associativity: compose(compose(h,g),f) = compose(h,compose(g,f))  (x200 random cases)

B. Functor laws
  Functor: Result<string, _>
  ok  - Result: fmap(id) = id  (x200 random cases)
  ok  - Result: fmap(g . f) = fmap(g) . fmap(f)  (x200 random cases)
  Functor: WithLog<_>
  ok  - WithLog: fmap(id) = id  (x200 random cases)
  ok  - WithLog: fmap(g . f) = fmap(g) . fmap(f)  (x200 random cases)

C. Naturality: Result<E,_> => Maybe<_>
  ok  - naturality square commutes  (x200 random cases)

----------------------------------------
Total: 8 passed, 0 failed
All category / functor / naturality laws hold. ✔
```

### Captured output — demo (`npm run demo`)

```
=== Category-Theory API: end-to-end demo ===

> valid request (endpoint = compose of 3 handlers)
  request : POST /greet {"name":"Ada"}
  response: 200 {"greeting":"Hello, Ada!"}
  meta    : {"matched":true,"step":"greetLogic","ok":true}

> invalid request (Result short-circuits via functor)
  request : POST /greet {"name":""}
  response: 400 {"error":"field 'name' is required"}
  meta    : {"matched":true,"step":"greetLogic","ok":false}

> unmatched route (router returns 404)
  request : GET /nope null
  response: 404 {"error":"No route for GET /nope"}
  meta    : {"matched":false}

> natural transformation Result => Maybe (drop error detail)
  ok  Result -> Maybe: {"tag":"just","value":{"name":"Ada"}}
  err Result -> Maybe: {"tag":"nothing"}

Done.
```

The demo shows the theory doing real work: the invalid request's `400` is produced
purely by `resultFmap` skipping `buildGreeting` on the `err` branch (note
`"ok":false` in meta), and the final two lines show `resultToMaybe` collapsing a
validated `Result` into a `Maybe`, discarding the error detail — the same natural
transformation whose square is proven in the tests.

---

## Testing

`npm test` compiles to `dist/laws.js` and runs it. What each block verifies:

| Block | What it checks | Cases |
| ----- | -------------- | ----- |
| A. Category | `compose` has left & right identities and is associative across a type-changing `number → number → string → string` chain | 3 laws × 200 |
| B. Functor  | `resultFmap` and `logFmap` each preserve `id` and composition, over mixed `ok`/`err` and non-empty-log samples | 4 laws × 200 |
| C. Naturality | `maybeFmap(f) ∘ resultToMaybe == resultToMaybe ∘ resultFmap(f)` for both `ok` and `err` inputs | 1 law × 200 |

Properties of the harness:

- **Reproducible.** The xorshift32 PRNG is seeded (`0x2f6e2b1`), so a given build
  runs the same 200 samples each time; failures are reproducible.
- **CI-ready.** Any failing case flips the exit code to `1` and lists the failing
  check names, so `npm test` gates a pipeline.
- **Extensional equality.** Morphisms/functor values are compared with structural
  helpers (`eqCtx`, `eqResult`, `eqWithLog`, `eqMaybe`) on sampled inputs.

---

## Limitations & honest caveats

- **Property tests are not proofs.** 200 samples per law raise confidence; they do
  not certify the laws for all inputs. (For `compose` the law also holds by
  construction, but that is reasoning outside the test.)
- **Value-level functors.** The functors are endofunctors on **Type**, bridged
  into the handler pipeline by wrapping payloads in `Ctx`. The bridge is a modeling
  choice, not a categorical theorem.
- **Loose objects.** `Ctx.meta` is `Record<string, unknown>`, so "objects" are
  `(payload type, untyped meta bag)`; the category is only as precise as that meta
  is disciplined.
- **No monads / Kleisli.** No monadic composition laws, no monoidal structure, no
  adjunctions — deliberately out of scope.
- **`pipe` is loosely typed.** Its variadic form uses `Handler<any, any>[]`
  internally; type safety is recovered at the pairwise call sites, not inside
  `pipe`.
- **Toy router.** `Router` does exact method+path matching only — no params, no
  wildcards, no query parsing. It exists to show an endpoint is a composed
  morphism, not to be a web framework.

---

## References

- Saunders Mac Lane, *Categories for the Working Mathematician* — categories,
  functors, natural transformations (the naturality square).
- Bartosz Milewski, *Category Theory for Programmers* — the **Type**/**Set**
  reading of functors and natural transformations used here.
- The `Functor` / natural-transformation vocabulary from typed FP (Haskell's
  `Functor`, `fmap`, and `Maybe`/`Either`), reproduced structurally in TypeScript.

## License

MIT

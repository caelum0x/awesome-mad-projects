# Category-Theory API Layer (TypeScript)

A small, **self-contained, runnable** prototype that models an HTTP/handler
layer as a **category** and then *actually enforces* the relevant laws with
property-based tests. No runtime dependencies; the only dev dependency is
TypeScript (+ `@types/node`).

## Concept

We treat the request/response pipeline as a category:

| Category theory        | This codebase                                             |
| ---------------------- | -------------------------------------------------------- |
| Object                 | A context type `Ctx<A>` (payload `A` plus immutable meta)|
| Morphism `A -> B`      | A pure handler `Handler<A,B> = (Ctx<A>) => Ctx<B>`       |
| Identity `id_A`        | `id<A>()`                                                |
| Composition `g ∘ f`    | `compose(g, f)` (mathematical order: "g after f")        |
| Endofunctor `F`        | `Result<E,_>` and `WithLog<_>` with their `fmap`         |
| Natural transformation | `resultToMaybe : Result<E,_> ⇒ Maybe<_>`                 |
| Endpoint               | a composition of handlers registered on a `Router`       |

An **endpoint is literally a composition of morphisms**. In `demo.ts`:

```ts
const greetEndpoint = compose(toResponse, compose(greetLogic, parseGreet));
```

Middleware that can fail (validation) is expressed by lifting business logic
*over* the `Result` functor with `resultFmap`, which gives short-circuit-on-error
behaviour for free (`F(f)` is applied on `ok`, skipped on `err`).

## What the laws mean here, and how they are enforced

All laws are checked in `src/laws.ts` using lightweight property testing
(200 random cases per law; reproducible xorshift PRNG). `npm test` exits
non-zero if any law fails, so it works as a CI gate.

**A. Category laws** (objects = `Ctx`, morphisms = `Handler`)
- Left identity:  `compose(id, f) = f`
- Right identity: `compose(f, id) = f`
- Associativity:  `compose(compose(h,g), f) = compose(h, compose(g,f))`

**B. Functor laws** (two concrete endofunctors: `Result<string,_>`, `WithLog<_>`)
- Identity preserved:    `fmap(id) = id`
- Composition preserved: `fmap(g ∘ f) = fmap(g) ∘ fmap(f)`

**C. Naturality** for `alpha = resultToMaybe : Result<E,_> ⇒ Maybe<_>`
(it forgets the error: `ok a ↦ just a`, `err e ↦ nothing`). The naturality
square must commute for every `f : A -> B`:

```
       Result<E,A>  --alpha-->  Maybe<A>
           |                        |
    resultFmap(f)             maybeFmap(f)
           v                        v
       Result<E,B>  --alpha-->  Maybe<B>

   maybeFmap(f) ∘ alpha  ==  alpha ∘ resultFmap(f)
```

## Honesty: exact vs. metaphorical

- **Exact.** `id`/`compose` genuinely satisfy the category laws (identity and
  associativity) for these pure handlers — the tests demonstrate it on random
  data, and it also holds by construction since `compose` is plain function
  composition. `resultFmap`, `logFmap`, `maybeFmap` are honest functor maps and
  satisfy both functor laws. `resultToMaybe` is a genuine natural transformation:
  it is parametric in `A` (no per-type special-casing), which is exactly the
  condition that forces naturality; the square commutes in the tests.
- **Exact-but-value-level.** Our functors act on *values* (`A ↦ Result<E,A>`)
  rather than on the arbitrary `Ctx`-morphisms of the base category. They are
  endofunctors on the category **Set**/**Type** (types + functions), which is
  the standard setting for "functor" in typed FP. So the functor/naturality
  story lives in the type-and-function category, and we *bridge* it into the
  handler pipeline by wrapping payloads in `Ctx` (e.g. `Handler<Request,
  Result<string, GreetInput>>`). That bridge is a modelling choice, not a
  theorem.
- **Metaphorical / not enforced.** Property tests sample finitely many inputs;
  they raise confidence, they are not proofs. `Ctx.meta` is an untyped bag, so
  "objects" are really `(payload type, loose meta)`; equality of morphisms is
  tested extensionally on sampled inputs, not proven intensionally. We do not
  model monoidal structure, monads (no `Kleisli` composition laws are tested),
  or size/foundational issues. "Middleware = endofunctor" is a useful lens, not
  a claim that every middleware you could write is functorial.

## Files

- `src/category.ts` — `Ctx`, `Handler`, `id`, `compose`, `pipe`.
- `src/functor.ts`  — `Result`/`Either` and `WithLog`/`Writer` functors + `fmap`.
- `src/natural.ts`  — `Maybe` functor and the `Result ⇒ Maybe` natural transformation.
- `src/router.ts`   — tiny immutable router; an endpoint is a composed handler.
- `src/demo.ts`     — end-to-end example requests.
- `src/laws.ts`     — the executable law tests (must pass).

## Run instructions

```bash
npm install
npm run build      # tsc -> dist/
npm test           # runs the law tests (exits non-zero on any failure)
npm run demo       # runs the end-to-end request demo
# or all three:
npm start
```

Requires Node 18+ (developed on Node 24).

## Sample output

Law tests (`npm test`):

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

Demo (`npm run demo`):

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

## License

MIT.

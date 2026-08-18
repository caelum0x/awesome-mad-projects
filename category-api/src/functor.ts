/**
 * functor.ts
 * ----------
 * Functors on our category of contexts.
 *
 * A functor F maps
 *   - objects  A         to objects  F<A>, and
 *   - morphisms f: A->B  to morphisms F<f>: F<A> -> F<B>   (that is `fmap`),
 * preserving identities and composition:
 *   - F(id_A) = id_{F A}
 *   - F(g . f) = F(g) . F(f)
 *
 * We give two concrete functors:
 *   1. Result<E, _>  -- an Either-style success/failure wrapper. This is an
 *      ENDOFUNCTOR on the value level (maps types to types, functions to
 *      functions). It models middleware that can short-circuit with an error.
 *   2. WithLog        -- a Writer-style logger that threads a log alongside a
 *      value. Also an endofunctor; models logging middleware.
 *
 * Both are exercised against the functor laws in `laws.ts`.
 */

// ---------------------------------------------------------------------------
// 1. Result / Either functor
// ---------------------------------------------------------------------------

export type Ok<A> = { readonly tag: "ok"; readonly value: A };
export type Err<E> = { readonly tag: "err"; readonly error: E };

/** Result<E, A> is either an error E or a value A. */
export type Result<E, A> = Ok<A> | Err<E>;

export function ok<E, A>(value: A): Result<E, A> {
  return { tag: "ok", value };
}

export function err<E, A>(error: E): Result<E, A> {
  return { tag: "err", error };
}

export function isOk<E, A>(r: Result<E, A>): r is Ok<A> {
  return r.tag === "ok";
}

/**
 * `fmap` for Result. The error `E` is fixed; we map only over the success
 * value. On `err` the function is not applied -- this is exactly what makes
 * error middleware "short-circuit".
 *
 *   resultFmap(f) : Result<E, A> -> Result<E, B>
 */
export function resultFmap<E, A, B>(
  f: (a: A) => B,
): (r: Result<E, A>) => Result<E, B> {
  return (r: Result<E, A>): Result<E, B> =>
    r.tag === "ok" ? ok(f(r.value)) : err(r.error);
}

// ---------------------------------------------------------------------------
// 2. Writer / Logger functor
// ---------------------------------------------------------------------------

/** A value carried together with an accumulated, immutable log. */
export interface WithLog<A> {
  readonly value: A;
  readonly log: ReadonlyArray<string>;
}

export function withLog<A>(value: A, log: ReadonlyArray<string> = []): WithLog<A> {
  return { value, log: [...log] };
}

/**
 * `fmap` for the logger functor: transform the carried value, keep the log.
 *
 *   logFmap(f) : WithLog<A> -> WithLog<B>
 */
export function logFmap<A, B>(f: (a: A) => B): (w: WithLog<A>) => WithLog<B> {
  return (w: WithLog<A>): WithLog<B> => withLog(f(w.value), w.log);
}

/** A structural equality helper used by the law tests. */
export function eqResult<E, A>(x: Result<E, A>, y: Result<E, A>): boolean {
  if (x.tag === "ok" && y.tag === "ok") return Object.is(x.value, y.value);
  if (x.tag === "err" && y.tag === "err") return Object.is(x.error, y.error);
  return false;
}

export function eqWithLog<A>(x: WithLog<A>, y: WithLog<A>): boolean {
  return (
    Object.is(x.value, y.value) &&
    x.log.length === y.log.length &&
    x.log.every((s, i) => s === y.log[i])
  );
}

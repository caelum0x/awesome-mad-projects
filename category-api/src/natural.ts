/**
 * natural.ts
 * ----------
 * A natural transformation between two functors.
 *
 * We map the `Result<E, _>` functor to the `Maybe<_>` functor by forgetting
 * the error payload:
 *
 *   alpha_A : Result<E, A> -> Maybe<A>
 *   alpha(ok a)  = just a
 *   alpha(err e) = nothing
 *
 * A transformation `alpha` is NATURAL when, for every morphism `f : A -> B`,
 * the "naturality square" commutes:
 *
 *        Result<E,A>  --alpha_A-->  Maybe<A>
 *            |                          |
 *   resultFmap(f)                 maybeFmap(f)
 *            v                          v
 *        Result<E,B>  --alpha_B-->  Maybe<B>
 *
 * i.e.  maybeFmap(f) . alpha_A  ===  alpha_B . resultFmap(f).
 *
 * Practically: it does not matter whether you transform the value first and
 * then discard the error, or discard the error first and then transform --
 * you land on the same Maybe. This is verified in `laws.ts`.
 */

import { Result } from "./functor";

// ---------------------------------------------------------------------------
// The target functor: Maybe
// ---------------------------------------------------------------------------

export type Just<A> = { readonly tag: "just"; readonly value: A };
export type Nothing = { readonly tag: "nothing" };
export type Maybe<A> = Just<A> | Nothing;

export function just<A>(value: A): Maybe<A> {
  return { tag: "just", value };
}

export const nothing: Maybe<never> = { tag: "nothing" };

/** `fmap` for Maybe. */
export function maybeFmap<A, B>(f: (a: A) => B): (m: Maybe<A>) => Maybe<B> {
  return (m: Maybe<A>): Maybe<B> =>
    m.tag === "just" ? just(f(m.value)) : nothing;
}

// ---------------------------------------------------------------------------
// The natural transformation Result<E, _> => Maybe<_>
// ---------------------------------------------------------------------------

/**
 * `resultToMaybe` is the component `alpha_A` of the natural transformation.
 * It is a single polymorphic function, which is exactly the point: a
 * transformation defined uniformly in `A` (with no per-type special-casing)
 * is automatically natural. The test in `laws.ts` confirms the square
 * commutes for concrete data.
 */
export function resultToMaybe<E, A>(r: Result<E, A>): Maybe<A> {
  return r.tag === "ok" ? just(r.value) : nothing;
}

/** Structural equality for Maybe, used by the law tests. */
export function eqMaybe<A>(x: Maybe<A>, y: Maybe<A>): boolean {
  if (x.tag === "just" && y.tag === "just") return Object.is(x.value, y.value);
  return x.tag === "nothing" && y.tag === "nothing";
}

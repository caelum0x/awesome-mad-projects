/**
 * category.ts
 * -----------
 * The base category.
 *
 * Objects  : TypeScript types used as request/response contexts, `Ctx<A>`.
 * Morphisms: pure handlers `Handler<A, B> = (Ctx<A>) => Ctx<B>`.
 *
 * We provide the two pieces of data every category must have:
 *   - an identity morphism `id` for every object, and
 *   - a composition operator `compose` that is associative and unital.
 *
 * The laws themselves are checked in `laws.ts`.
 */

/**
 * A request/response context flowing through the handler pipeline.
 * `A` is the shape of the payload the handler cares about. `meta` carries
 * cross-cutting data (headers, timing, logs) that handlers may read/extend
 * without changing the payload's type.
 */
export interface Ctx<A> {
  readonly value: A;
  readonly meta: Readonly<Record<string, unknown>>;
}

/** Build a fresh context. Immutable by construction. */
export function ctx<A>(value: A, meta: Record<string, unknown> = {}): Ctx<A> {
  return { value, meta: { ...meta } };
}

/**
 * A morphism in our category: a total function from one context type to
 * another. Handlers are pure: they return a NEW context and never mutate
 * the input (see coding-style: immutability).
 */
export type Handler<A, B> = (input: Ctx<A>) => Ctx<B>;

/**
 * Identity morphism `id_A : Ctx<A> -> Ctx<A>`.
 * Returns its input unchanged. There is one `id` per object; TypeScript's
 * parametric polymorphism lets a single generic function stand in for the
 * whole family.
 */
export function id<A>(): Handler<A, A> {
  return (input: Ctx<A>): Ctx<A> => input;
}

/**
 * Composition of morphisms, written in the usual mathematical order:
 * `compose(g, f)` is "g after f", i.e. `x => g(f(x))`.
 *
 *   f : A -> B
 *   g : B -> C
 *   compose(g, f) : A -> C
 */
export function compose<A, B, C>(
  g: Handler<B, C>,
  f: Handler<A, B>,
): Handler<A, C> {
  return (input: Ctx<A>): Ctx<C> => g(f(input));
}

/**
 * Variadic left-to-right pipeline sugar. `pipe(f, g, h)` applies f, then g,
 * then h. It is defined purely in terms of `compose` and `id`, so it inherits
 * their laws. Types are checked pairwise at the call sites in router.ts / demo.ts.
 */
export function pipe<A>(...handlers: Handler<any, any>[]): Handler<A, any> {
  return handlers.reduce(
    (acc, h) => compose(h, acc),
    id<A>() as Handler<any, any>,
  );
}

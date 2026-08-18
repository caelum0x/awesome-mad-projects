/**
 * router.ts
 * ---------
 * A tiny router that composes typed handlers (morphisms) into endpoints and
 * runs example requests end to end.
 *
 * The router is deliberately thin: an endpoint IS a morphism `Ctx<Req> ->
 * Ctx<Res>` built with `compose`/`pipe` from `category.ts`. The router just
 * dispatches on method+path and applies the composed handler.
 */

import { Ctx, Handler, ctx } from "./category";

export interface Request {
  readonly method: string;
  readonly path: string;
  readonly body: unknown;
}

export interface Response {
  readonly status: number;
  readonly body: unknown;
}

/** An endpoint is a morphism from a request context to a response context. */
export type Endpoint = Handler<Request, Response>;

interface Route {
  readonly method: string;
  readonly path: string;
  readonly endpoint: Endpoint;
}

/**
 * Immutable router. `register` returns a NEW router with the added route
 * rather than mutating in place (coding-style: immutability).
 */
export class Router {
  private constructor(private readonly routes: ReadonlyArray<Route>) {}

  static create(): Router {
    return new Router([]);
  }

  register(method: string, path: string, endpoint: Endpoint): Router {
    const route: Route = { method: method.toUpperCase(), path, endpoint };
    return new Router([...this.routes, route]);
  }

  /** Handle a request, returning a response context. */
  handle(req: Request): Ctx<Response> {
    const match = this.routes.find(
      (r) => r.method === req.method.toUpperCase() && r.path === req.path,
    );
    if (!match) {
      return ctx<Response>(
        { status: 404, body: { error: `No route for ${req.method} ${req.path}` } },
        { matched: false },
      );
    }
    return match.endpoint(ctx(req, { matched: true }));
  }
}

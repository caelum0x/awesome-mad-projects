/**
 * awesome-mad-projects — Worker + Static Assets entry point.
 *
 * Static files in ./site are served directly by the Assets binding (they take
 * precedence). This Worker only runs for paths with no matching asset, where it
 * exposes GET /api/projects (serving the site's projects.json with CORS). All
 * other unmatched paths fall through to the static assets (e.g. index.html).
 */
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/api/projects") {
      if (request.method === "OPTIONS") {
        return new Response(null, { status: 204, headers: cors() });
      }
      if (request.method !== "GET" && request.method !== "HEAD") {
        return new Response("Method Not Allowed", {
          status: 405,
          headers: { ...cors(), Allow: "GET, HEAD, OPTIONS" },
        });
      }
      const res = await env.ASSETS.fetch(
        new Request(new URL("/projects.json", url.origin), request)
      );
      const body = await res.text();
      return new Response(body, {
        status: res.status,
        headers: {
          "content-type": "application/json; charset=utf-8",
          "cache-control": "public, max-age=300",
          ...cors(),
        },
      });
    }

    // Everything else: serve from static assets.
    return env.ASSETS.fetch(request);
  },
};

function cors() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, HEAD, OPTIONS",
  };
}

/**
 * awesome-mad-projects — Worker + Static Assets entry point.
 *
 * Static files in ./site are served directly by the Assets binding (they take
 * precedence). This Worker only runs for paths with no matching asset, where it
 * exposes GET /api/projects (serving the site's projects.json with CORS). All
 * other unmatched paths fall through to the static assets (e.g. index.html).
 *
 * Because `run_worker_first = true` in wrangler.toml, every request (including
 * static HTML) passes through this Worker first. We use that to inject the X
 * (Twitter) conversion tracking pixel into every served HTML page via
 * HTMLRewriter, rather than hand-editing ~24 independent static HTML files
 * (index.html, gallery.html, and each page under site/projects/) that share no
 * build-time template.
 */

const TWITTER_PIXEL_SNIPPET = `<!-- X conversion tracking base code -->
<script>
!function(e,t,n,s,u,a){e.twq||(s=e.twq=function(){s.exe?s.exe.apply(s,arguments):s.queue.push(arguments);
},s.version='1.1',s.queue=[],u=t.createElement(n),u.async=!0,u.src='https://static.ads-twitter.com/uwt.js',
a=t.getElementsByTagName(n)[0],a.parentNode.insertBefore(u,a))}(window,document,'script');
twq('config','rhhqi');
</script>
<!-- End X conversion tracking base code -->`;

/** Appends the X pixel snippet right before the closing </body> tag. */
class PixelInjector {
  element(element) {
    element.append(TWITTER_PIXEL_SNIPPET, { html: true });
  }
}

/**
 * Injects the X conversion tracking pixel into HTML responses only.
 * @param {Response} response
 * @returns {Response}
 */
function withPixel(response) {
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("text/html")) {
    return response;
  }
  return new HTMLRewriter().on("body", new PixelInjector()).transform(response);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // Consolidate legacy static-file URLs that Google discovered before the
    // extensionless canonicals shipped. Keep the query string, but issue a
    // permanent redirect so ranking signals move to one URL.
    if (
      (request.method === "GET" || request.method === "HEAD") &&
      url.pathname.endsWith(".html")
    ) {
      const canonical = new URL(url);
      canonical.pathname = url.pathname.endsWith("/index.html")
        ? url.pathname.slice(0, -"index.html".length) || "/"
        : url.pathname.slice(0, -".html".length) || "/";
      return Response.redirect(canonical.toString(), 301);
    }

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

    // Everything else: serve from static assets, injecting the X pixel into
    // any HTML response along the way.
    return withPixel(await env.ASSETS.fetch(request));
  },
};

function cors() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, HEAD, OPTIONS",
  };
}

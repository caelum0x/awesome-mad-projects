# awesome-mad-projects — showcase site

A self-contained, static showcase for ~22 "anime/pop-culture × mathematics, in real
code" projects. No external CDNs, no build step. It ships one Cloudflare Pages
Function so `GET /api/projects` returns the same catalog the page renders.

## Contents

```
site/
├── index.html              # showcase (hero, featured media, project grid, caveats, footer)
├── gallery.html            # full infinity-lab artifact gallery
├── projects.json           # canonical machine-readable project catalog (22 projects)
├── assets/                 # local media (poster, headline PNGs, MP4s) + app.js
├── functions/
│   └── api/
│       └── projects.js     # Pages Function → GET /api/projects (JSON + CORS)
├── _headers                # caching + security headers (CSP, nosniff, immutable assets)
├── _redirects              # /gallery → /gallery.html, /repo → GitHub
└── README.md               # this file
```

The project grid is data-driven from `projects.json` (fetched by `assets/app.js`,
with an inline JSON fallback so the page also works when opened directly from disk).

## Local preview

Run a local server that also executes the Pages Function:

```bash
npx wrangler pages dev site
```

Then open the printed URL and check both the page and `http://localhost:8788/api/projects`.

## Deploy to Cloudflare Pages

### Option A — direct upload (fastest)

```bash
npx wrangler pages deploy site --project-name awesome-mad-projects
```

Wrangler uploads the `site/` directory and automatically picks up `site/functions/`
as Pages Functions (Workers), so `GET /api/projects` works on the live site.

### Option B — Git integration (dashboard)

1. Push this repo to GitHub (already at
   `https://github.com/caelum0x/awesome-mad-projects`).
2. In the Cloudflare dashboard: **Workers & Pages → Create → Pages → Connect to Git**,
   and select the repo.
3. Configure the build:
   - **Framework preset:** `None`
   - **Build command:** *(leave empty)*
   - **Build output directory:** `site`
4. Save and deploy. Every push to the default branch triggers a new deployment.

### Pages Functions (Workers)

`site/functions/api/projects.js` uses the standard Pages Functions signature
(`export async function onRequest(context) { ... }`). Cloudflare deploys everything
under `site/functions/` as Workers automatically — no `wrangler.toml` required — so
`GET /api/projects` returns `projects.json` as `application/json` with permissive CORS.

## Notes

- Fully local media: only outbound links are the GitHub source folders and the
  attribution essay PDF. Everything else is same-origin.
- MP4s are used instead of the multi-megabyte GIFs to keep the deploy small.
- `_headers` sets a long immutable cache for `assets/*` and `no-cache` for HTML.

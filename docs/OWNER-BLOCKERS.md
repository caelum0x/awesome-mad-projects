# Owner-only blockers

## www.mad-projects.com returns NXDOMAIN

A Cloudflare Workers route for `www.mad-projects.com/*` already exists
(bound to the `awesome-mad-projects` worker, same as the apex), but there
is no DNS record at `www` to trigger it — so the route never fires and
the hostname doesn't resolve at all. This session's Cloudflare API
credentials are read-only (`dns_records:read` but no write scope), so it
can't be fixed from here.

**Fix (Cloudflare dashboard, zone `mad-projects.com`, ~2 minutes):**
DNS → Add record → Type `CNAME`, Name `www`, Target `mad-projects.com`,
Proxy status **Proxied** (orange cloud) ON.

Once that record exists, `https://www.mad-projects.com` should resolve
through the existing route with no further Worker changes needed.

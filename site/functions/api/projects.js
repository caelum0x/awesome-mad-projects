// Cloudflare Pages Function — GET /api/projects
// Serves the same project catalog used by the static site as JSON, with
// permissive CORS so the data can be consumed from anywhere.

import projects from "../../projects.json";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function onRequest(context) {
  const { request } = context;

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: CORS_HEADERS });
  }

  if (request.method !== "GET") {
    return new Response(
      JSON.stringify({ success: false, data: null, error: "Method not allowed" }),
      {
        status: 405,
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          Allow: "GET, OPTIONS",
          ...CORS_HEADERS,
        },
      }
    );
  }

  const body = JSON.stringify({ success: true, data: projects, error: null });

  return new Response(body, {
    status: 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=300",
      ...CORS_HEADERS,
    },
  });
}

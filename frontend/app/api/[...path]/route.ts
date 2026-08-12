import { NextRequest, NextResponse } from "next/server";

// 所有 /api/* 请求经此代理转发到后端，手机/电脑只需访问 Vercel
const BACKEND =
  process.env.BACKEND_API_URL ?? "https://tripai-api-gvspoitbkf.cn-hangzhou.fcapp.run";

type RouteCtx = { params: Promise<{ path: string[] }> };

async function proxy(req: NextRequest, method: string, ctx: RouteCtx) {
  const { path } = await ctx.params;
  const url = `${BACKEND}/api/${path.join("/")}${req.nextUrl.search}`;

  const headers: Record<string, string> = {};
  const auth = req.headers.get("authorization");
  if (auth) headers.authorization = auth;
  const contentType = req.headers.get("content-type");
  if (contentType) headers["content-type"] = contentType;

  const body = ["GET", "HEAD", "OPTIONS"].includes(method)
    ? undefined
    : await req.text();

  const res = await fetch(url, {
    method,
    headers,
    body,
    signal: AbortSignal.timeout(55_000),
  });
  const responseHeaders = new Headers();
  responseHeaders.set(
    "content-type",
    res.headers.get("content-type") ?? "application/json"
  );
  responseHeaders.set("cache-control", "no-store");
  return new Response(res.body, { status: res.status, headers: responseHeaders });
}

export const GET = (req: NextRequest, ctx: RouteCtx) => proxy(req, "GET", ctx);
export const POST = (req: NextRequest, ctx: RouteCtx) => proxy(req, "POST", ctx);
export const PUT = (req: NextRequest, ctx: RouteCtx) => proxy(req, "PUT", ctx);
export const DELETE = (req: NextRequest, ctx: RouteCtx) =>
  proxy(req, "DELETE", ctx);
export const OPTIONS = (req: NextRequest, ctx: RouteCtx) =>
  proxy(req, "OPTIONS", ctx);

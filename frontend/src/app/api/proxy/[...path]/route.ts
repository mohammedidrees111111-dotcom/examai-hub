import { NextRequest, NextResponse } from "next/server";

const BACKEND = "https://examai-hub-api.onrender.com";

export async function GET(request: NextRequest) {
  return proxy(request, "GET");
}
export async function POST(request: NextRequest) {
  return proxy(request, "POST");
}
export async function PUT(request: NextRequest) {
  return proxy(request, "PUT");
}
export async function DELETE(request: NextRequest) {
  return proxy(request, "DELETE");
}
export async function PATCH(request: NextRequest) {
  return proxy(request, "PATCH");
}
export async function OPTIONS() {
  return new NextResponse(null, { status: 200, headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS", "Access-Control-Allow-Headers": "*" } });
}

async function proxy(request: NextRequest, method: string) {
  const url = request.nextUrl.pathname.replace("/api/proxy", "");
  const search = request.nextUrl.search;
  const backendUrl = `${BACKEND}${url}${search}`;

  try {
    const headers: Record<string, string> = {};
    request.headers.forEach((v, k) => { if (!["host","connection","content-length"].includes(k.toLowerCase())) headers[k] = v; });

    const body = method !== "GET" && method !== "HEAD" ? await request.text() : undefined;

    const res = await fetch(backendUrl, { method, headers, body });
    const responseHeaders: Record<string, string> = {};
    res.headers.forEach((v, k) => { if (!["content-encoding","transfer-encoding"].includes(k.toLowerCase())) responseHeaders[k] = v; });
    responseHeaders["Access-Control-Allow-Origin"] = "*";

    return new NextResponse(await res.text(), { status: res.status, headers: responseHeaders });
  } catch {
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 502 });
  }
}

import { createHmac, timingSafeEqual, randomBytes } from 'node:crypto';
import { NextRequest, NextResponse } from 'next/server.js';

const COOKIE = 'mark5_operator';
const MAX_BODY = 128 * 1024;
const SESSION_SECONDS = 8 * 60 * 60;
const loginAttempts = new Map<string, { count: number; until: number }>();
function loginLimited(request: NextRequest): boolean {
  const key = request.headers.get('x-vercel-forwarded-for') ?? request.headers.get('x-forwarded-for') ?? 'local';
  const at = Date.now();
  for (const [id, entry] of loginAttempts) if (entry.until < at) loginAttempts.delete(id);
  if (loginAttempts.size >= 1000 && !loginAttempts.has(key)) return true;
  const entry = loginAttempts.get(key) ?? { count: 0, until: at + 60_000 };
  entry.count += 1; loginAttempts.set(key, entry);
  return entry.count > 8;
}
async function boundedResponse(response: Response): Promise<string> {
  const reader = response.body?.getReader(); if (!reader) return '';
  const parts: Uint8Array[] = []; let count = 0;
  while (true) { const part = await reader.read(); if (part.done) break; count += part.value.byteLength;
    if (count > 16 * 1024 * 1024) { await reader.cancel(); throw new Error('Service response exceeds limit'); }
    parts.push(part.value);
  }
  return Buffer.concat(parts).toString('utf8');
}
function secret(): string { return process.env.MARK5_SESSION_SECRET ?? ''; }
function constantEqual(a: string, b: string): boolean {
  const x = Buffer.from(a), y = Buffer.from(b);
  return x.length === y.length && timingSafeEqual(x, y);
}
function signature(value: string): string { return createHmac('sha256', secret()).update(value).digest('hex'); }
export function authenticated(request: NextRequest): boolean {
  if (secret().length < 32) return false;
  const value = request.cookies.get(COOKIE)?.value ?? '';
  const fields = value.split('.');
  if (fields.length !== 3 || !/^\d{10,12}$/.test(fields[0]) || !/^[a-f0-9]{32}$/.test(fields[1])) return false;
  const expires = Number(fields[0]);
  return expires > Math.floor(Date.now() / 1000) && expires <= Math.floor(Date.now() / 1000) + SESSION_SECONDS + 60 && constantEqual(fields[2], signature(`${fields[0]}.${fields[1]}`));
}
export function errorResponse(message: string, status: number): NextResponse { return NextResponse.json({ error: message }, { status, headers: { 'Cache-Control': 'no-store' } }); }
export function sameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get('origin');
  // Browsers send Origin on cookie-authenticated writes; no permissive fallback.
  const configured = process.env.MARK5_PUBLIC_ORIGIN;
  return !!origin && origin === (configured ?? request.nextUrl.origin);
}
export async function limitedBody(request: NextRequest): Promise<string> {
  const declared = request.headers.get('content-length');
  if (declared && (!/^\d+$/.test(declared) || Number(declared) > MAX_BODY)) throw new Error('Request body exceeds limit');
  const reader = request.body?.getReader();
  if (!reader) return '{}';
  const chunks: Uint8Array[] = []; let size = 0;
  while (true) {
    const part = await reader.read(); if (part.done) break;
    size += part.value.byteLength;
    if (size > MAX_BODY) { await reader.cancel(); throw new Error('Request body exceeds limit'); }
    chunks.push(part.value);
  }
  const body = Buffer.concat(chunks).toString('utf8');
  const parsed: unknown = JSON.parse(body || '{}');
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error('JSON object required');
  return body || '{}';
}
export function validDate(date: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(date) && Number.isFinite(Date.parse(`${date}T00:00:00Z`)) && new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) === date;
}
export async function proxy(request: NextRequest, path: string, write = false, webhook = false): Promise<Response> {
  if (!/^\/v1\/(dashboard|refresh|events|ai\/review|jobs\/[a-f0-9]{32}|plans\/\d{4}-\d{2}-\d{2}(\/(revise|approve))?)$/.test(path)) return errorResponse('Invalid route', 400);
  if (write && !webhook && (!sameOrigin(request) || !authenticated(request))) return errorResponse('Operator authentication and same-origin request required', 401);
  const base = process.env.MARK5_SERVICE_URL;
  if (!base) return errorResponse('Planning service is not configured', 503);
  let serviceUrl: URL;
  try { serviceUrl = new URL(base); } catch { return errorResponse('Invalid service configuration', 503); }
  if (!['http:', 'https:'].includes(serviceUrl.protocol) || serviceUrl.username || serviceUrl.password || serviceUrl.pathname !== '/' || serviceUrl.search || serviceUrl.hash) return errorResponse('Invalid service configuration', 503);
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (write) {
    headers['Content-Type'] = 'application/json';
    if (webhook) {
      headers['X-Mark5-Timestamp'] = request.headers.get('x-mark5-timestamp') ?? '';
      headers['X-Mark5-Signature'] = request.headers.get('x-mark5-signature') ?? '';
    } else {
      if (!process.env.MARK5_SERVICE_SECRET) return errorResponse('Planning service authentication is not configured', 503);
      headers.Authorization = `Bearer ${process.env.MARK5_SERVICE_SECRET}`;
    }
  }
  const etag = request.headers.get('if-none-match'); if (etag && !write) headers['If-None-Match'] = etag;
  let body: string | undefined;
  try { if (write) body = await limitedBody(request); } catch { return errorResponse('Invalid JSON or request body exceeds limit', 400); }
  try {
    const response = await fetch(new URL(path, serviceUrl), { method: write ? 'POST' : 'GET', headers, body, cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(15_000) });
    const outHeaders: Record<string, string> = { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };
    const responseEtag = response.headers.get('etag'); if (responseEtag) outHeaders.ETag = responseEtag;
    return new Response(response.status === 304 ? null : await boundedResponse(response), { status: response.status, headers: outHeaders });
  } catch { return errorResponse('Planning service is temporarily unavailable; the last loaded plan remains on screen', 503); }
}
export async function session(request: NextRequest): Promise<NextResponse> {
  if (request.method === 'GET') return NextResponse.json({ authenticated: authenticated(request) }, { headers: { 'Cache-Control': 'no-store' } });
  if (!sameOrigin(request)) return errorResponse('Same-origin request required', 403);
  if (request.method === 'DELETE') {
    const response = NextResponse.json({ authenticated: false });
    response.cookies.set(COOKIE, '', { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'strict', path: '/', maxAge: 0 }); return response;
  }
  if (loginLimited(request)) return errorResponse('Too many login attempts; retry in one minute', 429);
  const expected = process.env.MARK5_OPERATOR_PASSCODE ?? '';
  if (expected.length < 16 || secret().length < 32) return errorResponse('Operator access is not configured', 503);
  let value: unknown;
  try { value = JSON.parse(await limitedBody(request)); } catch { return errorResponse('Invalid request', 400); }
  const fields = value as Record<string, unknown>;
  if (Object.keys(fields).length !== 1 || typeof fields.passcode !== 'string' || fields.passcode.length > 256 || !constantEqual(fields.passcode, expected)) return errorResponse('Incorrect operator passcode', 401);
  const unsigned = `${Math.floor(Date.now() / 1000) + SESSION_SECONDS}.${randomBytes(16).toString('hex')}`;
  const response = NextResponse.json({ authenticated: true }, { headers: { 'Cache-Control': 'no-store' } });
  response.cookies.set(COOKIE, `${unsigned}.${signature(unsigned)}`, { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'strict', path: '/', maxAge: SESSION_SECONDS });
  return response;
}

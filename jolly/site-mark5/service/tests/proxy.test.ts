import test from 'node:test';
import assert from 'node:assert/strict';
import { NextRequest } from 'next/server.js';
import { authenticated, session, proxy, validDate } from '../../lib/service-client.ts';
process.env.MARK5_SESSION_SECRET = 'a'.repeat(40);
process.env.MARK5_OPERATOR_PASSCODE = 'b'.repeat(40);
process.env.MARK5_SERVICE_URL = 'https://service.example.test';
process.env.MARK5_SERVICE_SECRET = 'c'.repeat(40);
process.env.MARK5_PUBLIC_ORIGIN = 'https://planner.example.test';
const origin = 'https://planner.example.test';
function request(path: string, method = 'GET', body?: object, cookie?: string, withOrigin = true) {
  return new NextRequest(origin + path, { method, headers: { ...(withOrigin ? { origin } : {}), ...(cookie ? { cookie } : {}), 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
}
test('cookie login, Origin protection, and tamper rejection', async () => {
  const login = await session(request('/api/session', 'POST', { passcode: 'b'.repeat(40) }));
  assert.equal(login.status, 200);
  const set = login.headers.get('set-cookie')!;
  assert.match(set, /HttpOnly/i); assert.match(set, /SameSite=strict/i);
  const cookie = set.split(';')[0];
  assert.equal(authenticated(request('/api/session', 'GET', undefined, cookie)), true);
  assert.equal(authenticated(request('/api/session', 'GET', undefined, cookie + 'x')), false);
  assert.equal((await session(request('/api/session', 'POST', { passcode: 'b'.repeat(40) }, undefined, false))).status, 403);
  assert.equal((await proxy(request('/api/refresh', 'POST', {}, cookie, false), '/v1/refresh', true)).status, 401);
  const logout = await session(request('/api/session', 'DELETE', undefined, cookie));
  assert.match(logout.headers.get('set-cookie')!, /Max-Age=0/);
});
test('proxy requires auth for mutation and forwards only to configured upstream', async () => {
  assert.equal((await proxy(request('/api/refresh', 'POST', {}), '/v1/refresh', true)).status, 401);
  assert.equal((await proxy(request('/api/dashboard'), '/v1/../../etc/passwd')).status, 400);
  const oldFetch = globalThis.fetch;
  let called = '';
  globalThis.fetch = (async (url: unknown, init?: RequestInit) => { called = String(url); assert.equal(init?.redirect, 'error'); return new Response('{}', { status: 200, headers: { ETag: '"test"' } }); }) as typeof fetch;
  try {
    const r = await proxy(request('/api/dashboard'), '/v1/dashboard');
    assert.equal(r.status, 200); assert.equal(called, 'https://service.example.test/v1/dashboard'); assert.equal(r.headers.get('etag'), '"test"');
  } finally { globalThis.fetch = oldFetch; }
});
test('dates reject impossible days and path injection', () => {
  assert.equal(validDate('2026-02-30'), false); assert.equal(validDate('../2026-09-10'), false);
  assert.equal(validDate('2026-09-10'), true);
});

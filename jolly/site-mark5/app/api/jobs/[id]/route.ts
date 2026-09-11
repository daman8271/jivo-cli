import { NextRequest } from 'next/server.js';
import { proxy, errorResponse } from '../../../../lib/service-client';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export async function GET(request: NextRequest, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  if (!/^[a-f0-9]{32}$/.test(id)) return errorResponse('Invalid job ID', 400);
  return proxy(request, `/v1/jobs/${id}`);
}

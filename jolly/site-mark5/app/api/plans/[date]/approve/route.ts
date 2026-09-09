import { NextRequest } from 'next/server.js';
import { proxy, validDate, errorResponse } from '../../../../../lib/service-client';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export async function POST(request: NextRequest, context: { params: Promise<{ date: string }> }) {
  const { date } = await context.params;
  if (!validDate(date)) return errorResponse('Invalid date', 400);
  return proxy(request, `/v1/plans/${date}/approve`, true);
}

import { NextRequest } from 'next/server.js';
import { proxy } from '../../../../lib/service-client';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export function POST(request: NextRequest) { return proxy(request, '/v1/ai/review', true); }

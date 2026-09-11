import { NextRequest } from 'next/server.js';
import { proxy } from '../../../lib/service-client';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export function GET(request: NextRequest) { return proxy(request, '/v1/dashboard'); }

import { NextRequest } from 'next/server.js';
import { session } from '../../../lib/service-client';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
export const GET = (request: NextRequest) => session(request);
export const POST = GET;
export const DELETE = GET;

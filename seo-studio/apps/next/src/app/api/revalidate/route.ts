// app/api/revalidate/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { revalidateTag } from 'next/cache';
import crypto from 'crypto';

// This secret should be stored in environment variables and shared with the CMS
const REVALIDATE_SECRET = process.env.REVALIDATE_SECRET || 'a-secure-secret-token';

export async function POST(request: NextRequest) {
  const signature = request.headers.get('x-hmac-signature');
  const body = await request.json();

  // 1. Verify the HMAC signature
  const expectedSignature = crypto
    .createHmac('sha256', REVALIDATE_SECRET)
    .update(JSON.stringify(body))
    .digest('hex');

  if (signature !== expectedSignature) {
    console.warn('Invalid revalidation signature received.');
    return NextResponse.json({ message: 'Invalid signature' }, { status: 401 });
  }

  // 2. Revalidate the tags
  const tags = body.tags as string[];
  if (!tags || !Array.isArray(tags)) {
    return NextResponse.json({ message: 'Invalid tags payload' }, { status: 400 });
  }

  try {
    tags.forEach(tag => revalidateTag(tag));
    console.log(`Revalidated tags: ${tags.join(', ')}`);
    return NextResponse.json({ revalidated: true, tags, now: Date.now() });
  } catch (error) {
    console.error('Error during revalidation:', error);
    return NextResponse.json({ message: 'Error during revalidation' }, { status: 500 });
  }
}

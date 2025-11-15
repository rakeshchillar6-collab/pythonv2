// lib/api.ts
import { notFound } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

interface PostRender {
  id: string;
  slug: string;
  html: string;
  meta: Record<string, any>;
  jsonld: any[];
  updated_at: string;
}

async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  const url = `${API_URL}${endpoint}`;

  try {
    const res = await fetch(url, { ...options, headers });

    if (!res.ok) {
      if (res.status === 404) {
        notFound();
      }
      throw new Error(`Failed to fetch API: ${res.status} ${res.statusText}`);
    }
    return res.json();
  } catch (error) {
    console.error('API Fetch Error:', error);
    throw new Error('Failed to fetch from the API.');
  }
}

export async function getPostBySlug(slug: string): Promise<PostRender> {
  const endpoint = `/content/render/${slug}/`;
  const options = {
    next: {
      revalidate: 60, // Revalidate every 60 seconds
      tags: [`post:${slug}`],
    },
  };
  return fetchAPI<PostRender>(endpoint, options);
}

// Add other fetchers as needed, e.g., for search
// export async function searchVector(query: string) { ... }

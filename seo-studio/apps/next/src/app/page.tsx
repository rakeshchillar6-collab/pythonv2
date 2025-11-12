// src/app/page.tsx
import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="bg-white p-8 rounded-lg shadow-md text-center">
      <h1 className="text-4xl font-bold mb-4">Welcome to Our Blog!</h1>
      <p className="text-gray-600 mb-6">
        This is a sample blog built with Django, Next.js, and a lot of love.
      </p>
      <Link
        href="/blog"
        className="bg-blue-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-600 transition-colors"
      >
        Explore Blog Posts
      </Link>
    </div>
  );
}

// src/app/blog/page.tsx
import Link from 'next/link';
import { getPosts, Post } from '@/lib/api';

async function fetchPosts() {
    try {
        const response = await getPosts();
        return response.results;
    } catch (error) {
        console.error("Failed to fetch posts:", error);
        return [];
    }
}

export default async function BlogPage() {
    const posts = await fetchPosts();

    return (
        <div>
            <h1 className="text-4xl font-bold mb-8">Blog Posts</h1>

            {posts.length === 0 ? (
                <p className="text-gray-500">No posts found. Maybe the API is not connected?</p>
            ) : (
                <div className="space-y-6">
                    {posts.map((post: Post) => (
                        <div key={post.id} className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
                            <h2 className="text-2xl font-bold mb-2">
                                <Link href={`/blog/${post.slug}`} className="text-gray-800 hover:text-blue-500">
                                    {post.title}
                                </Link>
                            </h2>
                            <p className="text-gray-600">{post.excerpt}</p>
                            <div className="text-sm text-gray-400 mt-4">
                                <span>Published on {new Date(post.published_at).toLocaleDateString()}</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// src/app/blog/[slug]/page.tsx
import { getPostBySlug, getPosts } from '@/lib/api';
import { notFound } from 'next/navigation';

type Props = {
  params: { slug: string };
};

// This generates static pages at build time for better performance and SEO
export async function generateStaticParams() {
    try {
        const posts = await getPosts();
        return posts.results.map((post) => ({
            slug: post.slug,
        }));
    } catch(error) {
        console.error("Failed to generate static params:", error);
        return [];
    }
}

async function fetchPost(slug: string) {
    try {
        return await getPostBySlug(slug);
    } catch (error) {
        console.error(`Failed to fetch post with slug ${slug}:`, error);
        notFound();
    }
}

export default async function PostDetailPage({ params }: Props) {
    const post = await fetchPost(params.slug);

    return (
        <article className="bg-white p-8 rounded-lg shadow-md">
            <h1 className="text-4xl font-bold mb-4">{post.title}</h1>
            <div className="text-sm text-gray-500 mb-6">
                Published on {new Date(post.published_at).toLocaleDateString()} by {post.author}
            </div>
            <div
                className="prose lg:prose-xl max-w-none"
                dangerouslySetInnerHTML={{ __html: post.content }}
            />
        </article>
    );
}

// Add metadata generation for SEO
export async function generateMetadata({ params }: Props) {
    try {
        const post = await fetchPost(params.slug);
        return {
            title: post.title,
            description: post.excerpt,
        };
    } catch(error) {
        return {
            title: "Post not found",
            description: "This post could not be found.",
        }
    }
}

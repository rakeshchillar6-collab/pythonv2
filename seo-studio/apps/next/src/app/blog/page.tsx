// app/blog/page.tsx
import { getPosts } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import Link from 'next/link';

export default async function BlogIndex() {
  const posts = await getPosts();

  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold mb-8">Blog</h1>
      <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
        {posts.map((post) => (
          <Link href={`/${post.slug}`} key={post.id}>
            <Card className="h-full hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle>{post.meta.title}</CardTitle>
                <CardDescription>{new Date(post.updated_at).toLocaleDateString()}</CardDescription>
              </CardHeader>
              <CardContent>
                <p>{post.meta.seo_description}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </main>
  );
}

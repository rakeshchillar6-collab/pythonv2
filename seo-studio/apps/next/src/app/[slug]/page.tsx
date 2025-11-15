// app/[slug]/page.tsx
import { getPostBySlug } from '@/lib/api';
import { injectJsonLd } from '@/lib/schema';
import { RenderHTML } from '@/components/content/RenderHTML';
import { Metadata } from 'next';

type Props = {
  params: { slug: string };
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const post = await getPostBySlug(params.slug);
  return {
    title: post.meta.seo_title || post.meta.title,
    description: post.meta.seo_description,
    // ... add other metadata like canonical, open graph, etc.
  };
}

export default async function PostPage({ params }: Props) {
  const post = await getPostBySlug(params.slug);

  return (
    <>
      {injectJsonLd(post.jsonld)}
      <main className="container mx-auto px-4 py-8">
        <article>
          <h1 className="text-4xl font-bold mb-4">{post.meta.title}</h1>
          <RenderHTML html={post.html} />
        </article>
      </main>
    </>
  );
}

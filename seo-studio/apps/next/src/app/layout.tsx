// src/app/layout.tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../styles/globals.css'
import Link from 'next/link'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SEO Studio Blog',
  description: 'A blog powered by Django and Next.js',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-100">
          <nav className="bg-white shadow-md">
            <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
              <Link href="/" className="text-2xl font-bold text-gray-800">
                My Awesome Blog
              </Link>
              <div className="space-x-4">
                <Link href="/" className="text-gray-600 hover:text-blue-500">
                  Home
                </Link>
                <Link href="/blog" className="text-gray-600 hover:text-blue-500">
                  Blog
                </Link>
              </div>
            </div>
          </nav>
          <main className="max-w-4xl mx-auto px-4 py-8">
            {children}
          </main>
          <footer className="text-center py-4 text-gray-500 text-sm">
            <p>&copy; {new Date().getFullYear()} SEO Studio. All rights reserved.</p>
          </footer>
        </div>
      </body>
    </html>
  )
}

// src/lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// You can add interceptors for handling auth tokens here if needed
// For example:
// api.interceptors.request.use(config => {
//   const token = localStorage.getItem('accessToken');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

// Define types for our data
export interface Post {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  published_at: string;
  author: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// API functions
export const getPosts = async (): Promise<PaginatedResponse<Post>> => {
  const response = await api.get('/posts/');
  return response.data;
};

export const getPostBySlug = async (slug: string): Promise<Post> => {
  const response = await api.get(`/posts/${slug}/`);
  return response.data;
};

export default api;

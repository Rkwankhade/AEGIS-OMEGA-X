/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_PDT_API_URL: process.env.NEXT_PUBLIC_PDT_API_URL || 'http://localhost:8001',
    NEXT_PUBLIC_GENOME_API_URL: process.env.NEXT_PUBLIC_GENOME_API_URL || 'http://localhost:8002',
    NEXT_PUBLIC_KNOWLEDGE_API_URL: process.env.NEXT_PUBLIC_KNOWLEDGE_API_URL || 'http://localhost:8003',
    NEXT_PUBLIC_GATEWAY_URL: process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000',
  },
};
module.exports = nextConfig;

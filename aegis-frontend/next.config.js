// aegis-frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    optimizeCss: true,
  },
  images: {
    domains: [],
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_PDT_API_URL:       process.env.NEXT_PUBLIC_PDT_API_URL       || 'http://localhost:8001',
    NEXT_PUBLIC_GENOME_API_URL:    process.env.NEXT_PUBLIC_GENOME_API_URL    || 'http://localhost:8002',
    NEXT_PUBLIC_KNOWLEDGE_API_URL: process.env.NEXT_PUBLIC_KNOWLEDGE_API_URL || 'http://localhost:8003',
    NEXT_PUBLIC_GATEWAY_URL:       process.env.NEXT_PUBLIC_GATEWAY_URL       || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL:            process.env.NEXT_PUBLIC_WS_URL            || 'ws://localhost:8001/ws',
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options',           value: 'DENY' },
          { key: 'X-Content-Type-Options',     value: 'nosniff' },
          { key: 'Referrer-Policy',            value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy',         value: 'camera=(), microphone=(), geolocation=()' },
          { key: 'X-XSS-Protection',           value: '1; mode=block' },
        ],
      },
    ];
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;

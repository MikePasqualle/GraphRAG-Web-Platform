/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  // Remove deprecated experimental.appDir and unused env vars
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
  webpack: (config) => {
    // Налаштування для Cytoscape.js
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
    };
    return config;
  },
  images: {
    domains: ['localhost'],
    unoptimized: true,
  },
  // Налаштування для production
  output: 'standalone',
  poweredByHeader: false,
  compress: true,
  trailingSlash: false,
  // Додаткові налаштування для Docker
  generateEtags: false,
  distDir: '.next',
};

module.exports = nextConfig;

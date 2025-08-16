const path = require('path');
const TsconfigPathsPlugin = require('tsconfig-paths-webpack-plugin');
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
    // Явний alias для "@" → "src" щоб Webpack розумів імпортні шляхи
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      '@': path.resolve(__dirname, 'src'),
    };

    // Дозволяємо Webpack враховувати tsconfig.json paths (дублюємо для надійності)
    config.resolve.plugins = config.resolve.plugins || [];
    config.resolve.plugins.push(
      new TsconfigPathsPlugin({
        configFile: path.resolve(__dirname, 'tsconfig.json'),
      })
    );

    // Гарантуємо пошук модулів також у src/
    config.resolve.modules = [
      path.resolve(__dirname, 'src'),
      'node_modules',
      ...(config.resolve.modules || []),
    ];
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

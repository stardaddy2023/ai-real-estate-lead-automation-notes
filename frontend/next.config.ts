import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';

const nextConfig: NextConfig = {
  output: 'standalone', // Required for Docker deployment
  async rewrites() {
    return [
      {
        source: '/api/v1/recorder/:path*',
        destination: `${backendUrl}/api/v1/recorder/:path*`,
      },
      {
        source: '/scout/:path*',
        destination: `${backendUrl}/scout/:path*`,
      },
    ];
  },
};

export default nextConfig;

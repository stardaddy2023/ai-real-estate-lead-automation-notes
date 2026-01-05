import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/v1/recorder/:path*',
        destination: 'http://127.0.0.1:8000/api/v1/recorder/:path*',
      },
      {
        source: '/scout/:path*',
        destination: 'http://127.0.0.1:8000/scout/:path*',
      },
    ];
  },
};

export default nextConfig;

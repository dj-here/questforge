/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    const apiTarget = process.env.NEXT_PUBLIC_API_URL;
    // If no external API URL is configured, use Next.js native serverless Route Handlers
    if (!apiTarget) {
      return [];
    }
    return [
      {
        source: "/auth/:path*",
        destination: `${apiTarget}/auth/:path*`,
      },
      {
        source: "/generation-jobs/:path*",
        destination: `${apiTarget}/generation-jobs/:path*`,
      },
      {
        source: "/generation-jobs",
        destination: `${apiTarget}/generation-jobs`,
      },
      {
        source: "/questions/:path*",
        destination: `${apiTarget}/questions/:path*`,
      },
      {
        source: "/questions",
        destination: `${apiTarget}/questions`,
      },
      {
        source: "/publish/:path*",
        destination: `${apiTarget}/publish/:path*`,
      },
      {
        source: "/health",
        destination: `${apiTarget}/health`,
      },
      {
        source: "/metrics",
        destination: `${apiTarget}/metrics`,
      },
      {
        source: "/api/v1/:path*",
        destination: `${apiTarget}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

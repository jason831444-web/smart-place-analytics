/** @type {import('next').NextConfig} */
const nextConfig = {
  turbopack: {
    root: new URL(".", import.meta.url).pathname
  },
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/media/**"
      }
    ]
  }
};

export default nextConfig;


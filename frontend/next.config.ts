import type { NextConfig } from "next";

const backendUrl = (process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`, // 백엔드 서버 프록시 (로컬 또는 EC2 배포 주소)
      },
    ];
  },
  // 모바일 접속을 허용하기 위한 설정 (Next.js 보안 정책 우회)
  allowedDevOrigins: ['192.168.45.212', '192.168.219.103', 'localhost'],
};

export default nextConfig;

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function DashboardRoutePage() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/');
  }, [router]);
  return (
    <div className="p-6">
      <p className="text-gray-600">Redirecting to dashboard…</p>
    </div>
  );
}

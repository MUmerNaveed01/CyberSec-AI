import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-zinc-950 text-slate-100 p-4">
      <AlertTriangle className="w-16 h-16 text-cyan-500 mb-6" />
      <h1 className="text-4xl font-bold mb-2">404 - Target Not Found</h1>
      <p className="text-slate-400 mb-8 max-w-md text-center">
        The requested resource could not be located in our systems. It may have been removed or the path is incorrect.
      </p>
      <Button asChild>
        <Link href="/dashboard">Return to Dashboard</Link>
      </Button>
    </div>
  );
}
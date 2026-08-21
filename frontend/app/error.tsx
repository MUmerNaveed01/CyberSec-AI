'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-zinc-950 text-slate-100 p-4">
      <AlertCircle className="w-16 h-16 text-red-500 mb-6" />
      <h1 className="text-4xl font-bold mb-2">System Error</h1>
      <p className="text-slate-400 mb-8 max-w-md text-center">
        A critical error occurred while processing your request. Our systems have logged this event.
      </p>
      <Button onClick={() => reset()} variant="destructive">
        Attempt Recovery
      </Button>
    </div>
  );
}
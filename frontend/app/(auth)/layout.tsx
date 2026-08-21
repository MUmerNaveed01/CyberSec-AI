export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="auth-shell min-h-screen flex items-center justify-center bg-zinc-950 bg-gradient-to-br from-[#070b12] via-[#0a111c] to-[#10252d] p-4">
      {children}
    </div>
  );
}
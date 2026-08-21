'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { LayoutDashboard, FolderKanban, Server, Scan, ShieldAlert, FileText, Settings, ChevronLeft, ChevronRight, LogOut, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/auth-context';

const navItems = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Assets', href: '/assets', icon: Server },
  { name: 'Scans', href: '/scans', icon: Scan },
  { name: 'Findings', href: '/findings', icon: ShieldAlert },
  { name: 'Reports', href: '/reports', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar({ isOpen, setIsOpen }: { isOpen: boolean; setIsOpen: (val: boolean) => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const initials = user?.name
    ? user.name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  return (
    <div className={cn('app-sidebar fixed inset-y-0 left-0 z-40 flex flex-col border-r border-slate-800/80 bg-[#080d15] transition-all duration-300 lg:static', isOpen ? 'w-64' : 'w-20', isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0')}>
      <div className="flex h-16 items-center justify-between border-b border-slate-800/80 px-4">
        {isOpen && <div className="flex items-center gap-2"><span className="landing-brand-mark"><Shield className="h-4 w-4" /></span><div><span className="block text-sm font-semibold text-white">CyberShield AI</span><span className="block text-[9px] uppercase tracking-[0.16em] text-slate-600">Security console</span></div></div>}
        <Button variant="ghost" size="icon" onClick={() => setIsOpen(!isOpen)} className="text-slate-400 hover:text-cyan-300" aria-label={isOpen ? 'Collapse navigation' : 'Expand navigation'}>
          {isOpen ? <ChevronLeft /> : <ChevronRight />}
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-6">
        {isOpen && <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">Workspace</p>}
        <div className="space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link key={item.name} href={item.href} className={cn('group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors', isActive ? 'bg-cyan-400/10 text-cyan-300 ring-1 ring-inset ring-cyan-400/15' : 'text-slate-500 hover:bg-slate-900/80 hover:text-slate-200')}>
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {isOpen && <span>{item.name}</span>}
            </Link>
          );
        })}
        </div>
      </div>

      <div className="border-t border-slate-800/80 p-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-sm text-white flex-shrink-0">
            {initials}
          </div>
          {isOpen && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-100 truncate">{user?.name ?? 'User'}</p>
              <p className="text-xs text-slate-500 truncate">{user?.email ?? ''}</p>
            </div>
          )}
          {isOpen && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-slate-500 hover:text-red-400 flex-shrink-0"
              title="Log out"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
'use client';

import { Bell, LogOut, Menu, User as UserIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/context/auth-context';

interface HeaderProps {
  title?: string;
  toggleSidebar?: () => void;
}

export function Header({ title = 'Dashboard', toggleSidebar }: HeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className="app-header sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        {toggleSidebar && <Button variant="ghost" size="icon" onClick={toggleSidebar} className="text-slate-400 hover:text-cyan-300 lg:hidden" aria-label="Open navigation"><Menu className="h-5 w-5" /></Button>}
        <div><p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-cyan-400/80">Security Operations</p><h1 className="text-lg font-semibold tracking-tight text-slate-100">{title}</h1></div>
      </div>

      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="relative text-slate-400 hover:text-slate-100">
          <Bell className="h-5 w-5" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-cyan-500" />
        </Button>

        {user ? (
          <div className="flex items-center gap-3 border-l border-slate-800 pl-4">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-medium text-xs">
                {user.name ? user.name.slice(0, 2).toUpperCase() : 'U'}
              </div>
              <div className="hidden md:block text-left">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-slate-200 leading-none">{user.name}</p>
                  <Badge variant="outline" className="text-[10px] py-0 px-1 border-cyan-500/30 text-cyan-400">
                    {user.role}
                  </Badge>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">{user.email}</p>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => logout()}
              title="Sign Out"
              className="text-slate-400 hover:text-red-400"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
              <UserIcon className="h-4 w-4" />
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
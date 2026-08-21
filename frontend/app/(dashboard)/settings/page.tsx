'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/context/auth-context';
import {
  Settings, User, Shield, Database, Server, Activity,
  FolderKanban, Scan, ShieldAlert, Users, Key, LogOut
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';

interface PlatformStats {
  users: number;
  projects: number;
  assets: number;
  scans: number;
  findings: number;
  audit_logs: number;
  version: string;
  app_name: string;
}

function StatCard({ icon: Icon, label, value, color }: {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="bg-zinc-900 border border-slate-800 rounded-xl p-5 flex items-center gap-4">
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-100">{value}</p>
        <p className="text-sm text-slate-400">{label}</p>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'profile' | 'platform' | 'security'>('profile');

  useEffect(() => {
    apiClient.get('/api/v1/admin/stats')
      .then(res => setStats(res.data))
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const tabs = [
    { id: 'profile', label: 'My Profile', icon: User },
    { id: 'platform', label: 'Platform Info', icon: Server },
    { id: 'security', label: 'Security', icon: Shield },
  ] as const;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-slate-700/50 flex items-center justify-center">
          <Settings className="w-5 h-5 text-slate-300" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Settings</h1>
          <p className="text-slate-400 text-sm">Manage your account and platform configuration</p>
        </div>
      </div>

      {/* Tab Nav */}
      <div className="flex gap-1 bg-zinc-900 border border-slate-800 rounded-lg p-1 w-fit">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="space-y-4">
          <div className="bg-zinc-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-2xl font-bold text-white">
                {user?.name?.charAt(0).toUpperCase() ?? 'U'}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-100">{user?.name ?? '—'}</h2>
                <p className="text-slate-400">{user?.email ?? '—'}</p>
                <span className={`inline-flex items-center gap-1 mt-1 text-xs px-2 py-0.5 rounded-full font-medium ${
                  user?.role === 'ADMIN'
                    ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                    : user?.role === 'ANALYST'
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                    : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                }`}>
                  <Shield className="w-3 h-3" />
                  {user?.role ?? 'VIEWER'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-slate-500 mb-1 uppercase tracking-wide">Full Name</label>
                <div className="bg-zinc-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm">
                  {user?.name ?? '—'}
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1 uppercase tracking-wide">Email Address</label>
                <div className="bg-zinc-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm">
                  {user?.email ?? '—'}
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1 uppercase tracking-wide">Role</label>
                <div className="bg-zinc-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm">
                  {user?.role ?? '—'}
                </div>
              </div>
              <div>
                <label className="block text-xs text-slate-500 mb-1 uppercase tracking-wide">Account Status</label>
                <div className="bg-zinc-950 border border-slate-700 rounded-lg px-3 py-2 text-sm">
                  <span className="text-emerald-400 font-medium">● Active</span>
                </div>
              </div>
            </div>
          </div>

          {/* Danger zone */}
          <div className="bg-zinc-900 border border-red-900/30 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-red-400 mb-3 flex items-center gap-2">
              <LogOut className="w-4 h-4" />
              Session
            </h3>
            <p className="text-slate-400 text-sm mb-4">
              Sign out from all devices by logging out of your current session.
            </p>
            <Button
              onClick={handleLogout}
              variant="outline"
              className="border-red-800 text-red-400 hover:bg-red-900/20"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Log Out
            </Button>
          </div>
        </div>
      )}

      {/* Platform Tab */}
      {activeTab === 'platform' && (
        <div className="space-y-4">
          <div className="bg-zinc-900 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-slate-100">Platform Overview</h2>
                <p className="text-slate-400 text-sm">Live counts across the entire platform</p>
              </div>
              {stats && (
                <div className="text-xs text-slate-500 bg-zinc-800 px-3 py-1 rounded-full">
                  v{stats.version}
                </div>
              )}
            </div>

            {loading ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="bg-zinc-800 rounded-xl p-5 h-20 animate-pulse" />
                ))}
              </div>
            ) : stats ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <StatCard icon={Users} label="Total Users" value={stats.users} color="bg-purple-500/10 text-purple-400" />
                <StatCard icon={FolderKanban} label="Projects" value={stats.projects} color="bg-cyan-500/10 text-cyan-400" />
                <StatCard icon={Server} label="Assets" value={stats.assets} color="bg-blue-500/10 text-blue-400" />
                <StatCard icon={Scan} label="Total Scans" value={stats.scans} color="bg-amber-500/10 text-amber-400" />
                <StatCard icon={ShieldAlert} label="Findings" value={stats.findings} color="bg-red-500/10 text-red-400" />
                <StatCard icon={Activity} label="Audit Events" value={stats.audit_logs} color="bg-emerald-500/10 text-emerald-400" />
              </div>
            ) : (
              <div className="text-center py-10">
                <Server className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">Stats require Admin access or backend connection.</p>
              </div>
            )}
          </div>

          <div className="bg-zinc-900 border border-slate-800 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-4 flex items-center gap-2">
              <Database className="w-4 h-4 text-cyan-400" />
              Backend Configuration
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-2 border-b border-slate-800">
                <span className="text-slate-400">API Base URL</span>
                <span className="text-slate-200 font-mono">{process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-800">
                <span className="text-slate-400">Database</span>
                <span className="text-emerald-400">SQLite (local dev)</span>
              </div>
              <div className="flex justify-between py-2 border-b border-slate-800">
                <span className="text-slate-400">Authentication</span>
                <span className="text-slate-200">JWT (HS256)</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-slate-400">Password Hashing</span>
                <span className="text-slate-200">Argon2id</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Security Tab */}
      {activeTab === 'security' && (
        <div className="space-y-4">
          <div className="bg-zinc-900 border border-slate-800 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-slate-100 mb-1">Security Information</h2>
            <p className="text-slate-400 text-sm mb-6">Your account security details and active protections.</p>

            <div className="space-y-3">
              {[
                { label: 'Password Hashing', detail: 'Argon2id — memory-hard, GPU-resistant', status: 'secure' },
                { label: 'Access Tokens', detail: 'JWT (HS256) — 15 minute expiry', status: 'secure' },
                { label: 'Refresh Tokens', detail: 'Rotating — 7 day expiry', status: 'secure' },
                { label: 'Role-Based Access Control', detail: 'ADMIN / ANALYST / VIEWER roles enforced server-side', status: 'secure' },
                { label: 'CORS Protection', detail: 'Only localhost:3000 is allowed (dev)', status: 'secure' },
                { label: 'Rate Limiting', detail: '60 requests/minute per IP', status: 'secure' },
                { label: 'Audit Logging', detail: 'All actions logged with IP and user agent', status: 'secure' },
                { label: 'SSRF Prevention', detail: 'Internal IP ranges blocked for scans', status: 'secure' },
              ].map(item => (
                <div key={item.label} className="flex items-start justify-between p-3 rounded-lg bg-zinc-800/50">
                  <div>
                    <p className="text-sm font-medium text-slate-200">{item.label}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{item.detail}</p>
                  </div>
                  <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full whitespace-nowrap">
                    <Shield className="w-3 h-3" />
                    Enabled
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-zinc-900 border border-amber-900/30 rounded-xl p-6">
            <h3 className="text-sm font-semibold text-amber-400 mb-3 flex items-center gap-2">
              <Key className="w-4 h-4" />
              Password Change
            </h3>
            <p className="text-slate-400 text-sm mb-4">
              Password changes are not yet available in this interface. Contact your administrator or use the API directly at{' '}
              <code className="text-cyan-400 bg-zinc-800 px-1 rounded text-xs">POST /api/v1/auth/change-password</code>.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

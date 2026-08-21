'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  ShieldAlert,
  ShieldCheck,
  Activity,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Loader2,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { apiClient, API_ROUTES } from '@/lib/api';
import { Project, Finding, Scan, PaginatedResponse } from '@/types';

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDashboardData = useCallback(async () => {
    try {
      setIsLoading(true);
      const [projRes, findRes, scanRes] = await Promise.all([
        apiClient.get<PaginatedResponse<Project>>(API_ROUTES.PROJECTS.LIST),
        apiClient.get<PaginatedResponse<Finding>>(API_ROUTES.FINDINGS.LIST),
        apiClient.get<PaginatedResponse<Scan>>(API_ROUTES.SCANS.LIST),
      ]);
      setProjects(projRes.data.items);
      setFindings(findRes.data.items);
      setScans(scanRes.data.items);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Aggregate Metrics
  const criticalCount = findings.filter((f) => f.severity === 'CRITICAL').length;
  const highCount = findings.filter((f) => f.severity === 'HIGH').length;
  const mediumCount = findings.filter((f) => f.severity === 'MEDIUM').length;
  const lowCount = findings.filter((f) => f.severity === 'LOW').length;

  const avgScore =
    projects.length > 0
      ? Math.round(
          projects.reduce((acc, p) => acc + (p.stats?.security_score ?? 100), 0) / projects.length
        )
      : 100;

  const severityChartData = [
    { name: 'Critical', value: criticalCount, color: '#e11d48' },
    { name: 'High', value: highCount, color: '#ea580c' },
    { name: 'Medium', value: mediumCount, color: '#f59e0b' },
    { name: 'Low', value: lowCount, color: '#06b6d4' },
  ].filter((d) => d.value > 0);

  const categoryCounts = findings.reduce((acc: Record<string, number>, f) => {
    acc[f.category] = (acc[f.category] || 0) + 1;
    return acc;
  }, {});

  const categoryChartData = Object.entries(categoryCounts).map(([cat, count]) => ({
    category: cat.slice(0, 10),
    count,
  }));

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100">Security Posture Dashboard</h2>
          <p className="text-sm text-slate-400">
            Real-time vulnerability metrics, project health scores, and scanner activity
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/projects">
            <Button variant="outline" className="border-slate-800 text-slate-300">
              Manage Projects
            </Button>
          </Link>
          <Link href="/scans">
            <Button className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold">
              New Scan
            </Button>
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card className="border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Average Security Score</span>
            <ShieldCheck className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-100">{avgScore}</span>
            <span className="text-xs text-slate-500">/ 100</span>
          </div>
        </Card>

        <Card className="border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-rose-400">Critical Findings</span>
            <AlertTriangle className="h-4 w-4 text-rose-500" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-rose-400">{criticalCount}</span>
            <span className="text-xs text-rose-500/80">Immediate Action</span>
          </div>
        </Card>

        <Card className="border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-orange-400">High Findings</span>
            <ShieldAlert className="h-4 w-4 text-orange-400" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold text-orange-400">{highCount}</span>
          </div>
        </Card>

        <Card className="border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-amber-400">Medium & Low</span>
            <Activity className="h-4 w-4 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-amber-400">{mediumCount + lowCount}</span>
            <span className="text-xs text-slate-500">Total</span>
          </div>
        </Card>

        <Card className="border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Scans Executed</span>
            <TrendingUp className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-2">
            <span className="text-2xl font-bold text-cyan-400">{scans.length}</span>
          </div>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-slate-200">
              Vulnerabilities by Severity
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Distribution of active risks across targets
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center">
            {severityChartData.length === 0 ? (
              <p className="text-xs text-slate-500">No vulnerabilities detected</p>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {severityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#020617',
                      borderColor: '#1e293b',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="text-sm font-semibold text-slate-200">
              Findings by Security Category
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Vulnerabilities mapped across defensive categories
            </CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            {categoryChartData.length === 0 ? (
              <div className="flex h-full items-center justify-center">
                <p className="text-xs text-slate-500">No category data available</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryChartData}>
                  <XAxis dataKey="category" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#020617',
                      borderColor: '#1e293b',
                      borderRadius: '8px',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="count" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Findings Preview */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base font-semibold text-slate-100">
              Highest Risk Vulnerabilities
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Issues requiring prioritized remediation
            </CardDescription>
          </div>
          <Link href="/findings" className="text-xs text-cyan-400 hover:underline flex items-center gap-1">
            View All ({findings.length}) <ArrowRight className="h-3 w-3" />
          </Link>
        </CardHeader>
        <CardContent>
          {findings.length === 0 ? (
            <p className="text-xs text-slate-500 py-4">No active findings.</p>
          ) : (
            <div className="space-y-2">
              {findings.slice(0, 5).map((f) => (
                <div
                  key={f.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-slate-950/60 border border-slate-800/80"
                >
                  <div className="flex items-center gap-3">
                    <Badge
                      variant="outline"
                      className={`text-[10px] ${
                        f.severity === 'CRITICAL'
                          ? 'text-rose-400 border-rose-500/30'
                          : f.severity === 'HIGH'
                          ? 'text-orange-400 border-orange-500/30'
                          : 'text-amber-400 border-amber-500/30'
                      }`}
                    >
                      {f.severity}
                    </Badge>
                    <div>
                      <p className="text-xs font-semibold text-slate-200">{f.title}</p>
                      <p className="text-[11px] text-slate-400">{f.category}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-mono font-semibold text-cyan-400">
                      Score: {f.risk_score}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
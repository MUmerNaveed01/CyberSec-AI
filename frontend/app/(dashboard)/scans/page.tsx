'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  Activity,
  Play,
  RotateCcw,
  Globe,
  Code,
  Loader2,
  XCircle,
  CheckCircle2,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { apiClient, API_ROUTES } from '@/lib/api';
import { Scan, ScanType, Project, Asset, PaginatedResponse } from '@/types';
import { formatDate } from '@/lib/utils';

export default function ScansPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLaunchModalOpen, setIsLaunchModalOpen] = useState(false);

  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [selectedAssetId, setSelectedAssetId] = useState<string>('');
  const [selectedScanType, setSelectedScanType] = useState<ScanType>('WEBSITE');
  const [launchError, setLaunchError] = useState<string | null>(null);
  const [isLaunching, setIsLaunching] = useState(false);

  const fetchScans = useCallback(async () => {
    try {
      const res = await apiClient.get<PaginatedResponse<Scan>>(API_ROUTES.SCANS.LIST);
      setScans(res.data.items);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchProjectsAndAssets = useCallback(async () => {
    try {
      const projRes = await apiClient.get<PaginatedResponse<Project>>(API_ROUTES.PROJECTS.LIST);
      setProjects(projRes.data.items);
      if (projRes.data.items.length > 0) {
        setSelectedProjectId(projRes.data.items[0].id);
      }
    } catch {
      // Fallback
    }
  }, []);

  useEffect(() => {
    fetchScans();
    fetchProjectsAndAssets();

    // Poll scans every 4 seconds for live updates
    const interval = setInterval(fetchScans, 4000);
    return () => clearInterval(interval);
  }, [fetchScans, fetchProjectsAndAssets]);

  useEffect(() => {
    if (!selectedProjectId) return;
    const fetchAssetsForProject = async () => {
      try {
        const res = await apiClient.get<PaginatedResponse<Asset>>(API_ROUTES.PROJECTS.ASSETS(selectedProjectId));
        setAssets(res.data.items);
        if (res.data.items.length > 0) {
          setSelectedAssetId(res.data.items[0].id);
        } else {
          setSelectedAssetId('');
        }
      } catch {
        setAssets([]);
      }
    };
    fetchAssetsForProject();
  }, [selectedProjectId]);

  const onLaunchScan = async () => {
    if (!selectedProjectId || !selectedAssetId) {
      setLaunchError('Please select both a project and an authorized asset.');
      return;
    }
    setLaunchError(null);
    setIsLaunching(true);
    try {
      await apiClient.post(API_ROUTES.SCANS.LIST, {
        project_id: selectedProjectId,
        asset_id: selectedAssetId,
        scan_type: selectedScanType,
      });
      setIsLaunchModalOpen(false);
      fetchScans();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: { message?: string } } } };
      setLaunchError(error.response?.data?.error?.message || 'Failed to start scan');
    } finally {
      setIsLaunching(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return (
          <Badge variant="outline" className="text-cyan-400 border-cyan-500/30 gap-1 bg-cyan-500/10">
            <Loader2 className="h-3 w-3 animate-spin" /> In Progress
          </Badge>
        );
      case 'COMPLETED':
        return (
          <Badge variant="outline" className="text-emerald-400 border-emerald-500/30 gap-1 bg-emerald-500/10">
            <CheckCircle2 className="h-3 w-3" /> Completed
          </Badge>
        );
      case 'FAILED':
        return (
          <Badge variant="outline" className="text-rose-400 border-rose-500/30 gap-1 bg-rose-500/10">
            <XCircle className="h-3 w-3" /> Failed
          </Badge>
        );
      case 'CANCELLED':
        return (
          <Badge variant="outline" className="text-slate-400 border-slate-700">
            Cancelled
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="text-amber-400 border-amber-500/30">
            Queued
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100">Security Scans</h2>
          <p className="text-sm text-slate-400">
            Launch, monitor, and review automated vulnerability scanning pipelines
          </p>
        </div>

        <Dialog open={isLaunchModalOpen} onOpenChange={setIsLaunchModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold gap-2">
              <Play className="h-4 w-4 fill-current" />
              Launch Assessment Scan
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[480px]">
            <DialogHeader>
              <DialogTitle>Launch Security Scan</DialogTitle>
              <DialogDescription>
                Select target asset and scanning engine to inspect for vulnerabilities.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-3">
              {launchError && (
                <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400 border border-red-500/20">
                  {launchError}
                </div>
              )}

              <div className="space-y-2">
                <Label className="text-slate-200">Security Project</Label>
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <Label className="text-slate-200">Target Asset</Label>
                {assets.length === 0 ? (
                  <p className="text-xs text-amber-400">No assets in this project. Please add an asset first.</p>
                ) : (
                  <select
                    value={selectedAssetId}
                    onChange={(e) => setSelectedAssetId(e.target.value)}
                    className="w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                  >
                    {assets.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.name} ({a.type})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div className="space-y-2">
                <Label className="text-slate-200">Scanner Engine</Label>
                <select
                  value={selectedScanType}
                  onChange={(e) => setSelectedScanType(e.target.value as ScanType)}
                  className="w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                >
                  <option value="WEBSITE">Website Security Scanner (Safe Headers, TLS, Cookies)</option>
                  <option value="SECRETS">Source Code Secrets Scanner (API Keys & Credentials)</option>
                  <option value="DEPENDENCIES">Dependency Vulnerability Scanner (Known CVEs)</option>
                </select>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsLaunchModalOpen(false)} className="border-slate-800">
                Cancel
              </Button>
              <Button
                onClick={onLaunchScan}
                disabled={isLaunching || !selectedAssetId}
                className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold"
              >
                {isLaunching ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Start Scan'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Scans Table */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <div>
            <CardTitle className="text-base font-semibold text-slate-100 flex items-center gap-2">
              <Activity className="h-4 w-4 text-cyan-400" />
              Scan History ({scans.length})
            </CardTitle>
            <CardDescription className="text-xs text-slate-400">
              Live status and results from security scanner workers
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchScans} className="text-xs text-slate-400 hover:text-slate-200">
            <RotateCcw className="h-3.5 w-3.5 mr-1" /> Refresh
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-cyan-500" />
            </div>
          ) : scans.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-slate-500">No scans executed yet. Click &apos;Launch Assessment Scan&apos; to begin.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="border-b border-slate-800 text-xs uppercase text-slate-500 bg-slate-950/40">
                  <tr>
                    <th className="px-4 py-3">Scan Type</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Progress</th>
                    <th className="px-4 py-3">Started</th>
                    <th className="px-4 py-3">Completed</th>
                    <th className="px-4 py-3">Errors / Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {scans.map((scan) => (
                    <tr key={scan.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 font-medium text-slate-100 flex items-center gap-2">
                        {scan.scan_type === 'WEBSITE' ? (
                          <Globe className="h-4 w-4 text-cyan-400" />
                        ) : (
                          <Code className="h-4 w-4 text-purple-400" />
                        )}
                        {scan.scan_type}
                      </td>
                      <td className="px-4 py-3">{getStatusBadge(scan.status)}</td>
                      <td className="px-4 py-3">
                        <div className="w-24 bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                          <div
                            className="bg-cyan-500 h-full transition-all duration-300"
                            style={{ width: `${scan.progress}%` }}
                          />
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-400">
                        {scan.started_at ? formatDate(scan.started_at) : 'Queued'}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-400">
                        {scan.completed_at ? formatDate(scan.completed_at) : '-'}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 max-w-xs truncate">
                        {scan.error_message || 'OK'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

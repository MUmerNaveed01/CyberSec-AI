'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import {
  Layers,
  Search,
  ShieldCheck,
  Globe,
  Code,
  FileCode,
  ExternalLink,
  Loader2,
  Trash2,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiClient, API_ROUTES } from '@/lib/api';
import { Asset, AssetType, PaginatedResponse } from '@/types';
import { formatDate } from '@/lib/utils';

export default function AssetsPage() {
  const [assets, setAssets] = useState<Asset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('ALL');

  const fetchAssets = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await apiClient.get<PaginatedResponse<Asset>>(API_ROUTES.ASSETS.DETAIL(''));
      setAssets(res.data.items);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);

  const onDeleteAsset = async (id: string) => {
    if (!confirm('Are you sure you want to remove this asset?')) return;
    try {
      await apiClient.delete(API_ROUTES.ASSETS.DETAIL(id));
      fetchAssets();
    } catch {
      alert('Failed to delete asset');
    }
  };

  const getAssetIcon = (type: AssetType) => {
    switch (type) {
      case 'WEBSITE':
        return <Globe className="h-4 w-4 text-cyan-400" />;
      case 'SOURCE_CODE':
        return <Code className="h-4 w-4 text-purple-400" />;
      case 'DEPENDENCY_MANIFEST':
        return <FileCode className="h-4 w-4 text-amber-400" />;
    }
  };

  const filteredAssets = assets.filter((asset) => {
    const matchesSearch =
      asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.target.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = selectedType === 'ALL' || asset.type === selectedType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100">Asset Inventory</h2>
          <p className="text-sm text-slate-400">
            Registered websites, repositories, and dependency manifests across all security projects
          </p>
        </div>
        <Link href="/projects">
          <Button className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold">
            Manage via Projects
          </Button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full max-w-sm">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search assets by name or target..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-900/60 border-slate-800 text-slate-100 placeholder:text-slate-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          {['ALL', 'WEBSITE', 'SOURCE_CODE', 'DEPENDENCY_MANIFEST'].map((t) => (
            <Button
              key={t}
              variant="outline"
              size="sm"
              onClick={() => setSelectedType(t)}
              className={`text-xs border-slate-800 ${
                selectedType === t
                  ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {t === 'ALL' ? 'All Types' : t.replace('_', ' ')}
            </Button>
          ))}
        </div>
      </div>

      {/* Assets Table */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <Layers className="h-4 w-4 text-cyan-400" />
            Inventory ({filteredAssets.length})
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Targets confirmed for defensive security analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-cyan-500" />
            </div>
          ) : filteredAssets.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-slate-500">No assets found matching the criteria.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="border-b border-slate-800 text-xs uppercase text-slate-500 bg-slate-950/40">
                  <tr>
                    <th className="px-4 py-3">Asset</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Target</th>
                    <th className="px-4 py-3">Authorization</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Added</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredAssets.map((asset) => (
                    <tr key={asset.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 font-medium text-slate-100 flex items-center gap-2">
                        {getAssetIcon(asset.type)}
                        {asset.name}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="text-[11px] border-slate-700">
                          {asset.type}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-cyan-400">
                        {asset.type === 'WEBSITE' ? (
                          <a
                            href={asset.target}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-center gap-1 hover:underline"
                          >
                            {asset.target}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          asset.target
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center gap-1 text-emerald-400 text-xs">
                          <ShieldCheck className="h-3.5 w-3.5" /> Confirmed
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant="outline"
                          className={
                            asset.status === 'ACTIVE'
                              ? 'text-emerald-400 border-emerald-500/30'
                              : 'text-slate-400 border-slate-700'
                          }
                        >
                          {asset.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">
                        {formatDate(asset.created_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => onDeleteAsset(asset.id)}
                          className="text-slate-500 hover:text-red-400 h-7 w-7"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
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

'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  FolderLock,
  Plus,
  ShieldAlert,
  Globe,
  Code,
  FileCode,
  ArrowLeft,
  Loader2,
  Trash2,
  ExternalLink,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { apiClient, API_ROUTES } from '@/lib/api';
import { Project, Asset, AssetType, PaginatedResponse } from '@/types';
import { formatDate } from '@/lib/utils';

const assetSchema = z.object({
  name: z.string().min(2, 'Asset name must be at least 2 characters').max(100),
  type: z.enum(['WEBSITE', 'SOURCE_CODE', 'DEPENDENCY_MANIFEST'] as const),
  target: z.string().min(1, 'Target is required').max(1000),
  description: z.string().max(500).optional(),
  authorization_confirmed: z.boolean().refine((val) => val === true, {
    message: 'You must confirm authorization before registering this asset',
  }),
});

type AssetFormValues = z.infer<typeof assetSchema>;

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAssetModalOpen, setIsAssetModalOpen] = useState(false);
  const [assetError, setAssetError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AssetFormValues>({
    resolver: zodResolver(assetSchema),
    defaultValues: {
      name: '',
      type: 'WEBSITE',
      target: '',
      description: '',
      authorization_confirmed: false,
    },
  });

  const fetchData = useCallback(async () => {
    if (!projectId) return;
    try {
      setIsLoading(true);
      const [projRes, assetsRes] = await Promise.all([
        apiClient.get<Project>(API_ROUTES.PROJECTS.DETAIL(projectId)),
        apiClient.get<PaginatedResponse<Asset>>(API_ROUTES.PROJECTS.ASSETS(projectId)),
      ]);
      setProject(projRes.data);
      setAssets(assetsRes.data.items);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const onAddAsset = async (data: AssetFormValues) => {
    setAssetError(null);
    try {
      await apiClient.post(API_ROUTES.PROJECTS.ASSETS(projectId), data);
      setIsAssetModalOpen(false);
      reset();
      fetchData();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: { message?: string } } } };
      setAssetError(error.response?.data?.error?.message || 'Failed to add asset');
    }
  };

  const onDeleteAsset = async (assetId: string) => {
    if (!confirm('Are you sure you want to remove this asset?')) return;
    try {
      await apiClient.delete(API_ROUTES.ASSETS.DETAIL(assetId));
      fetchData();
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

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-cyan-500" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Project not found</p>
        <Button
          onClick={() => router.push('/projects')}
          variant="outline"
          className="mt-4 border-slate-800"
        >
          Back to Projects
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/projects')}
            className="text-slate-400 hover:text-slate-100"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-2xl font-bold tracking-tight text-slate-100">{project.name}</h2>
              <Badge variant="outline" className="text-slate-400 border-slate-700 text-xs">
                {project.status}
              </Badge>
            </div>
            <p className="text-sm text-slate-400 mt-0.5">
              {project.description || 'Project workspace for authorized security assessments.'}
            </p>
          </div>
        </div>

        {/* Add Asset Modal */}
        <Dialog open={isAssetModalOpen} onOpenChange={setIsAssetModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold gap-2">
              <Plus className="h-4 w-4" />
              Register Asset
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[520px]">
            <form onSubmit={handleSubmit(onAddAsset)}>
              <DialogHeader>
                <DialogTitle>Register Authorized Target Asset</DialogTitle>
                <DialogDescription>
                  Specify the target system or source manifest to be tested under this project.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {assetError && (
                  <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400 border border-red-500/20">
                    {assetError}
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="asset-name" className="text-slate-200">
                    Asset Name
                  </Label>
                  <Input
                    id="asset-name"
                    placeholder="e.g. Production Web App or Core API"
                    className="bg-slate-950 border-slate-800 text-slate-100"
                    {...register('name')}
                  />
                  {errors.name && <p className="text-xs text-red-400">{errors.name.message}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="asset-type" className="text-slate-200">
                    Asset Type
                  </Label>
                  <select
                    id="asset-type"
                    className="w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    {...register('type')}
                  >
                    <option value="WEBSITE">Website / Web Service (URL)</option>
                    <option value="SOURCE_CODE">Source Code Repository / Path</option>
                    <option value="DEPENDENCY_MANIFEST">Dependency Manifest (e.g. package.json, requirements.txt)</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target" className="text-slate-200">
                    Target URI / Identifier
                  </Label>
                  <Input
                    id="target"
                    placeholder="https://example.com or ./manifests/package.json"
                    className="bg-slate-950 border-slate-800 text-slate-100"
                    {...register('target')}
                  />
                  {errors.target && <p className="text-xs text-red-400">{errors.target.message}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="asset-desc" className="text-slate-200">
                    Description (Optional)
                  </Label>
                  <Input
                    id="asset-desc"
                    placeholder="Main customer gateway"
                    className="bg-slate-950 border-slate-800 text-slate-100"
                    {...register('description')}
                  />
                </div>

                {/* Explicit Authorization Confirmation Checkbox */}
                <div className="rounded-lg bg-amber-500/10 p-3.5 border border-amber-500/20 space-y-2">
                  <div className="flex items-start gap-2.5">
                    <input
                      type="checkbox"
                      id="auth-confirm"
                      className="mt-1 h-4 w-4 rounded border-slate-700 bg-slate-950 text-cyan-500 focus:ring-cyan-500"
                      {...register('authorization_confirmed')}
                    />
                    <label htmlFor="auth-confirm" className="text-xs text-amber-200 leading-relaxed cursor-pointer select-none">
                      <strong className="font-semibold text-amber-100">Mandatory Authorization:</strong> I confirm that I own this target or have explicit, documented authorization to perform defensive security assessments against it.
                    </label>
                  </div>
                  {errors.authorization_confirmed && (
                    <p className="text-xs text-red-400">{errors.authorization_confirmed.message}</p>
                  )}
                </div>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsAssetModalOpen(false)}
                  className="border-slate-800 text-slate-300"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Registering...
                    </>
                  ) : (
                    'Register Asset'
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Assets Table/Card Inventory */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <FolderLock className="h-5 w-5 text-cyan-400" />
            Registered Assets ({assets.length})
          </CardTitle>
          <CardDescription className="text-slate-400 text-xs">
            Targets configured for automated vulnerability scanning and risk analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          {assets.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-slate-500">No assets registered in this project yet.</p>
              <Button
                onClick={() => setIsAssetModalOpen(true)}
                variant="outline"
                className="mt-3 border-slate-800 text-slate-300 text-xs"
              >
                Register First Asset
              </Button>
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
                    <th className="px-4 py-3">Created</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {assets.map((asset) => (
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
                          <ShieldAlert className="h-3.5 w-3.5" /> Confirmed
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

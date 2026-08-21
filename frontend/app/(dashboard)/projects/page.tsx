'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  FolderLock,
  Plus,
  Search,
  ShieldCheck,
  Layers,
  Activity,
  AlertTriangle,
  Loader2,
  Calendar,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Project, PaginatedResponse } from '@/types';
import { formatDate } from '@/lib/utils';

const projectSchema = z.object({
  name: z.string().min(2, 'Project name must be at least 2 characters').max(100),
  description: z.string().max(500).optional(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: { name: '', description: '' },
  });

  const fetchProjects = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await apiClient.get<PaginatedResponse<Project>>(API_ROUTES.PROJECTS.LIST);
      setProjects(res.data.items);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const onCreateProject = async (data: ProjectFormValues) => {
    setCreateError(null);
    try {
      await apiClient.post(API_ROUTES.PROJECTS.LIST, data);
      setIsModalOpen(false);
      reset();
      fetchProjects();
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: { message?: string } } } };
      setCreateError(error.response?.data?.error?.message || 'Failed to create project');
    }
  };

  const filteredProjects = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100">Security Projects</h2>
          <p className="text-sm text-slate-400">
            Create assessment scopes, register authorized assets, and monitor security posture
          </p>
        </div>

        <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold gap-2">
              <Plus className="h-4 w-4" />
              New Project
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[480px]">
            <form onSubmit={handleSubmit(onCreateProject)}>
              <DialogHeader>
                <DialogTitle>Create Security Project</DialogTitle>
                <DialogDescription>
                  Define a project workspace to group and scan related applications and domains.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {createError && (
                  <div className="rounded-lg bg-red-500/10 p-3 text-sm text-red-400 border border-red-500/20">
                    {createError}
                  </div>
                )}
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-slate-200">
                    Project Name
                  </Label>
                  <Input
                    id="name"
                    placeholder="e.g. Production Web Platform"
                    className="bg-slate-950 border-slate-800 text-slate-100"
                    {...register('name')}
                  />
                  {errors.name && <p className="text-xs text-red-400">{errors.name.message}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description" className="text-slate-200">
                    Description (Optional)
                  </Label>
                  <Input
                    id="description"
                    placeholder="Primary user-facing portals & microservices"
                    className="bg-slate-950 border-slate-800 text-slate-100"
                    {...register('description')}
                  />
                  {errors.description && (
                    <p className="text-xs text-red-400">{errors.description.message}</p>
                  )}
                </div>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsModalOpen(false)}
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
                      Creating...
                    </>
                  ) : (
                    'Create Workspace'
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-900/60 border-slate-800 text-slate-100 placeholder:text-slate-500"
          />
        </div>
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-56 rounded-xl border border-slate-800/80 bg-slate-900/40 animate-pulse"
            />
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        <Card className="border-dashed border-slate-800 bg-slate-900/20 py-12 text-center">
          <CardContent className="flex flex-col items-center justify-center space-y-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-slate-800/80 text-slate-400">
              <FolderLock className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-medium text-slate-200">No projects found</h3>
              <p className="text-sm text-slate-500 max-w-sm">
                Get started by creating your first security assessment workspace.
              </p>
            </div>
            <Button
              onClick={() => setIsModalOpen(true)}
              className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-medium"
            >
              Create Project
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => {
            const stats = project.stats || {
              security_score: 100,
              assets_count: 0,
              scans_count: 0,
              critical_findings: 0,
              high_findings: 0,
            };

            const getScoreColor = (score: number) => {
              if (score >= 80) return 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10';
              if (score >= 60) return 'text-amber-400 border-amber-500/20 bg-amber-500/10';
              return 'text-rose-400 border-rose-500/20 bg-rose-500/10';
            };

            return (
              <Card
                key={project.id}
                className="border-slate-800 bg-slate-900/50 hover:border-slate-700 transition-all flex flex-col justify-between"
              >
                <CardHeader className="space-y-2">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/20">
                        <FolderLock className="h-4 w-4" />
                      </div>
                      <CardTitle className="text-base font-semibold text-slate-100 hover:text-cyan-400 transition-colors">
                        <Link href={`/projects/${project.id}`}>{project.name}</Link>
                      </CardTitle>
                    </div>
                    <Badge variant="outline" className="text-slate-400 border-slate-700 text-xs">
                      {project.status}
                    </Badge>
                  </div>
                  <CardDescription className="text-xs text-slate-400 line-clamp-2 min-h-[32px]">
                    {project.description || 'No description provided.'}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Security Score Banner */}
                  <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4 text-slate-400" />
                      <span className="text-xs text-slate-400">Security Score</span>
                    </div>
                    <div
                      className={`text-xs font-bold px-2 py-0.5 rounded-md border ${getScoreColor(
                        stats.security_score
                      )}`}
                    >
                      {stats.security_score} / 100
                    </div>
                  </div>

                  {/* Metrics Row */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-lg bg-slate-950/40 p-2 border border-slate-800/60">
                      <div className="flex items-center justify-center gap-1 text-slate-400 text-[11px]">
                        <Layers className="h-3 w-3" /> Assets
                      </div>
                      <p className="text-sm font-semibold text-slate-200 mt-0.5">
                        {stats.assets_count}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-950/40 p-2 border border-slate-800/60">
                      <div className="flex items-center justify-center gap-1 text-slate-400 text-[11px]">
                        <Activity className="h-3 w-3" /> Scans
                      </div>
                      <p className="text-sm font-semibold text-slate-200 mt-0.5">
                        {stats.scans_count}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-950/40 p-2 border border-slate-800/60">
                      <div className="flex items-center justify-center gap-1 text-red-400 text-[11px]">
                        <AlertTriangle className="h-3 w-3" /> Critical
                      </div>
                      <p className="text-sm font-semibold text-red-400 mt-0.5">
                        {stats.critical_findings}
                      </p>
                    </div>
                  </div>
                </CardContent>

                <CardFooter className="border-t border-slate-800/60 pt-3 flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    <span>{formatDate(project.created_at)}</span>
                  </div>
                  <Link
                    href={`/projects/${project.id}`}
                    className="text-cyan-400 hover:text-cyan-300 font-medium"
                  >
                    Open View →
                  </Link>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
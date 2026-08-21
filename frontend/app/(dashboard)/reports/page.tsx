'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  FileText,
  Plus,
  Download,
  Loader2,
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
import { Report, Project, ReportType, PaginatedResponse } from '@/types';
import { formatDate } from '@/lib/utils';

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false);

  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [selectedType, setSelectedType] = useState<'EXECUTIVE' | 'TECHNICAL' | 'FULL'>('EXECUTIVE');
  const [isGenerating, setIsGenerating] = useState(false);

  const [viewingReport, setViewingReport] = useState<Report | null>(null);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);

  const fetchReports = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await apiClient.get<PaginatedResponse<Report>>(API_ROUTES.REPORTS.LIST);
      setReports(res.data.items);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await apiClient.get<PaginatedResponse<Project>>(API_ROUTES.PROJECTS.LIST);
      setProjects(res.data.items);
      if (res.data.items.length > 0) {
        setSelectedProjectId(res.data.items[0].id);
      }
    } catch {
      // Fallback
    }
  }, []);

  useEffect(() => {
    fetchReports();
    fetchProjects();
  }, [fetchReports, fetchProjects]);

  const onGenerateReport = async () => {
    if (!selectedProjectId) return;
    setIsGenerating(true);
    try {
      await apiClient.post(API_ROUTES.REPORTS.LIST, {
        project_id: selectedProjectId,
        report_type: selectedType,
      });
      setIsGenerateModalOpen(false);
      fetchReports();
    } catch {
      alert('Failed to generate report');
    } finally {
      setIsGenerating(false);
    }
  };

  const onOpenReport = async (reportId: string) => {
    try {
      const res = await apiClient.get<Report>(API_ROUTES.REPORTS.DETAIL(reportId));
      setViewingReport(res.data);
      setIsViewModalOpen(true);
    } catch {
      alert('Could not load report content');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100">Security Reports</h2>
          <p className="text-sm text-slate-400">
            Generate and export Executive and Technical vulnerability assessment reports
          </p>
        </div>

        <Dialog open={isGenerateModalOpen} onOpenChange={setIsGenerateModalOpen}>
          <DialogTrigger asChild>
            <Button className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold gap-2">
              <Plus className="h-4 w-4" />
              Generate Security Report
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[480px]">
            <DialogHeader>
              <DialogTitle>Generate Assessment Report</DialogTitle>
              <DialogDescription>
                Compile vulnerability metrics and findings into an executive or technical document.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-3">
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
                <Label className="text-slate-200">Report Scope / Type</Label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value as ReportType)}
                  className="w-full rounded-md border border-slate-800 bg-slate-950 px-3 py-2 text-sm text-slate-100"
                >
                  <option value="EXECUTIVE">Executive Summary (High-level posture & risk overview)</option>
                  <option value="TECHNICAL">Technical Assessment (Detailed findings, CVEs, and remediation)</option>
                  <option value="FULL">Comprehensive Report (Complete Executive & Technical breakdown)</option>
                </select>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setIsGenerateModalOpen(false)} className="border-slate-800">
                Cancel
              </Button>
              <Button
                onClick={onGenerateReport}
                disabled={isGenerating || !selectedProjectId}
                className="bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-semibold"
              >
                {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Compile Report'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Reports Grid */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <FileText className="h-4 w-4 text-cyan-400" />
            Generated Reports ({reports.length})
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Exportable cybersecurity audit and remediation summaries
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-cyan-500" />
            </div>
          ) : reports.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-slate-500">No reports generated yet.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="border-b border-slate-800 text-xs uppercase text-slate-500 bg-slate-950/40">
                  <tr>
                    <th className="px-4 py-3">Report ID</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Generated Date</th>
                    <th className="px-4 py-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {reports.map((report) => (
                    <tr key={report.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-slate-300 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-cyan-400" />
                        {report.id.slice(0, 8)}...
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="text-xs border-cyan-500/30 text-cyan-400">
                          {report.report_type}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-400">
                        {formatDate(report.created_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onOpenReport(report.id)}
                          className="text-xs border-slate-800 hover:bg-slate-800 text-cyan-400"
                        >
                          View Report →
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

      {/* Report View Modal */}
      {viewingReport && (
        <Dialog open={isViewModalOpen} onOpenChange={setIsViewModalOpen}>
          <DialogContent className="sm:max-w-[750px] max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className="text-cyan-400 border-cyan-500/30">
                  {viewingReport.report_type}
                </Badge>
                <span className="text-xs text-slate-400">Date: {formatDate(viewingReport.created_at)}</span>
              </div>
              <DialogTitle className="text-lg font-bold text-slate-100">Cybersecurity Assessment Report</DialogTitle>
            </DialogHeader>

            <div className="py-4">
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">
                {viewingReport.content}
              </pre>
            </div>

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  const blob = new Blob([viewingReport.content || ''], { type: 'text/markdown' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `Security-Report-${viewingReport.id.slice(0, 8)}.md`;
                  a.click();
                }}
                className="gap-2 border-slate-800 text-cyan-400 hover:bg-slate-800"
              >
                <Download className="h-4 w-4" /> Download Markdown
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

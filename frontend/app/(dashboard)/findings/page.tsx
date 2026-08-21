'use client';

import React, { useEffect, useState, useCallback } from 'react';
import {
  ShieldAlert,
  Search,
  Bot,
  Loader2,
  Sparkles,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { apiClient, API_ROUTES } from '@/lib/api';
import { Finding, FindingStatus, AIAnalysis, PaginatedResponse } from '@/types';
import { formatDate } from '@/lib/utils';

export default function FindingsPage() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');

  const [activeFinding, setActiveFinding] = useState<Finding | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysis | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [isDetailOpen, setIsDetailOpen] = useState(false);

  const fetchFindings = useCallback(async () => {
    try {
      setIsLoading(true);
      const res = await apiClient.get<PaginatedResponse<Finding>>(API_ROUTES.FINDINGS.LIST);
      setFindings(res.data.items);
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFindings();
  }, [fetchFindings]);

  const onOpenDetail = async (finding: Finding) => {
    setActiveFinding(finding);
    setAiAnalysis(null);
    setIsDetailOpen(true);
  };

  const onRunAiAnalysis = async (findingId: string) => {
    setIsAiLoading(true);
    try {
      const res = await apiClient.post<AIAnalysis>(API_ROUTES.AI.ANALYZE(findingId));
      setAiAnalysis(res.data);
    } catch {
      alert('AI Analysis could not be generated');
    } finally {
      setIsAiLoading(false);
    }
  };

  const onUpdateStatus = async (findingId: string, newStatus: string) => {
    try {
      await apiClient.patch(API_ROUTES.FINDINGS.DETAIL(findingId), { status: newStatus });
      fetchFindings();
      if (activeFinding) {
        setActiveFinding({ ...activeFinding, status: newStatus as FindingStatus });
      }
    } catch {
      alert('Failed to update status');
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return <Badge variant="destructive" className="bg-rose-600 text-white font-semibold">CRITICAL</Badge>;
      case 'HIGH':
        return <Badge variant="destructive" className="bg-orange-600 text-white font-semibold">HIGH</Badge>;
      case 'MEDIUM':
        return <Badge variant="outline" className="text-amber-400 border-amber-500/30 bg-amber-500/10">MEDIUM</Badge>;
      case 'LOW':
        return <Badge variant="outline" className="text-cyan-400 border-cyan-500/30 bg-cyan-500/10">LOW</Badge>;
      default:
        return <Badge variant="outline" className="text-slate-400 border-slate-700">INFO</Badge>;
    }
  };

  const filteredFindings = findings.filter((f) => {
    const matchesSearch =
      f.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSeverity = selectedSeverity === 'ALL' || f.severity === selectedSeverity;
    return matchesSearch && matchesSeverity;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-100">Vulnerability Findings</h2>
          <p className="text-sm text-slate-400">
            Normalized security vulnerabilities, risk scores, evidence, and AI remediation guidance
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-center gap-4">
        <div className="relative flex-1 w-full max-w-sm">
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search findings by title or keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-900/60 border-slate-800 text-slate-100 placeholder:text-slate-500"
          />
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map((sev) => (
            <Button
              key={sev}
              variant="outline"
              size="sm"
              onClick={() => setSelectedSeverity(sev)}
              className={`text-xs border-slate-800 ${
                selectedSeverity === sev
                  ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {sev}
            </Button>
          ))}
        </div>
      </div>

      {/* Findings Table */}
      <Card className="border-slate-800 bg-slate-900/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-cyan-400" />
            Detected Findings ({filteredFindings.length})
          </CardTitle>
          <CardDescription className="text-xs text-slate-400">
            Click on any finding to review evidence, update remediation status, or trigger AI analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-32 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-cyan-500" />
            </div>
          ) : filteredFindings.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-sm text-slate-500">No vulnerability findings detected in scope.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="border-b border-slate-800 text-xs uppercase text-slate-500 bg-slate-950/40">
                  <tr>
                    <th className="px-4 py-3">Severity</th>
                    <th className="px-4 py-3">Title</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Risk Score</th>
                    <th className="px-4 py-3">Standards</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredFindings.map((finding) => (
                    <tr
                      key={finding.id}
                      onClick={() => onOpenDetail(finding)}
                      className="hover:bg-slate-800/30 transition-colors cursor-pointer"
                    >
                      <td className="px-4 py-3">{getSeverityBadge(finding.severity)}</td>
                      <td className="px-4 py-3 font-medium text-slate-100 max-w-sm truncate">
                        {finding.title}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-400">{finding.category}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-cyan-400">
                        {finding.risk_score}
                      </td>
                      <td className="px-4 py-3 text-xs font-mono text-slate-400">
                        {finding.cve || finding.cwe || '-'}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="text-[10px] border-slate-700">
                          {finding.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right text-xs text-cyan-400 font-medium">
                        Investigate →
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Finding Detail & AI Analyst Modal */}
      {activeFinding && (
        <Dialog open={isDetailOpen} onOpenChange={setIsDetailOpen}>
          <DialogContent className="sm:max-w-[700px] max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <div className="flex items-center gap-2 mb-1">
                {getSeverityBadge(activeFinding.severity)}
                <span className="text-xs text-slate-400">Risk Score: {activeFinding.risk_score}/10</span>
              </div>
              <DialogTitle className="text-lg font-bold text-slate-100">{activeFinding.title}</DialogTitle>
              <DialogDescription className="text-xs text-slate-400">
                {activeFinding.category} | First seen {formatDate(activeFinding.first_seen_at)}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-3 text-sm">
              {/* Description */}
              <div className="space-y-1">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Description</h4>
                <p className="text-slate-300 text-xs leading-relaxed">{activeFinding.description}</p>
              </div>

              {/* Evidence */}
              <div className="space-y-1">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Evidence & Technical Indicators</h4>
                <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-cyan-300 overflow-x-auto">
                  {JSON.stringify(activeFinding.evidence, null, 2)}
                </pre>
              </div>

              {/* Remediation */}
              <div className="space-y-1">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Recommended Remediation</h4>
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-200 leading-relaxed">
                  {activeFinding.remediation}
                </div>
              </div>

              {/* Status Selector */}
              <div className="flex items-center gap-3 pt-2 border-t border-slate-800">
                <span className="text-xs text-slate-400">Update Status:</span>
                {['OPEN', 'IN_PROGRESS', 'RESOLVED', 'ACCEPTED_RISK', 'FALSE_POSITIVE'].map((st) => (
                  <Button
                    key={st}
                    size="sm"
                    variant="outline"
                    onClick={() => onUpdateStatus(activeFinding.id, st)}
                    className={`text-[11px] h-7 border-slate-800 ${
                      activeFinding.status === st
                        ? 'bg-cyan-500 text-slate-950 font-bold border-cyan-500'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {st}
                  </Button>
                ))}
              </div>

              {/* AI Security Analyst Section */}
              <div className="pt-3 border-t border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Bot className="h-4 w-4 text-purple-400" />
                    <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">AI Security Analyst</h4>
                  </div>
                  {!aiAnalysis && (
                    <Button
                      size="sm"
                      onClick={() => onRunAiAnalysis(activeFinding.id)}
                      disabled={isAiLoading}
                      className="bg-purple-600 hover:bg-purple-700 text-white font-medium text-xs h-8 gap-1.5"
                    >
                      {isAiLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                      Generate AI Analysis
                    </Button>
                  )}
                </div>

                {aiAnalysis && (
                  <div className="rounded-xl border border-purple-500/30 bg-purple-950/20 p-4 space-y-3 text-xs">
                    <div className="flex items-center justify-between text-purple-300">
                      <span className="font-semibold">{aiAnalysis.priority}</span>
                      <span className="text-[10px] text-purple-400 font-mono">Engine: {aiAnalysis.model}</span>
                    </div>
                    <div>
                      <p className="font-medium text-slate-200 mb-1">Executive Summary:</p>
                      <p className="text-slate-300 leading-relaxed">{aiAnalysis.summary}</p>
                    </div>
                    <div>
                      <p className="font-medium text-slate-200 mb-1">Business Impact:</p>
                      <p className="text-slate-300 leading-relaxed">{aiAnalysis.business_impact}</p>
                    </div>
                    <div>
                      <p className="font-medium text-slate-200 mb-1">Technical Deep Dive:</p>
                      <p className="text-slate-300 leading-relaxed">{aiAnalysis.technical_explanation}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}

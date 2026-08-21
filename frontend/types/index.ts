export type UserRole = 'ADMIN' | 'ANALYST' | 'VIEWER';
export type SeverityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type FindingStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'ACCEPTED_RISK' | 'FALSE_POSITIVE';
export type ScanStatus = 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
export type ScanType = 'WEBSITE' | 'SECRETS' | 'DEPENDENCIES';
export type AssetType = 'WEBSITE' | 'SOURCE_CODE' | 'DEPENDENCY_MANIFEST';
export type ProjectStatus = 'ACTIVE' | 'ARCHIVED' | 'COMPLETED';
export type ReportType = 'EXECUTIVE' | 'TECHNICAL' | 'FULL';

export interface User { id: string; name: string; email: string; role: UserRole; is_active: boolean; created_at: string; }
export interface ProjectStats { security_score: number; assets_count: number; scans_count: number; critical_findings: number; high_findings: number; medium_findings: number; low_findings: number; }
export interface Project { id: string; name: string; description?: string; owner_id: string; status: ProjectStatus; created_at: string; updated_at: string; stats?: ProjectStats | null; }
export interface Asset { id: string; project_id: string; name: string; type: AssetType; target: string; description?: string; authorization_confirmed: boolean; status: string; created_at: string; }
export interface Scan { id: string; project_id: string; asset_id: string; scan_type: ScanType; status: ScanStatus; progress: number; started_at?: string; completed_at?: string; error_message?: string; created_at: string; }
export interface Finding { id: string; scan_id: string; asset_id: string; title: string; description: string; category: string; severity: SeverityLevel; confidence: number; evidence: Record<string, unknown>; remediation: string; cwe?: string; cve?: string; status: FindingStatus; risk_score: number; first_seen_at: string; last_seen_at: string; created_at: string; }
export interface AIAnalysis { id: string; finding_id: string; summary: string; technical_explanation: string; business_impact: string; remediation: string; priority: string; model: string; created_at: string; }
export interface Report { id: string; project_id: string; scan_id?: string | null; report_type: ReportType; file_path?: string | null; generated_by: string; created_at: string; content?: string | null; }
export interface AuditLog { id: string; user_id: string; action: string; resource_type: string; resource_id: string; metadata: any; ip_address: string; created_at: string; }

export interface ApiError { error: { code: string; message: string } }
export interface PaginatedResponse<T> { items: T[]; total: number; page: number; page_size: number; pages: number; }
export interface AuthTokens { access_token: string; refresh_token: string; token_type: string; }
export interface LoginRequest { email: string; password: string; }
export interface RegisterRequest { name: string; email: string; password: string; }
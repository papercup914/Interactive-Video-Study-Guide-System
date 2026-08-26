/**
 * Admin Health Dashboard Data Models
 * Specified for Milestone M1 (Infrastructure & Data Layer)
 */

/**
 * Log Severity Level
 */
export type LogLevel = 'info' | 'warning' | 'error' | 'critical';

/**
 * Error Category / Type
 */
export type ErrorCategory =
  | 'API Error'
  | 'Network Error'
  | 'Auth Error'
  | 'Render Warning'
  | 'LLM Generation Error'
  | 'Audio Processing Error'
  | 'PDF Parse Warning';

/**
 * Log Originating Source Module
 */
export type LogSource =
  | 'Frontend / React Render'
  | 'Frontend / API Client'
  | 'Backend / FastAPI Router'
  | 'Backend / LLM Service'
  | 'Backend / Audio Transcriber'
  | 'Backend / PDF Parser'
  | 'System / Health Monitor';

/**
 * Individual System Log Entry
 */
export interface SystemLogEntry {
  id: string;
  timestamp: string; // ISO 8601 format string
  level: LogLevel;
  category: ErrorCategory;
  message: string;
  source: LogSource;
  details?: string | null;
  jobId?: string | null;
  statusCode?: number | null;
  resolved?: boolean;
}

/**
 * Aggregated Time-Series Data Point for Frequency Area/Line Charts
 */
export interface TimeSeriesPoint {
  timestamp: string;
  formattedTime: string;
  errorCount: number;
  warningCount: number;
  infoCount: number;
  totalCount: number;
}

/**
 * Category Breakdown for Donut/Pie Charts
 */
export interface CategoryBreakdown {
  category: ErrorCategory;
  count: number;
  percentage: number;
  color: string;
}

/**
 * Overall System Health Summary Metrics
 */
export interface SystemHealthSummary {
  systemStatus: 'Healthy' | 'Degraded' | 'Critical';
  totalLogs: number;
  errorRate: number; // percentage (e.g. 3.45)
  totalErrors: number;
  totalWarnings: number;
  avgLatencyMs: number;
  activeJobs: number;
  lastUpdated: string;
}

/**
 * Complete Admin Health Dashboard Data Payload Structure
 */
export interface AdminHealthData {
  summary: SystemHealthSummary;
  timeSeries: TimeSeriesPoint[];
  categoryBreakdown: CategoryBreakdown[];
  logs: SystemLogEntry[];
}

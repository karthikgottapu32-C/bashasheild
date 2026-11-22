import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  ShieldAlert,
  Flame,
  Languages,
  History,
  Award,
  RefreshCw,
  TrendingUp,
  AlertOctagon,
  AlertTriangle,
  Cpu,
  UserX,
  Trash2,
  Filter,
  CheckCircle2,
  Clock,
  Download,
  Search
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { getStats, getScans, clearScans, deleteScan } from '../services/api';
import { DashboardStats, ScanRecord } from '../types';
import { useTheme } from '../theme/useTheme';
import { ToastContainer, ToastMessage } from '../components/Toast';

interface DashboardViewProps {
  onNavigateToTextGuard: () => void;
  onNavigateToEvaluation: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onNavigateToTextGuard,
  onNavigateToEvaluation
}) => {
  const { palette } = useTheme();
  const [activeTab, setActiveTab] = useState<'overview' | 'threats' | 'languages' | 'history'>('overview');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [scans, setScans] = useState<ScanRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);
  const [filterRisk, setFilterRisk] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (toast: Omit<ToastMessage, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { ...toast, id }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, scansData] = await Promise.all([
        getStats(),
        getScans(50, 0)
      ]);
      setStats(statsData);
      setScans(scansData);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard operational data");
      addToast({
        type: 'error',
        title: 'Connection Error',
        message: err.message || 'Failed to load telemetry data from backend.',
        action: { label: 'Retry', onClick: loadData }
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const handleAuthChange = () => {
      loadData();
    };
    window.addEventListener('bhashashield:auth-change', handleAuthChange);
    return () => window.removeEventListener('bhashashield:auth-change', handleAuthChange);
  }, []);

  const handleClearHistory = async () => {
    if (!window.confirm("Are you sure you want to clear scan logs? This action is permanent.")) return;
    try {
      setClearing(true);
      await clearScans();
      await loadData();
      addToast({
        type: 'success',
        title: 'History Cleared',
        message: 'Telemetry audit records cleared successfully.'
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Clear Operation Failed',
        message: err.message || 'Failed to clear scans.'
      });
    } finally {
      setClearing(false);
    }
  };

  const handleDeleteRow = async (scanId: string) => {
    if (!window.confirm(`Delete scan ${scanId}?`)) return;
    try {
      await deleteScan(scanId);
      setScans(prev => prev.filter(s => s.id !== scanId));
      addToast({
        type: 'success',
        title: 'Scan Deleted',
        message: `Record ${scanId} removed from audit history.`
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Deletion Failed',
        message: err.message || `Failed to delete scan ${scanId}.`
      });
    }
  };

  const handleExportCsv = () => {
    if (filteredScans.length === 0) {
      addToast({
        type: 'warning',
        title: 'Export Unavailable',
        message: 'No scan records match current filter criteria.'
      });
      return;
    }
    try {
      const headers = ["Scan ID", "Timestamp", "Channel", "Language", "Script", "Risk Level", "Risk Score", "Primary Threat", "Text Preview"];
      const rows = filteredScans.map(s => [
        `"${s.id}"`,
        `"${s.timestamp}"`,
        `"${s.channel}"`,
        `"${s.language}"`,
        `"${s.script}"`,
        `"${s.risk_level}"`,
        s.risk_score,
        `"${s.primary_threat || 'BENIGN'}"`,
        `"${s.text_preview.replace(/"/g, '""')}"`
      ]);
      const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", `bhashashield_scans_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      addToast({
        type: 'success',
        title: 'CSV Export Succeeded',
        message: `Exported ${filteredScans.length} scan records to CSV.`
      });
    } catch (err: any) {
      addToast({
        type: 'error',
        title: 'Export Failed',
        message: err.message || 'Failed to generate CSV export.'
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-28 flex flex-col items-center justify-center text-center">
        <RefreshCw className="w-8 h-8 animate-spin text-cyan mb-3" />
        <p className="text-sm font-mono text-txt-secondary">Connecting to Security Intelligence Console...</p>
      </div>
    );
  }

  // Language Chart data
  const langChartData = stats ? Object.entries(stats.language_distribution).map(([name, count]) => ({
    name,
    count
  })) : [];

  // Risk Chart data
  const riskChartData = stats ? Object.entries(stats.risk_distribution).map(([name, count]) => ({
    name,
    count
  })) : [];

  // Threat Category Chart data
  const threatChartData = stats ? Object.entries(stats.threat_distribution).map(([name, count]) => ({
    name: name.replace('_', ' '),
    count
  })) : [];

  const RISK_COLORS: Record<string, string> = {
    LOW: '#00D68F',
    MEDIUM: '#397BFF',
    HIGH: '#FFB547',
    CRITICAL: '#FF4566'
  };

  const filteredScans = scans.filter(s => {
    const matchesRisk = filterRisk === "ALL" || s.risk_level === filterRisk;
    const q = searchQuery.trim().toLowerCase();
    const matchesQuery = !q ||
      s.id.toLowerCase().includes(q) ||
      s.text_preview.toLowerCase().includes(q) ||
      s.channel.toLowerCase().includes(q) ||
      s.language.toLowerCase().includes(q);
    return matchesRisk && matchesQuery;
  });

  return (
    <div className="min-h-screen pt-20 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      {/* Console Title Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-status-emerald animate-pulse" />
            <span className="text-xs text-txt-muted uppercase font-mono tracking-wider">
              BhashaShield SOC Console • Live Stream
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-bg-card border border-white/10 text-txt-secondary">
              SYNTHETIC & REAL SCANS
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-3">
            <LayoutDashboard className="w-7 h-7 text-cyan" />
            Security Intelligence Console
          </h1>
        </div>

        {/* Console Navigation Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-black/40 rounded-xl border border-white/10 overflow-x-auto text-xs">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3.5 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'overview' ? 'bg-[var(--theme-accent)] text-black font-bold shadow-[0_0_15px_rgba(var(--theme-accent-rgb),0.3)]' : 'text-white/60 hover:text-white'
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('threats')}
            className={`px-3.5 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'threats' ? 'bg-[var(--theme-accent)] text-black font-bold shadow-[0_0_15px_rgba(var(--theme-accent-rgb),0.3)]' : 'text-white/60 hover:text-white'
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            Threats
          </button>
          <button
            onClick={() => setActiveTab('languages')}
            className={`px-3.5 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'languages' ? 'bg-[var(--theme-accent)] text-black font-bold shadow-[0_0_15px_rgba(var(--theme-accent-rgb),0.3)]' : 'text-white/60 hover:text-white'
            }`}
          >
            <Languages className="w-3.5 h-3.5" />
            Languages
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-3.5 py-1.5 rounded-lg font-semibold transition-all flex items-center gap-1.5 whitespace-nowrap ${
              activeTab === 'history' ? 'bg-[var(--theme-accent)] text-black font-bold shadow-[0_0_15px_rgba(var(--theme-accent-rgb),0.3)]' : 'text-white/60 hover:text-white'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            Scan History
          </button>
        </div>
      </div>

      {/* Error Alert Banner */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-status-coral/10 border border-status-coral/30 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-status-coral shrink-0" />
            <p className="text-sm text-status-coral font-medium">{error}</p>
          </div>
          <button
            onClick={loadData}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg border border-status-coral/40 text-xs font-bold text-white hover:bg-status-coral/20 transition-all flex items-center gap-1.5 shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Retry Connection
          </button>
        </div>
      )}

      {/* KPI Cards Row */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div className="glass-panel p-4 rounded-xl border border-white/10">
            <div className="text-[11px] font-mono uppercase tracking-wider text-txt-secondary mb-1">
              Total Scans
            </div>
            <div className="text-2xl font-extrabold font-mono text-white">
              {stats.total_scans}
            </div>
            <div className="text-[10px] text-txt-muted mt-1">Live recorded inputs</div>
          </div>

          <div className="glass-panel p-4 rounded-xl border border-status-coral/30">
            <div className="text-[11px] font-mono uppercase tracking-wider text-status-coral mb-1 flex items-center gap-1">
              <AlertOctagon className="w-3.5 h-3.5" />
              Threats Flagged
            </div>
            <div className="text-2xl font-extrabold font-mono text-status-coral">
              {stats.threat_count}
            </div>
            <div className="text-[10px] text-txt-muted mt-1">Medium to Critical risk</div>
          </div>

          <div className="glass-panel p-4 rounded-xl border border-cyan/30">
            <div className="text-[11px] font-mono uppercase tracking-wider text-cyan mb-1 flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5" />
              Prompt Injections
            </div>
            <div className="text-2xl font-extrabold font-mono text-cyan">
              {stats.prompt_injection_count}
            </div>
            <div className="text-[10px] text-txt-muted mt-1">AI instruction hijacking</div>
          </div>

          <div className="glass-panel p-4 rounded-xl border border-status-amber/30">
            <div className="text-[11px] font-mono uppercase tracking-wider text-status-amber mb-1 flex items-center gap-1">
              <UserX className="w-3.5 h-3.5" />
              High Risk / Fraud
            </div>
            <div className="text-2xl font-extrabold font-mono text-status-amber">
              {stats.high_risk_count}
            </div>
            <div className="text-[10px] text-txt-muted mt-1">High & Critical findings</div>
          </div>

          <div className="glass-panel p-4 rounded-xl border border-status-emerald/30 col-span-2 lg:col-span-1">
            <div className="text-[11px] font-mono uppercase tracking-wider text-status-emerald mb-1 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Benign / Safe
            </div>
            <div className="text-2xl font-extrabold font-mono text-status-emerald">
              {stats.clean_count}
            </div>
            <div className="text-[10px] text-txt-muted mt-1">Safe inputs verified</div>
          </div>
        </div>
      )}

      {/* Tab: Overview */}
      {activeTab === 'overview' && stats && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Language Breakdown Chart */}
            <div className="lg:col-span-7 glass-panel p-6 rounded-2xl border border-white/10">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white mb-1">
                Linguistic Distribution
              </h3>
              <p className="text-xs text-txt-secondary mb-4">
                Input volume across Indian languages, scripts, and romanized forms
              </p>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={langChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                    <XAxis dataKey="name" stroke="#5A6E8A" fontSize={11} interval={0} angle={-15} textAnchor="end" />
                    <YAxis stroke="#5A6E8A" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: palette.primary.hex,
                        borderColor: palette.accent.hex,
                        borderRadius: '8px',
                        fontSize: '12px',
                        color: '#F5F7FA'
                      }}
                    />
                    <Bar dataKey="count" fill={palette.accent.hex} radius={[4, 4, 0, 0]}>
                      {langChartData.map((_, i) => (
                        <Cell key={`cell-${i}`} fill={i % 2 === 0 ? palette.accent.hex : palette.secondary.hex} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Risk Distribution Donut */}
            <div className="lg:col-span-5 glass-panel p-6 rounded-2xl border border-white/10 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-white mb-1">
                  Risk Level Proportions
                </h3>
                <p className="text-xs text-txt-secondary mb-4">
                  Aggregated threat severity across all recorded scans
                </p>
                <div className="h-52 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={riskChartData}
                        dataKey="count"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={4}
                      >
                        {riskChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={RISK_COLORS[entry.name] || '#00E5FF'} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0F182A',
                          borderColor: 'rgba(0, 229, 255, 0.3)',
                          borderRadius: '8px',
                          fontSize: '12px',
                          color: '#F5F7FA'
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/10 text-xs">
                {riskChartData.map((r) => (
                  <div key={r.name} className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full"
                      style={{ backgroundColor: RISK_COLORS[r.name] || '#00E5FF' }}
                    />
                    <span className="text-txt-secondary font-mono">{r.name}:</span>
                    <span className="font-bold text-white">{r.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Live Scans Table */}
          <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                  Recent Scan Stream
                </h3>
                <p className="text-xs text-txt-secondary mt-0.5">
                  Latest evaluated payloads with risk scores and channel tags
                </p>
              </div>
              <button
                onClick={onNavigateToTextGuard}
                className="text-xs font-semibold text-cyan hover:underline"
              >
                Launch Text Guard →
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-bg-midnight/70 text-txt-muted uppercase font-mono tracking-wider">
                  <tr>
                    <th className="py-2.5 px-3">Scan ID</th>
                    <th className="py-2.5 px-3">Input Text</th>
                    <th className="py-2.5 px-3">Channel</th>
                    <th className="py-2.5 px-3">Language</th>
                    <th className="py-2.5 px-3">Risk Level</th>
                    <th className="py-2.5 px-3">Score</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono">
                  {stats.recent_scans.map((s) => (
                    <tr key={s.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 px-3 text-cyan">{s.id.substring(0, 12)}</td>
                      <td className="py-3 px-3 font-sans max-w-xs truncate text-txt-primary">
                        {s.text_preview}
                      </td>
                      <td className="py-3 px-3 text-txt-secondary">{s.channel}</td>
                      <td className="py-3 px-3 text-txt-secondary">{s.language}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            s.risk_level === 'CRITICAL' ? 'bg-status-coral/20 text-status-coral' :
                            s.risk_level === 'HIGH' ? 'bg-status-amber/20 text-status-amber' :
                            s.risk_level === 'MEDIUM' ? 'bg-neon-blue/20 text-neon-blue' :
                            'bg-status-emerald/20 text-status-emerald'
                          }`}
                        >
                          {s.risk_level}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-white font-bold">{Math.round(s.risk_score)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Threat Intelligence */}
      {activeTab === 'threats' && stats && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                Threat Classification Breakdown
              </h3>
              <p className="text-xs text-txt-secondary">
                Frequency of specific attack categories detected in processed inputs
              </p>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={threatChartData} layout="vertical" margin={{ top: 10, right: 10, left: 30, bottom: 10 }}>
                    <XAxis type="number" stroke="#5A6E8A" fontSize={11} />
                    <YAxis dataKey="name" type="category" stroke="#5A6E8A" fontSize={11} width={130} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0F182A',
                        borderColor: 'rgba(0, 229, 255, 0.3)',
                        borderRadius: '8px',
                        fontSize: '12px',
                        color: '#F5F7FA'
                      }}
                    />
                    <Bar dataKey="count" fill="#FF4566" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                Target Entity Distinction
              </h3>
              <p className="text-xs text-txt-secondary">
                Classification between machine attacks and human social engineering
              </p>
              <div className="space-y-3 pt-4">
                <div className="p-4 rounded-xl bg-cyan/10 border border-cyan/30 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Cpu className="w-6 h-6 text-cyan" />
                    <div>
                      <div className="text-sm font-bold text-white">AI Assistant Target</div>
                      <div className="text-xs text-txt-secondary">Prompt injection, jailbreaks, data exfiltration</div>
                    </div>
                  </div>
                  <div className="text-2xl font-mono font-extrabold text-cyan">
                    {stats.target_distribution["AI_SYSTEM"] || 0}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-status-amber/10 border border-status-amber/30 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <UserX className="w-6 h-6 text-status-amber" />
                    <div>
                      <div className="text-sm font-bold text-white">Human User Target</div>
                      <div className="text-xs text-txt-secondary">UPI refund traps, phishing, credential theft</div>
                    </div>
                  </div>
                  <div className="text-2xl font-mono font-extrabold text-status-amber">
                    {stats.target_distribution["HUMAN_USER"] || 0}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Languages */}
      {activeTab === 'languages' && (
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-6">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-white">
              Multilingual Coverage & Script Verification
            </h3>
            <p className="text-xs text-txt-secondary mt-0.5">
              Active detection capabilities validated across scripts and romanized transliterations
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-bg-midnight/70 border border-cyan/30 space-y-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan/15 text-cyan">Active Defense Engine</span>
              <h4 className="text-sm font-bold text-white">Telugu (తెలుగు) & Romanized</h4>
              <p className="text-xs text-txt-secondary">
                Comprehensive native script detection and Romanized Telugu phonetics ("cheyyi", "marchipo", "bayataku cheppu").
              </p>
            </div>

            <div className="p-4 rounded-xl bg-bg-midnight/70 border border-cyan/30 space-y-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan/15 text-cyan">Active Defense Engine</span>
              <h4 className="text-sm font-bold text-white">Hindi (हिन्दी) & Romanized</h4>
              <p className="text-xs text-txt-secondary">
                Devanagari script injection detection and Romanized Hindi phonetics ("bhool jao", "nirdesh", "bina rules").
              </p>
            </div>

            <div className="p-4 rounded-xl bg-bg-midnight/70 border border-cyan/30 space-y-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-cyan/15 text-cyan">Active Defense Engine</span>
              <h4 className="text-sm font-bold text-white">English & Code-Mixed</h4>
              <p className="text-xs text-txt-secondary">
                Direct injection attacks, DAN persona overrides, and cross-lingual code-mixed payloads (e.g. English + Hindi).
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Scan History */}
      {activeTab === 'history' && (
        <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                Stored Scan History ({scans.length})
              </h3>
              <p className="text-xs text-txt-secondary mt-0.5">
                Privacy-controlled audit trail of evaluated inputs
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-txt-muted" />
                <input
                  type="text"
                  placeholder="Search scans..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-bg-dark border border-white/15 rounded-lg pl-8 pr-3 py-1.5 text-xs text-txt-primary focus:outline-none focus:border-cyan w-36 sm:w-48 placeholder:text-txt-muted"
                />
              </div>

              <select
                value={filterRisk}
                onChange={(e) => setFilterRisk(e.target.value)}
                className="bg-bg-dark border border-white/15 rounded-lg px-3 py-1.5 text-xs text-txt-primary focus:outline-none focus:border-cyan"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>

              <button
                onClick={handleExportCsv}
                disabled={filteredScans.length === 0}
                className="px-3 py-1.5 rounded-lg bg-cyan/15 hover:bg-cyan/25 text-cyan border border-cyan/30 text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-40"
                title="Export current filtered history as CSV"
              >
                <Download className="w-3.5 h-3.5" />
                Export CSV
              </button>

              <button
                onClick={handleClearHistory}
                disabled={clearing || scans.length === 0}
                className="px-3 py-1.5 rounded-lg bg-status-coral/15 hover:bg-status-coral/25 text-status-coral border border-status-coral/30 text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-40"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Clear History
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-bg-midnight/70 text-txt-muted uppercase font-mono tracking-wider">
                <tr>
                  <th className="py-2.5 px-3">Scan ID</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Text Sample</th>
                  <th className="py-2.5 px-3">Channel</th>
                  <th className="py-2.5 px-3">Risk Level</th>
                  <th className="py-2.5 px-3">Score</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono">
                {filteredScans.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-txt-muted font-sans">
                      No scan records matching your filter criteria.
                    </td>
                  </tr>
                ) : (
                  filteredScans.map((s) => (
                    <tr key={s.id} className="hover:bg-white/[0.02]">
                      <td className="py-3 px-3 text-cyan">{s.id}</td>
                      <td className="py-3 px-3 text-txt-muted">{s.timestamp.split('T')[0]}</td>
                      <td className="py-3 px-3 font-sans max-w-sm truncate text-txt-primary">
                        {s.text_preview}
                      </td>
                      <td className="py-3 px-3 text-txt-secondary">{s.channel}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            s.risk_level === 'CRITICAL' ? 'bg-status-coral/20 text-status-coral' :
                            s.risk_level === 'HIGH' ? 'bg-status-amber/20 text-status-amber' :
                            s.risk_level === 'MEDIUM' ? 'bg-neon-blue/20 text-neon-blue' :
                            'bg-status-emerald/20 text-status-emerald'
                          }`}
                        >
                          {s.risk_level}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-white font-bold">{Math.round(s.risk_score)}</td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => handleDeleteRow(s.id)}
                          className="p-1 rounded hover:bg-status-coral/20 text-txt-muted hover:text-status-coral transition-colors"
                          title={`Delete scan ${s.id}`}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Floating System Toasts */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
};

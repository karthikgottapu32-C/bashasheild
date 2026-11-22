import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import {
  Award,
  AlertTriangle,
  Play,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Cpu,
  Layers,
  Filter,
  Database,
  Search,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  ShieldAlert,
  Info
} from 'lucide-react';
import { getEvaluationReport, triggerEvaluation, getEvaluationDatasets } from '../services/api';
import { EvaluationMetrics, EvaluationDataset, FailedTestCase } from '../types';
import { useTheme } from '../theme/useTheme';

const FALLBACK_DATASETS: EvaluationDataset[] = [
  {
    id: "holdout_v2",
    name: "Frozen Independent Holdout Set 2 (100 Samples)",
    description: "Zero-leakage frozen validation set with 50 malicious and 50 benign samples across Telugu, Hindi, English, and Romanized scripts.",
    sample_count: 100
  },
  {
    id: "benchmark_v3",
    name: "BhashaShield Comprehensive Benchmark v3 (1,200 Samples)",
    description: "Full synthetic and real-world multi-vector evaluation benchmark across all 5 orthographic varieties and 5 channels.",
    sample_count: 1200
  },
  {
    id: "synthetic_test",
    name: "Synthetic Test Split (1,000 Samples)",
    description: "Heuristic and generator test split for regression testing.",
    sample_count: 1000
  }
];

export const EvaluationView: React.FC = () => {
  const { palette } = useTheme();
  const [selectedDataset, setSelectedDataset] = useState<string>("holdout_v2");
  const [availableDatasets, setAvailableDatasets] = useState<EvaluationDataset[]>(FALLBACK_DATASETS);
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningEval, setRunningEval] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<'language' | 'script' | 'channel'>('language');
  const [errorFilter, setErrorFilter] = useState<'ALL' | 'FALSE_POSITIVE' | 'FALSE_NEGATIVE' | 'UNCERTAIN_ABSTENTION'>('ALL');
  const [expandedCaseId, setExpandedCaseId] = useState<string | null>(null);

  // Fetch available datasets and current report
  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load dataset metadata
      try {
        const dsRes = await getEvaluationDatasets();
        if (dsRes && dsRes.datasets && dsRes.datasets.length > 0) {
          setAvailableDatasets(dsRes.datasets);
        }
      } catch {
        // Fallback to static list
      }

      // Load report for selected dataset
      const data = await getEvaluationReport(selectedDataset);
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || "Failed to load evaluation metrics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, [selectedDataset]);

  const handleDatasetChange = async (newDataset: string) => {
    setSelectedDataset(newDataset);
    try {
      setLoading(true);
      setError(null);
      const data = await getEvaluationReport(newDataset);
      setMetrics(data);
    } catch (err: any) {
      setError(err.message || `Failed to load metrics for ${newDataset}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunEvaluation = async () => {
    try {
      setRunningEval(true);
      setError(null);
      const result = await triggerEvaluation(selectedDataset);
      setMetrics(result.report);
    } catch (err: any) {
      setError(err.message || "Failed to run evaluation pipeline. (Note: Admin privileges required)");
    } finally {
      setRunningEval(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen pt-28 flex flex-col items-center justify-center text-center">
        <RefreshCw className="w-8 h-8 animate-spin text-[var(--theme-accent)] mb-3" />
        <p className="text-sm font-mono text-txt-secondary">
          Loading Benchmark Evaluation Data ({selectedDataset})...
        </p>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="min-h-screen pt-28 max-w-4xl mx-auto px-4 text-center">
        <div className="p-8 rounded-2xl bg-bg-card border border-status-coral/30">
          <AlertTriangle className="w-10 h-10 text-status-coral mx-auto mb-3" />
          <h2 className="text-xl font-bold text-white mb-2">Evaluation Benchmark Unavailable</h2>
          <p className="text-sm text-txt-secondary mb-6">{error || "No evaluation report available for this dataset."}</p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={() => handleDatasetChange("holdout_v2")}
              className="px-5 py-2.5 rounded-xl border border-white/20 text-white font-bold text-sm hover:bg-white/10 transition-all flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Load Holdout Set 2
            </button>
            <button
              onClick={handleRunEvaluation}
              disabled={runningEval}
              className="theme-button-primary px-6 py-2.5 rounded-xl font-bold text-sm hover:brightness-110 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {runningEval ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              Execute Evaluation Pipeline on {selectedDataset}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Format per-group chart data with safe fallbacks
  const filterSource = activeFilter === 'language'
    ? (metrics.per_language || {})
    : activeFilter === 'script'
    ? (metrics.per_script || {})
    : (metrics.per_channel || {});

  const chartData = Object.entries(filterSource).map(([name, data]) => ({
    name,
    f1: Math.round(((data as any).f1_score || 0) * 100),
    precision: Math.round(((data as any).precision || 0) * 100),
    recall: Math.round(((data as any).recall || 0) * 100),
    samples: (data as any).samples || 0
  }));

  const cm = metrics.confusion_matrix || { true_positives: 0, false_positives: 0, false_negatives: 0, true_negatives: 0 };
  const totalCm = (cm.true_positives + cm.false_positives + cm.false_negatives + cm.true_negatives) || 1;

  // Filter failed cases
  const failedCases = metrics.failed_cases || [];
  const filteredCases = failedCases.filter(c => {
    if (errorFilter === 'ALL') return true;
    return c.error_type === errorFilter;
  });

  return (
    <div className="min-h-screen pt-24 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-status-emerald/10 text-status-emerald border border-status-emerald/30">
              Verified Evaluation Benchmark
            </span>
            <span className="text-xs text-txt-muted font-mono">
              Model: {metrics.model_evaluated}
            </span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <Award className="w-9 h-9 text-[var(--theme-accent)]" />
            Evaluation & Model Performance
          </h1>
          <p className="text-txt-secondary text-sm mt-1">
            Empirical evaluation measured across unseen test partitions without dataset leakage.
          </p>
        </div>

        {/* Dataset Selector & Execution Button */}
        <div className="flex flex-wrap items-center gap-3 self-start md:self-auto">
          <div className="flex items-center gap-2 bg-bg-midnight/90 border border-white/10 rounded-xl px-3 py-2">
            <Database className="w-4 h-4 text-cyan" />
            <select
              value={selectedDataset}
              onChange={(e) => handleDatasetChange(e.target.value)}
              disabled={runningEval}
              className="bg-transparent text-xs text-white font-medium focus:outline-none cursor-pointer"
            >
              {availableDatasets.map((ds) => (
                <option key={ds.id} value={ds.id} className="bg-bg-dark text-white">
                  {ds.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleRunEvaluation}
            disabled={runningEval}
            className="theme-button-primary px-5 py-2.5 rounded-xl text-xs font-bold tracking-wider uppercase flex items-center gap-2 disabled:opacity-50"
          >
            {runningEval ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {runningEval ? "Evaluating Test Data..." : "Run Evaluation"}
          </button>
        </div>
      </div>

      {/* Mandatory Transparent Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-bg-card/90 border border-status-amber/40 flex items-start gap-3 shadow-lg">
        <AlertTriangle className="w-5 h-5 text-status-amber flex-shrink-0 mt-0.5" />
        <div className="text-xs text-txt-secondary leading-relaxed">
          <strong className="text-status-amber font-semibold block mb-0.5">EVALUATION METHODOLOGY DISCLAIMER:</strong>
          {metrics.disclaimer || "Results measured across verified holdout partitions with zero training overlap."} Current dataset: <strong className="text-white">{metrics.dataset_name || selectedDataset}</strong> ({metrics.total_samples} samples evaluated).
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-white/10">
          <div className="text-[11px] uppercase font-mono tracking-wider text-txt-secondary mb-1">
            Overall F1-Score
          </div>
          <div className="text-3xl font-extrabold font-mono text-[var(--theme-accent)]">
            {(metrics.f1_score * 100).toFixed(1)}%
          </div>
          <div className="mt-2 text-[11px] text-txt-muted">
            Precision: {(metrics.precision * 100).toFixed(1)}% • Recall: {(metrics.recall * 100).toFixed(1)}%
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-white/10">
          <div className="text-[11px] uppercase font-mono tracking-wider text-txt-secondary mb-1">
            Prompt Injection F1
          </div>
          <div className="text-3xl font-extrabold font-mono text-status-emerald">
            {(metrics.prompt_injection_f1 * 100).toFixed(1)}%
          </div>
          <div className="mt-2 text-[11px] text-txt-muted">
            Precision: {(metrics.prompt_injection_precision * 100).toFixed(1)}%
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-white/10">
          <div className="text-[11px] uppercase font-mono tracking-wider text-txt-secondary mb-1">
            Clean Pass Rate
          </div>
          <div className="text-3xl font-extrabold font-mono text-cyan">
            {((metrics.clean_pass_rate ?? (1.0 - metrics.false_positive_rate)) * 100).toFixed(1)}%
          </div>
          <div className="mt-2 text-[11px] text-txt-muted">
            Benign clean validation pass
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-white/10">
          <div className="text-[11px] uppercase font-mono tracking-wider text-txt-secondary mb-1">
            False Positive Rate
          </div>
          <div className="text-3xl font-extrabold font-mono text-status-amber">
            {(metrics.false_positive_rate * 100).toFixed(2)}%
          </div>
          <div className="mt-2 text-[11px] text-txt-muted">
            Zero or low false alarms
          </div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-white/10 col-span-2 md:col-span-1">
          <div className="text-[11px] uppercase font-mono tracking-wider text-txt-secondary mb-1">
            Test Partition Size
          </div>
          <div className="text-3xl font-extrabold font-mono text-white">
            {metrics.total_samples}
          </div>
          <div className="mt-2 text-[11px] text-txt-muted">
            Uncertain abstentions: {metrics.uncertain_samples ?? 0}
          </div>
        </div>
      </div>

      {/* Main Charts & Confusion Matrix Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Slice Performance Bar Chart */}
        <div className="lg:col-span-7 glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-white">
                Performance by Segment (F1 %)
              </h3>
              <p className="text-xs text-txt-secondary mt-0.5">
                Evaluation results grouped by orthographic and delivery dimensions
              </p>
            </div>

            {/* Filter buttons */}
            <div className="flex items-center gap-1.5 bg-bg-midnight/80 p-1 rounded-xl border border-white/10 text-xs">
              <button
                onClick={() => setActiveFilter('language')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  activeFilter === 'language'
                    ? 'bg-cyan text-bg-midnight font-bold shadow'
                    : 'text-txt-secondary hover:text-white'
                }`}
              >
                Language
              </button>
              <button
                onClick={() => setActiveFilter('script')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  activeFilter === 'script'
                    ? 'bg-cyan text-bg-midnight font-bold shadow'
                    : 'text-txt-secondary hover:text-white'
                }`}
              >
                Script
              </button>
              <button
                onClick={() => setActiveFilter('channel')}
                className={`px-3 py-1 rounded-lg transition-all ${
                  activeFilter === 'channel'
                    ? 'bg-cyan text-bg-midnight font-bold shadow'
                    : 'text-txt-secondary hover:text-white'
                }`}
              >
                Channel
              </button>
            </div>
          </div>

          <div className="h-64 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis
                  dataKey="name"
                  stroke="#5A6E8A"
                  fontSize={11}
                  interval={0}
                  angle={-15}
                  textAnchor="end"
                />
                <YAxis stroke="#5A6E8A" fontSize={11} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F182A',
                    borderColor: palette.accent.hex,
                    borderRadius: '8px',
                    fontSize: '12px',
                    color: '#F5F7FA'
                  }}
                />
                <Bar dataKey="f1" fill={palette.accent.hex} radius={[4, 4, 0, 0]}>
                  {chartData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={index % 2 === 0 ? palette.accent.hex : (palette.supporting?.blue || palette.secondary.hex)}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Confusion Matrix Interactive Visualizer */}
        <div className="lg:col-span-5 glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-white">
              Confusion Matrix ({selectedDataset})
            </h3>
            <p className="text-xs text-txt-secondary mt-0.5">
              Prediction distribution across malicious vs benign classifications
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-2">
            {/* True Positives */}
            <div className="p-4 rounded-xl bg-status-emerald/15 border border-status-emerald/30 text-center">
              <div className="text-[10px] uppercase font-mono tracking-wider text-status-emerald font-bold">
                True Positives (TP)
              </div>
              <div className="text-2xl font-extrabold font-mono text-white mt-1">
                {cm.true_positives}
              </div>
              <div className="text-[10px] text-txt-muted mt-1">
                {((cm.true_positives / totalCm) * 100).toFixed(1)}% of test set
              </div>
            </div>

            {/* False Positives */}
            <div className="p-4 rounded-xl bg-status-coral/15 border border-status-coral/30 text-center">
              <div className="text-[10px] uppercase font-mono tracking-wider text-status-coral font-bold">
                False Positives (FP)
              </div>
              <div className="text-2xl font-extrabold font-mono text-white mt-1">
                {cm.false_positives}
              </div>
              <div className="text-[10px] text-txt-muted mt-1">
                {((cm.false_positives / totalCm) * 100).toFixed(1)}% of test set
              </div>
            </div>

            {/* False Negatives */}
            <div className="p-4 rounded-xl bg-status-amber/15 border border-status-amber/30 text-center">
              <div className="text-[10px] uppercase font-mono tracking-wider text-status-amber font-bold">
                False Negatives (FN)
              </div>
              <div className="text-2xl font-extrabold font-mono text-white mt-1">
                {cm.false_negatives}
              </div>
              <div className="text-[10px] text-txt-muted mt-1">
                {((cm.false_negatives / totalCm) * 100).toFixed(1)}% of test set
              </div>
            </div>

            {/* True Negatives */}
            <div className="p-4 rounded-xl bg-neon-blue/15 border border-neon-blue/30 text-center">
              <div className="text-[10px] uppercase font-mono tracking-wider text-neon-blue font-bold">
                True Negatives (TN)
              </div>
              <div className="text-2xl font-extrabold font-mono text-white mt-1">
                {cm.true_negatives}
              </div>
              <div className="text-[10px] text-txt-muted mt-1">
                {((cm.true_negatives / totalCm) * 100).toFixed(1)}% of test set
              </div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-bg-midnight/70 border border-white/5 text-xs text-txt-secondary leading-relaxed">
            Evaluated on <span className="font-mono text-cyan">{metrics.evaluated_at.split('T')[0]}</span> using strict zero-leakage template family partitioning.
          </div>
        </div>
      </div>

      {/* Error Analysis & Discrepancies Section */}
      <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-white/10">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Search className="w-4 h-4 text-cyan" />
              Error Analysis & Inspection ({filteredCases.length} Discrepancy Samples)
            </h3>
            <p className="text-xs text-txt-secondary mt-0.5">
              Inspect misclassifications or safety abstentions to diagnose boundary cases.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            <button
              onClick={() => setErrorFilter('ALL')}
              className={`px-3 py-1 rounded-lg border transition-all ${
                errorFilter === 'ALL'
                  ? 'bg-white/15 text-white border-white/30 font-bold'
                  : 'bg-black/30 text-txt-secondary border-white/5 hover:border-white/20'
              }`}
            >
              All Errors ({failedCases.length})
            </button>
            <button
              onClick={() => setErrorFilter('FALSE_POSITIVE')}
              className={`px-3 py-1 rounded-lg border transition-all ${
                errorFilter === 'FALSE_POSITIVE'
                  ? 'bg-status-coral/20 text-status-coral border-status-coral/40 font-bold'
                  : 'bg-black/30 text-txt-secondary border-white/5 hover:border-white/20'
              }`}
            >
              False Positives ({failedCases.filter(c => c.error_type === 'FALSE_POSITIVE').length})
            </button>
            <button
              onClick={() => setErrorFilter('UNCERTAIN_ABSTENTION')}
              className={`px-3 py-1 rounded-lg border transition-all ${
                errorFilter === 'UNCERTAIN_ABSTENTION'
                  ? 'bg-purple-500/20 text-purple-300 border-purple-500/40 font-bold'
                  : 'bg-black/30 text-txt-secondary border-white/5 hover:border-white/20'
              }`}
            >
              Uncertain Abstentions ({failedCases.filter(c => c.error_type === 'UNCERTAIN_ABSTENTION').length})
            </button>
          </div>
        </div>

        {filteredCases.length === 0 ? (
          <div className="p-8 text-center text-xs text-txt-muted">
            <CheckCircle2 className="w-8 h-8 text-status-emerald mx-auto mb-2 opacity-80" />
            No error samples matching filter in this evaluation run.
          </div>
        ) : (
          <div className="space-y-2.5">
            {filteredCases.map((c) => {
              const isExpanded = expandedCaseId === c.id;
              return (
                <div
                  key={c.id}
                  className="p-3.5 rounded-xl bg-black/40 border border-white/5 hover:border-white/15 transition-all text-xs"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-txt-muted text-[11px]">{c.id}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white/5 text-txt-secondary uppercase">
                        {c.language}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        c.error_type === 'FALSE_POSITIVE'
                          ? 'bg-status-coral/20 text-status-coral'
                          : 'bg-purple-500/20 text-purple-300'
                      }`}>
                        {c.error_type.replace('_', ' ')}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] font-mono">
                      <span>Ground Truth: <strong className="text-white">{c.ground_truth}</strong></span>
                      <span>•</span>
                      <span>Predicted: <strong className={c.predicted === 'MALICIOUS' ? 'text-status-coral' : 'text-purple-300'}>{c.predicted}</strong></span>
                      <span>(Score: {Math.round(c.risk_score)})</span>
                    </div>
                  </div>

                  <p className="font-mono text-white/90 bg-bg-midnight/70 p-2.5 rounded-lg border border-white/5">
                    {c.text_preview}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

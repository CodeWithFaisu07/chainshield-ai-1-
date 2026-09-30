import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { importDataset } from '../api'
import {
  Activity,
  ArrowLeftRight,
  ArrowUpRight,
  BarChart3,
  CalendarDays,
  ChevronDown,
  Database,
  FileText,
  Network,
  ShieldAlert,
  ShieldCheck,
  Target,
  TrendingUp,
  Upload,
  Wallet,
} from 'lucide-react'

const riskTrend = [
  { day: 'Sep 23', high: 18, medium: 42, low: 74 },
  { day: 'Sep 24', high: 24, medium: 48, low: 82 },
  { day: 'Sep 25', high: 21, medium: 54, low: 91 },
  { day: 'Sep 26', high: 31, medium: 61, low: 88 },
  { day: 'Sep 27', high: 28, medium: 57, low: 96 },
  { day: 'Sep 28', high: 36, medium: 68, low: 103 },
  { day: 'Sep 29', high: 32, medium: 64, low: 98 },
]

const leads = [
  {
    rank: 1,
    entity: '89d88149...b48b4c',
    type: 'Transaction',
    score: 82,
    reason: 'Connected transaction cluster',
  },
  {
    rank: 2,
    entity: 'bc1p73wh...czntzju',
    type: 'Wallet',
    score: 76,
    reason: 'Multiple related transactions',
  },
  {
    rank: 3,
    entity: '7.175.77.125',
    type: 'IP Address',
    score: 71,
    reason: 'Repeated network observations',
  },
  {
    rank: 4,
    entity: '23042598...9c7e31',
    type: 'Transaction',
    score: 68,
    reason: 'Unusual activity pattern',
  },
  {
    rank: 5,
    entity: 'bc1q8k4m...72fd',
    type: 'Wallet',
    score: 64,
    reason: 'Cluster association',
  },
]

const recentInvestigations = [
  {
    id: 'INV-0241',
    name: 'Transaction cluster review',
    date: '29 Sep 2026',
    score: 82,
    status: 'Completed',
  },
  {
    id: 'INV-0240',
    name: 'Wallet relationship analysis',
    date: '28 Sep 2026',
    score: 76,
    status: 'Completed',
  },
  {
    id: 'INV-0239',
    name: 'Network observation review',
    date: '27 Sep 2026',
    score: 61,
    status: 'Completed',
  },
  {
    id: 'INV-0238',
    name: 'Transaction anomaly analysis',
    date: '26 Sep 2026',
    score: 44,
    status: 'Completed',
  },
]

function RiskBadge({ score }) {
  const level =
    score >= 70 ? 'High' : score >= 40 ? 'Medium' : 'Low'

  const styles =
    level === 'High'
      ? 'bg-red-50 text-red-700 border-red-200'
      : level === 'Medium'
        ? 'bg-amber-50 text-amber-700 border-amber-200'
        : 'bg-emerald-50 text-emerald-700 border-emerald-200'

  const dot =
    level === 'High'
      ? 'bg-red-500'
      : level === 'Medium'
        ? 'bg-amber-500'
        : 'bg-emerald-500'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold ${styles}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {level}
    </span>
  )
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
  iconClass,
  trend,
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">
            {label}
          </p>

          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            {value}
          </p>
        </div>

        <div
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${iconClass}`}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2">
        {trend && (
          <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600">
            <TrendingUp className="h-3.5 w-3.5" />
            {trend}
          </span>
        )}

        <span className="text-xs text-slate-400">
          {detail}
        </span>
      </div>
    </div>
  )
}

function RiskTrendChart() {
  const width = 760
  const height = 280

  const padding = {
    top: 24,
    right: 20,
    bottom: 42,
    left: 42,
  }

  const maxValue = 120

  const getX = (index) =>
    padding.left +
    (index * (width - padding.left - padding.right)) /
      (riskTrend.length - 1)

  const getY = (value) =>
    height -
    padding.bottom -
    (value / maxValue) *
      (height - padding.top - padding.bottom)

  const createPath = (key) =>
    riskTrend
      .map((item, index) => {
        const command = index === 0 ? 'M' : 'L'

        return `${command} ${getX(index)} ${getY(item[key])}`
      })
      .join(' ')

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-4 border-b border-slate-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <BarChart3 className="h-4 w-4" />
            </div>

            <h2 className="text-base font-semibold text-slate-950">
              Risk Trend
            </h2>
          </div>

          <p className="mt-1 text-sm text-slate-500">
            Investigation leads identified across recent activity
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
            High
          </span>

          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
            Medium
          </span>

          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
            Low
          </span>
        </div>
      </div>

      <div className="overflow-x-auto px-5 pb-4 pt-5">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-[280px] min-w-[620px] w-full"
          role="img"
          aria-label="Risk trend chart"
        >
          {[0, 30, 60, 90, 120].map((value) => (
            <g key={value}>
              <line
                x1={padding.left}
                y1={getY(value)}
                x2={width - padding.right}
                y2={getY(value)}
                stroke="#e2e8f0"
                strokeWidth="1"
              />

              <text
                x={padding.left - 10}
                y={getY(value) + 4}
                textAnchor="end"
                fontSize="11"
                fill="#94a3b8"
              >
                {value}
              </text>
            </g>
          ))}

          <path
            d={createPath('high')}
            fill="none"
            stroke="#ef4444"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          <path
            d={createPath('medium')}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          <path
            d={createPath('low')}
            fill="none"
            stroke="#10b981"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {riskTrend.map((item, index) => (
            <g key={item.day}>
              <circle
                cx={getX(index)}
                cy={getY(item.high)}
                r="4"
                fill="#ef4444"
              />

              <circle
                cx={getX(index)}
                cy={getY(item.medium)}
                r="4"
                fill="#f59e0b"
              />

              <circle
                cx={getX(index)}
                cy={getY(item.low)}
                r="4"
                fill="#10b981"
              />

              <text
                x={getX(index)}
                y={height - 15}
                textAnchor="middle"
                fontSize="10"
                fill="#64748b"
              >
                {item.day}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </div>
  )
}

function RiskDistribution() {
  const values = {
    high: 126,
    medium: 384,
    low: 982,
  }

  const total = values.high + values.medium + values.low

  const highPercent = Math.round((values.high / total) * 100)
  const mediumPercent = Math.round((values.medium / total) * 100)
  const lowPercent = 100 - highPercent - mediumPercent

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-6 py-5">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 text-red-600">
            <ShieldAlert className="h-4 w-4" />
          </div>

          <h2 className="text-base font-semibold text-slate-950">
            Risk Distribution
          </h2>
        </div>

        <p className="mt-1 text-sm text-slate-500">
          Investigation leads grouped by risk level
        </p>
      </div>

      <div className="flex flex-col items-center gap-7 p-6 sm:flex-row">
        <div className="relative h-40 w-40 shrink-0">
          <svg
            viewBox="0 0 120 120"
            className="h-full w-full -rotate-90"
          >
            <circle
              cx="60"
              cy="60"
              r="42"
              fill="none"
              stroke="#e2e8f0"
              strokeWidth="14"
            />

            <circle
              cx="60"
              cy="60"
              r="42"
              fill="none"
              stroke="#10b981"
              strokeWidth="14"
              strokeDasharray={`${lowPercent * 2.638} 263.8`}
            />

            <circle
              cx="60"
              cy="60"
              r="42"
              fill="none"
              stroke="#f59e0b"
              strokeWidth="14"
              strokeDasharray={`${mediumPercent * 2.638} 263.8`}
              strokeDashoffset={`${-lowPercent * 2.638}`}
            />

            <circle
              cx="60"
              cy="60"
              r="42"
              fill="none"
              stroke="#ef4444"
              strokeWidth="14"
              strokeDasharray={`${highPercent * 2.638} 263.8`}
              strokeDashoffset={`${-(lowPercent + mediumPercent) * 2.638}`}
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-bold text-slate-950">
              {total.toLocaleString()}
            </span>

            <span className="mt-0.5 text-xs text-slate-500">
              Total leads
            </span>
          </div>
        </div>

        <div className="w-full space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 rounded-full bg-red-500" />

              <div>
                <p className="text-sm font-medium text-slate-700">
                  High Risk
                </p>

                <p className="text-xs text-slate-400">
                  {highPercent}% of leads
                </p>
              </div>
            </div>

            <span className="text-sm font-bold text-slate-950">
              {values.high}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 rounded-full bg-amber-500" />

              <div>
                <p className="text-sm font-medium text-slate-700">
                  Medium Risk
                </p>

                <p className="text-xs text-slate-400">
                  {mediumPercent}% of leads
                </p>
              </div>
            </div>

            <span className="text-sm font-bold text-slate-950">
              {values.medium}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="h-3 w-3 rounded-full bg-emerald-500" />

              <div>
                <p className="text-sm font-medium text-slate-700">
                  Low Risk
                </p>

                <p className="text-xs text-slate-400">
                  {lowPercent}% of leads
                </p>
              </div>
            </div>

            <span className="text-sm font-bold text-slate-950">
              {values.low}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

function LeadTypeIcon({ type }) {
  if (type === 'Wallet') {
    return <Wallet className="h-4 w-4" />
  }

  if (type === 'IP Address') {
    return <Network className="h-4 w-4" />
  }

  return <ArrowLeftRight className="h-4 w-4" />
}

function QuickAction({
  to,
  icon: Icon,
  title,
  description,
  primary = false,
}) {
  return (
    <Link
      to={to}
      className="group flex items-center gap-4 p-5 transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
    >
      <div
        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition ${
          primary
            ? 'bg-blue-600 text-white group-hover:bg-blue-700'
            : 'bg-slate-100 text-slate-600 group-hover:bg-slate-200'
        }`}
      >
        <Icon className="h-5 w-5" />
      </div>

      <div className="min-w-0">
        <p className="text-sm font-semibold text-slate-900">
          {title}
        </p>

        <p className="mt-1 text-xs leading-5 text-slate-500">
          {description}
        </p>
      </div>

      <ArrowUpRight className="ml-auto h-4 w-4 shrink-0 text-slate-300 transition group-hover:text-blue-600" />
    </Link>
  )
}

export default function Dashboard() {
  const [analysis, setAnalysis] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)

  const handleAnalyzeDataset = async () => {
    if (!selectedFile) {
      setError('Please select a dataset first.')
      return
    }

    setIsAnalyzing(true)
    setError('')
    setAnalysis(null)

    try {
      const result = await importDataset(selectedFile)
      setAnalysis(result)
    } catch (analysisError) {
      setError(
        analysisError?.response?.data?.detail ||
          analysisError?.message ||
          'Dataset analysis failed.'
      )
    } finally {
      setIsAnalyzing(false)
    }
  }
  const handleFileSelect = (event) => {
    const selected = event.target.files?.[0]

    if (!selected) return

    const allowedExtensions = ['.csv', '.json', '.xml']
    const extension = selected.name.slice(selected.name.lastIndexOf('.')).toLowerCase()

    if (!allowedExtensions.includes(extension)) {
      setError('Please select a CSV, JSON, or XML file.')
      setSelectedFile(null)
      return
    }

    setError('')
    setSelectedFile(selected)
  }

  const dashboardImportCard = (
    <div className="mb-8 rounded-2xl border border-slate-800 bg-slate-950 p-6">
      <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <Upload size={20} />
            <h2 className="text-lg font-semibold text-white">
              Import Investigation Dataset
            </h2>
          </div>

          <p className="mt-2 text-sm text-slate-400">
            Upload a CSV, JSON, or XML dataset to begin Bitcoin transaction analysis.
          </p>

          {selectedFile && (
            <p className="mt-3 text-sm text-slate-300">
              Selected: <span className="font-medium text-white">{selectedFile.name}</span>
            </p>
          )}
          {error && (
            <div className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              {error}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="inline-flex cursor-pointer items-center justify-center rounded-lg bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-slate-200">
            <Upload size={16} className="mr-2" />
            Choose Dataset
            <input
              type="file"
              accept=".csv,.json,.xml"
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>

          <button
            type="button"
            onClick={handleAnalyzeDataset}
            disabled={!selectedFile || isAnalyzing}
            className="inline-flex items-center justify-center rounded-lg border border-slate-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isAnalyzing ? 'Analyzing Dataset...' : 'Analyze Dataset'}
          </button>
        </div>
      </div>
    </div>
  )
  const [period, setPeriod] = useState('Last 7 days')
  const [dataset, setDataset] = useState('SIH Local Dataset')

  const dashboardStatus = useMemo(
    () => ({
      dataset,
      period,
    }),
    [dataset, period]
  )
  const analysisStats = useMemo(() => {
    if (!analysis) return null

    const alerts = Array.isArray(analysis.alerts) ? analysis.alerts : []

    const high = alerts.filter(
      (item) => Number(item?.risk_score ?? 0) >= 70
    ).length

    const medium = alerts.filter((item) => {
      const score = Number(item?.risk_score ?? 0)
      return score >= 40 && score < 70
    }).length

    const low = alerts.filter(
      (item) => Number(item?.risk_score ?? 0) < 40
    ).length

    return {
      transactions: Number(analysis.transactions_analyzed ?? 0),
      entities:
        Number(analysis.ip_entities ?? 0) +
        Number(analysis.wallet_entities ?? 0) +
        Number(analysis.transaction_entities ?? 0),
      anomalies: Number(analysis.anomalous_signals ?? 0),
      high,
      medium,
      low,
      alerts,
      observedEdges: Number(analysis.observed_edges ?? 0),
      associatedEdges: Number(analysis.associated_edges ?? 0),
      ipEntities: Number(analysis.ip_entities ?? 0),
      walletEntities: Number(analysis.wallet_entities ?? 0),
      transactionEntities: Number(analysis.transaction_entities ?? 0),
    }
  }, [analysis])

  const renderValue = (value) => {
    if (value === null || value === undefined || value === '') {
      return '—'
    }

    if (typeof value === 'object') {
      return JSON.stringify(value)
    }

    return String(value)
  }

  const analysisResultSection = analysis && analysisStats ? (
    <section className="mb-6 space-y-5">

      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-700">
              Analysis complete
            </p>

            <h2 className="mt-1 text-xl font-bold text-slate-950">
              {analysis.filename}
            </h2>

            <p className="mt-1 text-sm text-slate-600">
              Real investigation dataset processed by the ChainShield analysis pipeline.
            </p>
          </div>

          <span className="inline-flex w-fit items-center rounded-full border border-emerald-200 bg-white px-3 py-1.5 text-xs font-semibold text-emerald-700">
            {analysis.status || 'analysis_complete'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          icon={ArrowLeftRight}
          label="Transactions Analyzed"
          value={analysisStats.transactions.toLocaleString()}
          detail={`${Number(analysis.total_rows ?? 0).toLocaleString()} dataset rows`}
          iconClass="bg-blue-50 text-blue-600"
        />

        <MetricCard
          icon={ShieldAlert}
          label="Anomalous Signals"
          value={analysisStats.anomalies.toLocaleString()}
          detail="flagged by analysis"
          iconClass="bg-red-50 text-red-600"
        />

        <MetricCard
          icon={Network}
          label="Entities"
          value={analysisStats.entities.toLocaleString()}
          detail={`${analysisStats.ipEntities} IP • ${analysisStats.walletEntities} wallets`}
          iconClass="bg-slate-100 text-slate-600"
        />

        <MetricCard
          icon={Target}
          label="Graph Edges"
          value={(analysisStats.observedEdges + analysisStats.associatedEdges).toLocaleString()}
          detail={`${analysisStats.observedEdges} observed • ${analysisStats.associatedEdges} associated`}
          iconClass="bg-amber-50 text-amber-600"
        />
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 text-red-600">
              <ShieldAlert className="h-4 w-4" />
            </div>

            <div>
              <h2 className="text-base font-semibold text-slate-950">
                Detected Anomalies & Risk Alerts
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Transaction-level signals returned by the SIH Isolation Forest analysis.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-3">
          <div className="rounded-lg border border-red-100 bg-red-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-red-600">
              High Risk
            </p>
            <p className="mt-1 text-2xl font-bold text-red-700">
              {analysisStats.high}
            </p>
          </div>

          <div className="rounded-lg border border-amber-100 bg-amber-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-amber-600">
              Medium Risk
            </p>
            <p className="mt-1 text-2xl font-bold text-amber-700">
              {analysisStats.medium}
            </p>
          </div>

          <div className="rounded-lg border border-emerald-100 bg-emerald-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600">
              Low Risk
            </p>
            <p className="mt-1 text-2xl font-bold text-emerald-700">
              {analysisStats.low}
            </p>
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {analysisStats.alerts.slice(0, 10).map((alert, index) => (
            <div key={`${alert.transaction_id || 'alert'}-${index}`} className="p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">

                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <RiskBadge score={Number(alert.risk_score ?? 0)} />

                    <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
                      {alert.model || 'SIH Isolation Forest'}
                    </span>
                  </div>

                  <p className="mt-3 break-all font-mono text-sm font-semibold text-slate-900">
                    {alert.transaction_id || 'Unknown transaction'}
                  </p>

                  <div className="mt-3 grid grid-cols-1 gap-3 text-xs text-slate-500 sm:grid-cols-2">
                    <div>
                      <span className="font-semibold text-slate-700">Risk score:</span>{' '}
                      {renderValue(alert.risk_score)}
                    </div>

                    <div>
                      <span className="font-semibold text-slate-700">Anomaly score:</span>{' '}
                      {renderValue(alert.anomaly_score)}
                    </div>

                    <div>
                      <span className="font-semibold text-slate-700">Wallets:</span>{' '}
                      {Array.isArray(alert.wallets)
                        ? alert.wallets.join(', ')
                        : renderValue(alert.wallets)}
                    </div>

                    <div>
                      <span className="font-semibold text-slate-700">IPs:</span>{' '}
                      {Array.isArray(alert.ips)
                        ? alert.ips.join(', ')
                        : renderValue(alert.ips)}
                    </div>
                  </div>
                </div>

                <div className="shrink-0 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-right">
                  <p className="text-xs text-slate-400">Risk</p>
                  <p className="text-2xl font-bold text-slate-950">
                    {Number(alert.risk_score ?? 0).toFixed(2)}
                  </p>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">

                <div className="rounded-lg border border-slate-200 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Evidence
                  </p>

                  <div className="mt-2 space-y-2 text-xs leading-5 text-slate-600">
                    {Array.isArray(alert.evidence) && alert.evidence.length > 0 ? (
                      alert.evidence.slice(0, 4).map((item, evidenceIndex) => (
                        <div
                          key={evidenceIndex}
                          className="rounded-md bg-slate-50 p-2"
                        >
                          {renderValue(item)}
                        </div>
                      ))
                    ) : (
                      <p>No evidence details returned.</p>
                    )}
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Model Explanation
                  </p>

                  <div className="mt-2 space-y-2 text-xs leading-5 text-slate-600">
                    {Array.isArray(alert.explanations) && alert.explanations.length > 0 ? (
                      alert.explanations.slice(0, 4).map((item, explanationIndex) => (
                        <div
                          key={explanationIndex}
                          className="rounded-md bg-slate-50 p-2"
                        >
                          {renderValue(item)}
                        </div>
                      ))
                    ) : (
                      <p>No explanation details returned.</p>
                    )}
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    SHAP Explainability
                  </p>

                  <div className="mt-2 space-y-2 text-xs leading-5 text-slate-600">
                    {Array.isArray(alert.shap_explanations) && alert.shap_explanations.length > 0 ? (
                      alert.shap_explanations.slice(0, 4).map((item, shapIndex) => (
                        <div
                          key={shapIndex}
                          className="rounded-md bg-slate-50 p-2"
                        >
                          {renderValue(item)}
                        </div>
                      ))
                    ) : (
                      <p>No SHAP details returned for this alert.</p>
                    )}
                  </div>
                </div>

              </div>
            </div>
          ))}

          {analysisStats.alerts.length === 0 && (
            <div className="p-8 text-center text-sm text-slate-500">
              No anomaly alerts were returned for this dataset.
            </div>
          )}
        </div>

        {analysisStats.alerts.length > 10 && (
          <div className="border-t border-slate-100 px-6 py-4 text-xs text-slate-500">
            Showing the first 10 highest-priority alerts returned by the analysis.
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <Network className="h-4 w-4" />
            </div>

            <div>
              <h2 className="text-base font-semibold text-slate-950">
                Investigation Graph
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Entity relationships generated from the imported dataset.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 p-5 sm:grid-cols-4">
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-xs text-slate-500">IP Entities</p>
            <p className="mt-1 text-xl font-bold text-slate-950">
              {analysisStats.ipEntities}
            </p>
          </div>

          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-xs text-slate-500">Wallet Entities</p>
            <p className="mt-1 text-xl font-bold text-slate-950">
              {analysisStats.walletEntities}
            </p>
          </div>

          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-xs text-slate-500">Transactions</p>
            <p className="mt-1 text-xl font-bold text-slate-950">
              {analysisStats.transactionEntities}
            </p>
          </div>

          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-xs text-slate-500">Total Edges</p>
            <p className="mt-1 text-xl font-bold text-slate-950">
              {(analysisStats.observedEdges + analysisStats.associatedEdges).toLocaleString()}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-4">
          <p className="text-xs leading-5 text-slate-500">
            Graph relationships are investigative observations and should be interpreted with the supporting transaction evidence.
          </p>

          <Link
            to="/graph"
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            Open Entity Graph
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
      </div>

      <div className="rounded-lg border border-amber-100 bg-amber-50 px-4 py-3">
        <p className="text-xs leading-5 text-amber-800">
          {analysis.disclaimer ||
            'Anomaly and risk scores are investigative signals and do not constitute proof of malicious or illegal activity.'}
        </p>
      </div>
    </section>
  ) : null

  return (
    <div className="min-h-full bg-slate-50 text-slate-900">
      <div className="mx-auto max-w-[1700px] px-5 py-6 sm:px-6 lg:px-8 lg:py-8">
        {dashboardImportCard}
        {/* HEADER */}
        <header className="mb-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />

                <span className="text-xs font-semibold text-emerald-700">
                  Investigation workspace offline
                </span>
              </div>

              <h1 className="text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
                Welcome Back, Investigator
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 sm:text-base">
                Monitor transaction activity, review investigation leads,
                and analyse network-to-blockchain relationships.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <Link
                to="/data-sources"
                className="inline-flex h-10 items-center gap-2 rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                <Upload className="h-4 w-4" />
                Import Dataset
              </Link>

              <div className="relative">
                <CalendarDays className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

                <select
                  value={period}
                  onChange={(event) => setPeriod(event.target.value)}
                  className="h-10 appearance-none rounded-lg border border-slate-200 bg-white pl-10 pr-9 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                  aria-label="Analysis period"
                >
                  <option>Last 7 days</option>
                  <option>Last 30 days</option>
                  <option>Last 90 days</option>
                </select>

                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              </div>

              <div className="relative">
                <Database className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

                <select
                  value={dataset}
                  onChange={(event) => setDataset(event.target.value)}
                  className="h-10 appearance-none rounded-lg border border-slate-200 bg-white pl-10 pr-9 text-sm font-medium text-slate-700 shadow-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
                  aria-label="Dataset"
                >
                  <option>SIH Local Dataset</option>
                  <option>Elliptic Dataset</option>
                  <option>All Local Datasets</option>
                </select>

                <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              </div>
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-slate-200 pt-4">
            <span className="inline-flex items-center gap-2 text-xs font-medium text-slate-500">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              Local analysis environment
            </span>

            <span className="h-1 w-1 rounded-full bg-slate-300" />

            <span className="text-xs text-slate-400">
              Dataset: {dashboardStatus.dataset}
            </span>

            <span className="h-1 w-1 rounded-full bg-slate-300" />

            <span className="text-xs text-slate-400">
              Period: {dashboardStatus.period}
            </span>
          </div>
        </header>

        {/* KPI CARDS */}
        <section
          aria-label="Investigation metrics"
          className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
        >
          <MetricCard
            icon={ArrowLeftRight}
            label="Total Transactions"
            value={analysisStats ? analysisStats.transactions.toLocaleString() : "—"}
            trend={analysisStats ? "" : "+8.4%"}
            detail={analysisStats ? "from imported dataset" : "vs previous period"}
            iconClass="bg-blue-50 text-blue-600"
          />

          <MetricCard
            icon={Network}
            label="Unique Entities"
            value={analysisStats ? analysisStats.entities.toLocaleString() : "—"}
            trend={analysisStats ? "" : "+5.7%"}
            detail={analysisStats ? "IP + wallet + transaction entities" : "transactions, wallets & IPs"}
            iconClass="bg-slate-100 text-slate-600"
          />

          <MetricCard
            icon={ShieldAlert}
            label="High Risk Leads"
            value={analysisStats ? analysisStats.high.toLocaleString() : "—"}
            trend={analysisStats ? "" : "+12.2%"}
            detail={analysisStats ? "risk score >= 70" : "requires investigator review"}
            iconClass="bg-red-50 text-red-600"
          />

          <MetricCard
            icon={Target}
            label="Medium Risk Leads"
            value={analysisStats ? analysisStats.medium.toLocaleString() : "—"}
            trend={analysisStats ? "" : "+4.1%"}
            detail={analysisStats ? "risk score 40–69" : "potential investigation leads"}
            iconClass="bg-amber-50 text-amber-600"
          />
        </section>

        {analysisResultSection}

        {/* PRIMARY ANALYTICS */}
        <section className="mb-6 grid grid-cols-1 gap-5 xl:grid-cols-[1.7fr_1fr]">
          <RiskTrendChart />
          <RiskDistribution />
        </section>

        {/* INVESTIGATION DATA */}
        <section className="grid grid-cols-1 gap-5 xl:grid-cols-[1.7fr_1fr]">

          {/* TOP LEADS */}
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-col gap-3 border-b border-slate-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-base font-semibold text-slate-950">
                  Top Investigation Leads
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Highest-priority entities requiring review
                </p>
              </div>

              <Link
                to="/investigations"
                className="inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-700"
              >
                View all
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px]">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <th className="px-6 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Rank
                    </th>

                    <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Entity
                    </th>

                    <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Type
                    </th>

                    <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Risk
                    </th>

                    <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Reason
                    </th>

                    <th className="px-6 py-3 text-right text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-100">
                  {leads.map((lead) => (
                    <tr
                      key={lead.rank}
                      className="transition-colors hover:bg-slate-50"
                    >
                      <td className="px-6 py-4 text-sm font-semibold text-slate-400">
                        #{lead.rank}
                      </td>

                      <td className="px-3 py-4">
                        <span className="font-mono text-sm text-slate-800">
                          {lead.entity}
                        </span>
                      </td>

                      <td className="px-3 py-4">
                        <span className="inline-flex items-center gap-2 text-sm text-slate-600">
                          <LeadTypeIcon type={lead.type} />
                          {lead.type}
                        </span>
                      </td>

                      <td className="px-3 py-4">
                        <div className="flex items-center gap-2">
                          <RiskBadge score={lead.score} />

                          <span className="text-sm font-bold text-slate-700">
                            {lead.score}
                          </span>
                        </div>
                      </td>

                      <td className="px-3 py-4 text-sm text-slate-500">
                        {lead.reason}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <Link
                          to="/investigations"
                          className="text-sm font-semibold text-blue-600 hover:text-blue-700"
                        >
                          Investigate
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* RECENT INVESTIGATIONS */}
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-6 py-5">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-slate-950">
                    Recent Investigations
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    Latest investigation activity
                  </p>
                </div>

                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
                  <Activity className="h-4 w-4" />
                </div>
              </div>
            </div>

            <div className="divide-y divide-slate-100">
              {recentInvestigations.map((item) => (
                <div
                  key={item.id}
                  className="px-6 py-4 transition-colors hover:bg-slate-50"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs text-slate-400">
                          {item.id}
                        </span>

                        <RiskBadge score={item.score} />
                      </div>

                      <p className="mt-2 truncate text-sm font-semibold text-slate-800">
                        {item.name}
                      </p>

                      <p className="mt-1 text-xs text-slate-400">
                        {item.date}
                      </p>
                    </div>

                    <span className="shrink-0 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                      {item.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <div className="border-t border-slate-100 px-6 py-4">
              <Link
                to="/investigations"
                className="inline-flex items-center gap-2 text-sm font-semibold text-blue-600 hover:text-blue-700"
              >
                Open investigation workspace
                <ArrowUpRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>

        {/* QUICK ACTIONS */}
        <section className="mt-6 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-5">
            <h2 className="text-base font-semibold text-slate-950">
              Investigation Workflow
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Start an investigation from the primary workflow actions
            </p>
          </div>

          <div className="grid grid-cols-1 divide-y divide-slate-100 sm:grid-cols-2 sm:divide-x sm:divide-y-0 xl:grid-cols-4">
            <QuickAction
              to="/data-sources"
              icon={Upload}
              title="Import Dataset"
              description="Upload CSV, JSON or XML data"
              primary
            />

            <QuickAction
              to="/transactions"
              icon={ArrowLeftRight}
              title="Search Transaction"
              description="Find a TXID, wallet or IP"
            />

            <QuickAction
              to="/graph"
              icon={Network}
              title="Entity Graph"
              description="Explore IP, transaction and wallet relationships"
            />

            <QuickAction
              to="/reports"
              icon={FileText}
              title="Investigation Reports"
              description="Review and export investigation findings"
            />
          </div>
        </section>

        {/* DATA NOTICE */}
        <div className="mt-5 flex items-start gap-3 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />

          <p className="text-xs leading-5 text-blue-800">
            Dashboard figures currently represent interface demonstration
            data. Investigation conclusions must be based on analysed local
            datasets, model outputs, graph relationships and supporting
            evidence.
          </p>
        </div>
      </div>
    </div>
  )
}




















import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search,
  SlidersHorizontal,
  ArrowRight,
  AlertTriangle,
  CheckCircle2,
  Info,
  Loader2,
  X,
  Network,
  Shield,
  Database,
  FileSearch,
  ExternalLink,
} from 'lucide-react'
import { analyzeTransaction } from '../api.js'

const searchTypes = ['All', 'Transaction ID']

function shorten(value, start = 14, end = 10) {
  if (!value || value.length <= start + end + 3) return value
  return `${value.slice(0, start)}...${value.slice(-end)}`
}

function RiskBadge({ score }) {
  if (score == null) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border border-black bg-white px-3 py-1.5 text-xs font-medium text-black">
        <Info size={13} />
        Risk unavailable
      </span>
    )
  }

  if (score >= 70) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-black px-3 py-1.5 text-xs font-semibold text-white">
        <AlertTriangle size={13} />
        High Risk · {score.toFixed(1)}
      </span>
    )
  }

  if (score >= 40) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full border-2 border-black bg-white px-3 py-1.5 text-xs font-semibold text-black">
        <AlertTriangle size={13} />
        Medium Risk · {score.toFixed(1)}
      </span>
    )
  }

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-black bg-white px-3 py-1.5 text-xs font-semibold text-black">
      <CheckCircle2 size={13} />
      Low Risk · {score.toFixed(1)}
    </span>
  )
}

function MetricCard({ label, value, description }) {
  return (
    <div className="rounded-xl border border-black bg-white p-5">
      <p className="text-xs font-medium uppercase tracking-wider text-black/50">
        {label}
      </p>

      <p className="mt-3 text-2xl font-bold tracking-tight text-black">
        {value}
      </p>

      {description && (
        <p className="mt-1 text-xs leading-5 text-black/50">
          {description}
        </p>
      )}
    </div>
  )
}

export default function TransactionSearch() {
  const navigate = useNavigate()

  const [query, setQuery] = useState('')
  const [searchType, setSearchType] = useState('All')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function handleSearch(event) {
    event.preventDefault()

    const value = query.trim()

    if (!value) {
      setError('Enter a transaction ID to begin the analysis.')
      setResult(null)
      return
    }

    if (searchType !== 'All' && searchType !== 'Transaction ID') {
      setError(
        `${searchType} search is not available on the current analysis endpoint.`
      )
      setResult(null)
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const data = await analyzeTransaction(value)
      setResult(data)
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          'Transaction could not be analyzed. Check the transaction ID and backend connection.'
      )
    } finally {
      setLoading(false)
    }
  }

  function clearSearch() {
    setQuery('')
    setResult(null)
    setError('')
  }

  return (
    <div className="min-h-full bg-white text-black">
      <div className="mx-auto max-w-7xl px-6 py-8 lg:px-8">

        {/* Header */}
        <header className="mb-8 border-b border-black pb-6">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-black/50">
                <Shield size={14} />
                Investigation Workspace
              </div>

              <h1 className="text-3xl font-bold tracking-tight">
                Transaction Search
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-black/55">
                Search a Bitcoin transaction and inspect its anomaly signals,
                risk indicators, network entities and supporting evidence.
              </p>
            </div>

            <div className="flex items-center gap-2 rounded-full border border-black px-4 py-2 text-xs font-medium">
              <span className="h-2 w-2 rounded-full bg-black" />
              Local investigation dataset
            </div>
          </div>
        </header>

        {/* Search Section */}
        <section className="rounded-2xl border-2 border-black bg-black p-5 lg:p-6">
          <div className="mb-5 flex items-center gap-3 text-white">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/30">
              <Search size={18} />
            </div>

            <div>
              <h2 className="text-sm font-semibold">
                Search transaction activity
              </h2>

              <p className="mt-1 text-xs text-white/55">
                Run the ChainShield analysis pipeline for a transaction.
              </p>
            </div>
          </div>

          <form onSubmit={handleSearch}>
            <div className="flex flex-col gap-3 lg:flex-row">
              <div className="relative flex-1">
                <Search
                  size={19}
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-black/40"
                />

                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter Bitcoin transaction ID..."
                  className="h-13 w-full rounded-xl border border-white bg-white pl-11 pr-11 text-sm text-black outline-none placeholder:text-black/35 focus:ring-2 focus:ring-white/50"
                />

                {query && (
                  <button
                    type="button"
                    onClick={clearSearch}
                    className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-black/45 hover:bg-black/5 hover:text-black"
                    aria-label="Clear search"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="inline-flex h-13 items-center justify-center gap-2 rounded-xl border border-white bg-white px-7 text-sm font-semibold text-black transition hover:bg-black hover:text-white disabled:cursor-not-allowed disabled:opacity-60 lg:min-w-[145px]"
              >
                {loading ? (
                  <>
                    <Loader2 size={17} className="animate-spin" />
                    Analyzing
                  </>
                ) : (
                  <>
                    Analyze
                    <ArrowRight size={17} />
                  </>
                )}
              </button>
            </div>
          </form>

          <div className="mt-4 flex flex-wrap items-center gap-2">
            <div className="mr-1 flex items-center gap-2 text-xs font-medium text-white/55">
              <SlidersHorizontal size={14} />
              Search by
            </div>

            {searchTypes.map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => {
                  setSearchType(type)
                  setError('')
                }}
                className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                  searchType === type
                    ? 'border-white bg-white text-black'
                    : 'border-white/30 bg-transparent text-white/65 hover:border-white hover:text-white'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </section>

        {/* Error */}
        {error && (
          <section className="mt-5 rounded-xl border-2 border-black bg-white p-5">
            <div className="flex items-start gap-3">
              <AlertTriangle size={18} className="mt-0.5 shrink-0" />

              <div>
                <p className="text-sm font-semibold">
                  Search could not be completed
                </p>

                <p className="mt-1 text-xs leading-5 text-black/55">
                  {error}
                </p>
              </div>
            </div>
          </section>
        )}

        {/* Empty State */}
        {!loading && !result && !error && (
          <section className="mt-6 rounded-2xl border border-black bg-white">
            <div className="px-6 py-20 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-black text-white">
                <FileSearch size={26} />
              </div>

              <h2 className="mt-5 text-lg font-semibold">
                Ready for investigation
              </h2>

              <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-black/50">
                Enter a transaction ID above to run anomaly analysis and
                inspect the transaction's risk indicators and supporting evidence.
              </p>

              <div className="mx-auto mt-8 grid max-w-3xl grid-cols-1 gap-3 text-left sm:grid-cols-3">
                <div className="rounded-xl border border-black p-4">
                  <Database size={18} />
                  <p className="mt-3 text-sm font-semibold">
                    Transaction data
                  </p>
                  <p className="mt-1 text-xs leading-5 text-black/50">
                    Inspect the analyzed transaction and observations.
                  </p>
                </div>

                <div className="rounded-xl border border-black p-4">
                  <Shield size={18} />
                  <p className="mt-3 text-sm font-semibold">
                    Risk analysis
                  </p>
                  <p className="mt-1 text-xs leading-5 text-black/50">
                    Review anomaly and risk signals produced by the model.
                  </p>
                </div>

                <div className="rounded-xl border border-black p-4">
                  <Network size={18} />
                  <p className="mt-3 text-sm font-semibold">
                    Entity relationships
                  </p>
                  <p className="mt-1 text-xs leading-5 text-black/50">
                    Inspect related wallets and network observations.
                  </p>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Loading */}
        {loading && (
          <section className="mt-6 rounded-2xl border-2 border-black bg-black p-10 text-center text-white">
            <Loader2 size={30} className="mx-auto animate-spin" />

            <h2 className="mt-4 text-sm font-semibold">
              Running ChainShield analysis
            </h2>

            <p className="mt-2 text-xs text-white/55">
              Extracting features, evaluating anomaly signals and preparing evidence.
            </p>
          </section>
        )}

        {/* Results */}
        {result && !loading && (
          <section className="mt-6">

            {/* Result header */}
            <div className="mb-5 flex flex-col gap-4 rounded-2xl border-2 border-black bg-black p-5 text-white lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-white/50">
                  Analysis Result
                </p>

                <h2 className="mt-2 text-xl font-bold">
                  Transaction investigation lead
                </h2>

                <p className="mt-2 break-all font-mono text-xs text-white/55">
                  {result.transaction_id}
                </p>
              </div>

              <RiskBadge score={result.risk_score} />
            </div>

            {/* Metrics */}
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Risk Score"
                value={
                  result.risk_score != null
                    ? result.risk_score.toFixed(1)
                    : '—'
                }
                description="Fused investigation risk signal"
              />

              <MetricCard
                label="Anomaly"
                value={result.is_anomaly ? 'Detected' : 'Not detected'}
                description="Isolation Forest signal"
              />

              <MetricCard
                label="Observations"
                value={result.observation_count ?? 0}
                description="Dataset observations"
              />

              <MetricCard
                label="Model"
                value={result.model || 'SIH Analysis'}
                description="Analysis engine"
              />
            </div>

            {/* Entity sections */}
            <div className="mt-5 grid gap-5 lg:grid-cols-2">

              {/* IPs */}
              <div className="rounded-2xl border border-black bg-white p-5">
                <div className="flex items-center justify-between border-b border-black pb-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-black/45">
                      Network
                    </p>

                    <h3 className="mt-1 text-base font-semibold">
                      IP observations
                    </h3>
                  </div>

                  <Network size={19} />
                </div>

                <div className="mt-4 space-y-2">
                  {(result.ips || []).length > 0 ? (
                    result.ips.map((ip) => (
                      <div
                        key={ip}
                        className="flex items-center justify-between rounded-lg border border-black px-3 py-2.5"
                      >
                        <span className="font-mono text-xs">
                          {ip}
                        </span>

                        <span className="text-[10px] uppercase tracking-wider text-black/40">
                          observed
                        </span>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-black/45">
                      No IP observations returned.
                    </p>
                  )}
                </div>
              </div>

              {/* Wallets */}
              <div className="rounded-2xl border border-black bg-white p-5">
                <div className="flex items-center justify-between border-b border-black pb-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-black/45">
                      Blockchain
                    </p>

                    <h3 className="mt-1 text-base font-semibold">
                      Wallet entities
                    </h3>
                  </div>

                  <Database size={19} />
                </div>

                <div className="mt-4 space-y-2">
                  {(result.wallets || []).length > 0 ? (
                    result.wallets.map((wallet) => (
                      <div
                        key={wallet}
                        title={wallet}
                        className="rounded-lg border border-black px-3 py-2.5 font-mono text-xs"
                      >
                        {shorten(wallet, 20, 12)}
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-black/45">
                      No wallet entities returned.
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Evidence */}
            {result.evidence?.length > 0 && (
              <div className="mt-5 rounded-2xl border border-black bg-white">
                <div className="flex items-center justify-between border-b border-black px-5 py-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-black/45">
                      Investigation
                    </p>

                    <h3 className="mt-1 text-base font-semibold">
                      Supporting evidence
                    </h3>
                  </div>

                  <FileSearch size={19} />
                </div>

                <div className="divide-y divide-black/15">
                  {result.evidence.map((item, index) => (
                    <div
                      key={`${item.feature}-${index}`}
                      className="grid gap-3 px-5 py-4 md:grid-cols-[120px_1fr_180px]"
                    >
                      <span className="text-xs font-semibold uppercase tracking-wide text-black/45">
                        {item.type}
                      </span>

                      <span className="break-all font-mono text-xs">
                        {item.feature}
                      </span>

                      <span className="break-all text-xs font-medium">
                        {String(item.value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Explanations */}
            {result.explanations?.length > 0 && (
              <div className="mt-5 rounded-2xl border border-black bg-white p-5">
                <div className="flex items-center gap-3 border-b border-black pb-4">
                  <Shield size={19} />

                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-black/45">
                      Explainability
                    </p>

                    <h3 className="mt-1 text-base font-semibold">
                      Model explanations
                    </h3>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  {result.explanations.map((item, index) => (
                    <div
                      key={index}
                      className="rounded-lg border border-black p-4 text-sm leading-6"
                    >
                      {typeof item === 'string'
                        ? item
                        : item?.text ||
                          item?.explanation ||
                          JSON.stringify(item)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* SHAP */}
            {result.shap_explanations?.length > 0 && (
              <div className="mt-5 rounded-2xl border-2 border-black bg-black p-5 text-white">
                <div className="flex items-center gap-3 border-b border-white/20 pb-4">
                  <Shield size={19} />

                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-white/45">
                      Explainable AI
                    </p>

                    <h3 className="mt-1 text-base font-semibold">
                      SHAP analysis
                    </h3>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  {result.shap_explanations.map((item, index) => (
                    <div
                      key={index}
                      className="rounded-lg border border-white/20 bg-white/5 p-4 text-sm leading-6 text-white/80"
                    >
                      {typeof item === 'string'
                        ? item
                        : item?.text ||
                          item?.explanation ||
                          JSON.stringify(item)}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="mt-5 flex flex-col gap-3 rounded-2xl border border-black bg-white p-5 sm:flex-row">
              <button
                onClick={() =>
                  navigate('/investigations/' + result.transaction_id)
                }
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-black px-5 py-3 text-sm font-semibold text-white transition hover:bg-black/80"
              >
                Open Investigation
                <ArrowRight size={17} />
              </button>

              <button
                onClick={() => navigate('/graph')}
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl border-2 border-black bg-white px-5 py-3 text-sm font-semibold text-black transition hover:bg-black hover:text-white"
              >
                View Entity Graph
                <ExternalLink size={17} />
              </button>
            </div>

            {/* Disclaimer */}
            {result.disclaimer && (
              <div className="mt-5 rounded-xl border border-black bg-white p-4">
                <div className="flex gap-3">
                  <Info size={17} className="mt-0.5 shrink-0" />

                  <p className="text-xs leading-5 text-black/60">
                    {result.disclaimer}
                  </p>
                </div>
              </div>
            )}
          </section>
        )}
      </div>
    </div>
  )
}

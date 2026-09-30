import { useState } from 'react'
import RiskGauge from '../components/RiskGauge.jsx'
import BreakdownChart from '../components/BreakdownChart.jsx'
import { setMode, analyzeTransaction } from '../api.js'

export default function InvestigationDetail() {
  const [mode, setModeState] = useState('offline')
  const [txid, setTxid] = useState('2984918')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleModeChange = async (newMode) => {
    setModeState(newMode)
    await setMode(newMode)
    setResult(null)
    setError(null)
  }

  const handleAnalyze = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await analyzeTransaction(txid)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-8">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <h1 className="text-2xl font-bold tracking-tight">
            ChainShield <span className="text-sky-400">AI</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            AI-Powered Monitoring &amp; Analysis of Bitcoin Transaction Traffic
          </p>
        </header>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-sm text-slate-400">Mode:</span>
            <button
              onClick={() => handleModeChange('offline')}
              className={"px-3 py-1 rounded-full text-xs font-medium border " + (mode === 'offline' ? 'bg-sky-500/20 border-sky-500 text-sky-300' : 'border-slate-700 text-slate-400')}
            >
              Offline (Elliptic Model)
            </button>
            <button
              onClick={() => handleModeChange('live')}
              className={"px-3 py-1 rounded-full text-xs font-medium border " + (mode === 'live' ? 'bg-sky-500/20 border-sky-500 text-sky-300' : 'border-slate-700 text-slate-400')}
            >
              Live (Mempool.space)
            </button>
          </div>

          <div className="flex gap-3">
            <input
              value={txid}
              onChange={(e) => setTxid(e.target.value)}
              placeholder={mode === 'offline' ? 'Elliptic txId, e.g. 2984918' : 'Real Bitcoin TXID'}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-sky-500"
            />
            <button
              onClick={handleAnalyze}
              disabled={loading || !txid}
              className="bg-sky-500 hover:bg-sky-400 disabled:opacity-50 disabled:cursor-not-allowed text-slate-950 font-semibold px-5 py-2 rounded-lg text-sm"
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/40 text-red-300 rounded-lg px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}

        {result && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <RiskGauge score={result.total_risk_score} />
              <div className="text-center text-xs text-slate-500 mt-2">
                Path: {result.path}
              </div>
            </div>

            {result.breakdown && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-slate-300 mb-2">Score Breakdown</h3>
                <BreakdownChart breakdown={result.breakdown} />
              </div>
            )}

            {result.graph_reason && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 md:col-span-2">
                <h3 className="text-sm font-semibold text-slate-300 mb-2">Graph Signal</h3>
                <p className="text-sm text-amber-300">Warning: {result.graph_reason}</p>
              </div>
            )}

            {result.explainability && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 md:col-span-2">
                <h3 className="text-sm font-semibold text-slate-300 mb-3">
                  Why this score? (Top contributing features)
                </h3>
                <div className="space-y-2">
                  {result.explainability.top_contributing_features.map((f, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">{f.feature}</span>
                      <span className={f.impact >= 0 ? 'font-mono text-red-400' : 'font-mono text-emerald-400'}>
                        {f.impact >= 0 ? '+' : ''}
                        {f.impact}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.reasons && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 md:col-span-2">
                <h3 className="text-sm font-semibold text-slate-300 mb-2">Flagged Reasons</h3>
                <ul className="list-disc list-inside text-sm text-amber-300 space-y-1">
                  {result.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="md:col-span-2 text-xs text-slate-500 italic border-t border-slate-800 pt-3">
              {result.disclaimer}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

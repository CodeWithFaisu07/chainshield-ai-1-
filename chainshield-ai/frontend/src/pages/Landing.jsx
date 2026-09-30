import { useNavigate } from 'react-router-dom'

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center px-6">
      <div className="max-w-2xl text-center">
        <h1 className="text-4xl font-bold tracking-tight mb-4">
          ChainShield <span className="text-sky-400">AI</span>
        </h1>
        <p className="text-slate-400 text-lg mb-2">
          AI-Powered Monitoring &amp; Analysis of Bitcoin Transaction Traffic
        </p>
        <p className="text-slate-500 text-sm mb-10">
          SIH26146 — Machine Learning risk scoring, anomaly detection, and graph-based
          analysis for Bitcoin transactions. Built on the Elliptic dataset with real-time
          mempool.space integration.
        </p>

        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => navigate('/login')}
            className="bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold px-6 py-3 rounded-lg text-sm"
          >
            Get Started
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="border border-slate-700 hover:bg-slate-800 text-slate-300 font-medium px-6 py-3 rounded-lg text-sm"
          >
            Skip to Dashboard
          </button>
        </div>

        <div className="grid grid-cols-3 gap-4 mt-16 text-left">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-sky-400 text-sm font-semibold mb-1">ML Classification</div>
            <div className="text-slate-500 text-xs">RandomForest trained on 200k+ labeled transactions</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-sky-400 text-sm font-semibold mb-1">Anomaly Detection</div>
            <div className="text-slate-500 text-xs">IsolationForest flags unusual patterns</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-sky-400 text-sm font-semibold mb-1">Graph Analysis</div>
            <div className="text-slate-500 text-xs">Network-level fan-in/fan-out risk signals</div>
          </div>
        </div>
      </div>
    </div>
  )
}

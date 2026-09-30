import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Upload,
  Search,
  Database,
  BrainCircuit,
  Network,
  ShieldAlert,
  FileSearch,
  FileText,
  ArrowRight,
} from 'lucide-react'

export default function Investigations() {
  const navigate = useNavigate()
  const [txid, setTxid] = useState('')

  const handleOpen = () => {
    if (!txid.trim()) return
    navigate('/investigations/' + txid.trim())
  }

  return (
    <div className="p-8 text-slate-100">

      {/* Page Header */}
      <div className="mb-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Investigations
            </h1>

            <p className="text-slate-400 text-sm mt-1">
              Create, analyze and investigate Bitcoin transaction datasets.
            </p>
          </div>

          <button
            onClick={() => navigate('/data-sources')}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold px-4 py-2.5 text-sm transition"
          >
            <Upload className="h-4 w-4" />
            Import Dataset
          </button>
        </div>
      </div>

      {/* Investigation Entry */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
        <div className="flex items-start gap-3 mb-5">
          <div className="rounded-lg bg-sky-500/10 p-2">
            <Search className="h-5 w-5 text-sky-400" />
          </div>

          <div>
            <h2 className="text-sm font-semibold">
              Open Transaction Investigation
            </h2>

            <p className="text-xs text-slate-500 mt-1">
              Investigate a specific Bitcoin transaction using its transaction ID.
            </p>
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-3">
          <input
            value={txid}
            onChange={(e) => setTxid(e.target.value)}
            placeholder="Enter transaction ID"
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-sky-500"
          />

          <button
            onClick={handleOpen}
            disabled={!txid.trim()}
            className="inline-flex items-center justify-center gap-2 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 disabled:cursor-not-allowed text-slate-950 font-semibold px-5 py-2.5 rounded-lg text-sm transition"
          >
            Open Investigation
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Dataset Investigation */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-indigo-500/10 p-2">
              <Database className="h-5 w-5 text-indigo-400" />
            </div>

            <div>
              <h2 className="text-sm font-semibold">
                Dataset Investigation
              </h2>

              <p className="text-xs text-slate-500 mt-1">
                Import your investigation dataset and run the complete ChainShield analysis pipeline.
              </p>
            </div>
          </div>

          <span className="hidden sm:inline-flex items-center rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-400">
            CSV / JSON / XML
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

          <div className="border border-slate-800 rounded-lg p-4 bg-slate-950/40">
            <Database className="h-5 w-5 text-sky-400" />

            <p className="font-medium mt-3">
              Import & Validate
            </p>

            <p className="text-xs text-slate-500 mt-1 leading-5">
              Parse the investigator-provided dataset and validate its structure.
            </p>
          </div>

          <div className="border border-slate-800 rounded-lg p-4 bg-slate-950/40">
            <BrainCircuit className="h-5 w-5 text-violet-400" />

            <p className="font-medium mt-3">
              AI Analysis
            </p>

            <p className="text-xs text-slate-500 mt-1 leading-5">
              Extract features, detect anomalous behaviour and calculate risk signals.
            </p>
          </div>

          <div className="border border-slate-800 rounded-lg p-4 bg-slate-950/40">
            <Network className="h-5 w-5 text-emerald-400" />

            <p className="font-medium mt-3">
              Graph Investigation
            </p>

            <p className="text-xs text-slate-500 mt-1 leading-5">
              Explore transaction, wallet and network relationships.
            </p>
          </div>
        </div>

        <button
          onClick={() => navigate('/data-sources')}
          className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-sky-400 hover:text-sky-300 transition"
        >
          Start dataset investigation
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>

      {/* Investigation Workflow */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="flex items-start gap-3 mb-6">
          <div className="rounded-lg bg-amber-500/10 p-2">
            <ShieldAlert className="h-5 w-5 text-amber-400" />
          </div>

          <div>
            <h2 className="text-sm font-semibold">
              Investigation Workflow
            </h2>

            <p className="text-xs text-slate-500 mt-1">
              From imported blockchain data to explainable investigation findings.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">

          <div className="border border-slate-800 rounded-lg p-4">
            <p className="text-sky-400 text-xs font-semibold">01</p>
            <p className="font-medium mt-2">Import Dataset</p>
            <p className="text-xs text-slate-500 mt-1 leading-5">
              Upload CSV, JSON or XML investigation data.
            </p>
          </div>

          <div className="border border-slate-800 rounded-lg p-4">
            <p className="text-sky-400 text-xs font-semibold">02</p>
            <p className="font-medium mt-2">Analyze Transactions</p>
            <p className="text-xs text-slate-500 mt-1 leading-5">
              Run feature extraction and the trained anomaly model.
            </p>
          </div>

          <div className="border border-slate-800 rounded-lg p-4">
            <p className="text-sky-400 text-xs font-semibold">03</p>
            <p className="font-medium mt-2">Detect Patterns</p>
            <p className="text-xs text-slate-500 mt-1 leading-5">
              Identify unusual transaction and network behaviour.
            </p>
          </div>

          <div className="border border-slate-800 rounded-lg p-4">
            <p className="text-sky-400 text-xs font-semibold">04</p>
            <p className="font-medium mt-2">Investigate Graph</p>
            <p className="text-xs text-slate-500 mt-1 leading-5">
              Trace relationships between transactions, wallets and IP observations.
            </p>
          </div>

          <div className="border border-slate-800 rounded-lg p-4">
            <p className="text-sky-400 text-xs font-semibold">05</p>
            <p className="font-medium mt-2">Review Evidence</p>
            <p className="text-xs text-slate-500 mt-1 leading-5">
              Review anomaly signals, evidence and model explanations.
            </p>
          </div>

          <div className="border border-slate-800 rounded-lg p-4">
            <p className="text-sky-400 text-xs font-semibold">06</p>
            <p className="font-medium mt-2">Generate Findings</p>
            <p className="text-xs text-slate-500 mt-1 leading-5">
              Prepare an investigation report from the analyzed results.
            </p>
          </div>

        </div>
      </div>

      {/* Investigation note */}
      <div className="mt-5 flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-950/50 p-4">
        <FileSearch className="h-4 w-4 text-slate-500 mt-0.5" />

        <p className="text-xs text-slate-500 leading-5">
          Risk and anomaly results are investigative signals. They do not by themselves establish malicious or illegal activity.
        </p>
      </div>

    </div>
  )
}
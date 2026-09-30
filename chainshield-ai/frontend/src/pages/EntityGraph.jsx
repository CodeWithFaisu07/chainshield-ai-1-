import { useState } from 'react'
import { getSihTransactionGraph } from '../api.js'

const DEFAULT_TXID =
  '89d881492777c30734ca4d55958246638b04503cc75a5e957ca33df75fb48b4c'

function NodeCard({ node }) {
  const typeStyles = {
    IP: 'border-sky-500/40 bg-sky-500/10 text-sky-300',
    TRANSACTION: 'border-violet-500/40 bg-violet-500/10 text-violet-300',
    WALLET: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
  }

  return (
    <div
      className={`rounded-xl border p-4 min-w-[220px] max-w-[320px] ${
        typeStyles[node.node_type] || 'border-slate-700 bg-slate-800'
      }`}
    >
      <div className="text-xs font-semibold uppercase tracking-wide mb-2">
        {node.node_type}
      </div>

      <div className="font-mono text-xs break-all text-slate-200">
        {node.value}
      </div>

      {node.first_seen && (
        <div className="mt-3 text-xs text-slate-400">
          First seen: {node.first_seen}
        </div>
      )}

      {node.last_seen && node.last_seen !== node.first_seen && (
        <div className="mt-1 text-xs text-slate-400">
          Last seen: {node.last_seen}
        </div>
      )}
    </div>
  )
}

function EdgeDetails({ edge }) {
  return (
    <div className="flex flex-col items-center py-3">
      <div className="text-xs font-semibold text-slate-400">
        {edge.relationship}
      </div>

      <div className="text-slate-500 text-xl leading-none my-1">
        ↓
      </div>

      <div className="flex flex-wrap justify-center gap-2 text-[11px]">
        {edge.port_no !== undefined && edge.port_no !== null && (
          <span className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sky-300">
            Port: {edge.port_no}
          </span>
        )}

        {edge.timestamp && (
          <span className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-300">
            Time: {edge.timestamp}
          </span>
        )}

        {edge.bitcoin_transferred !== undefined &&
          edge.bitcoin_transferred !== null && (
            <span className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-emerald-300">
              BTC: {edge.bitcoin_transferred}
            </span>
          )}
      </div>
    </div>
  )
}

export default function EntityGraph() {
  const [txid, setTxid] = useState(DEFAULT_TXID)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleGraph = async () => {
    setLoading(true)
    setError(null)

    try {
      const data = await getSihTransactionGraph(txid.trim())
      setResult(data)
    } catch (e) {
      setError(
        e.response?.data?.detail ||
          'SIH transaction graph could not be loaded'
      )
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  const ipNodes =
    result?.nodes?.filter((node) => node.node_type === 'IP') || []

  const transactionNodes =
    result?.nodes?.filter(
      (node) => node.node_type === 'TRANSACTION'
    ) || []

  const walletNodes =
    result?.nodes?.filter(
      (node) => node.node_type === 'WALLET'
    ) || []

  const observationEdges =
    result?.edges?.filter(
      (edge) => edge.relationship === 'OBSERVED'
    ) || []

  const associationEdges =
    result?.edges?.filter(
      (edge) => edge.relationship === 'ASSOCIATED'
    ) || []

  return (
    <div className="p-8 text-slate-100">
      <div className="mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">
              SIH Entity Graph
            </h1>

            <p className="text-slate-400 text-sm mt-1">
              Network-to-blockchain correlation: IP → Transaction → Wallet.
            </p>
          </div>

          <span className="text-xs border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 rounded-full px-3 py-1">
            SIH • OFFLINE
          </span>
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-6">
        <h2 className="text-sm font-semibold mb-4">
          Transaction Investigation
        </h2>

        <div className="flex flex-col md:flex-row gap-3">
          <input
            value={txid}
            onChange={(e) => setTxid(e.target.value)}
            placeholder="Enter SIH transaction ID"
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-sky-500"
          />

          <button
            onClick={handleGraph}
            disabled={loading || !txid.trim()}
            className="bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-slate-950 font-semibold px-5 py-2 rounded-lg text-sm"
          >
            {loading ? 'Loading Graph...' : 'Build Graph'}
          </button>
        </div>

        <p className="text-xs text-slate-500 mt-3">
          Source: SIH synthetic transaction/network dataset
        </p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/40 text-red-300 rounded-lg px-4 py-3 text-sm mb-6">
          {error}
        </div>
      )}

      {result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <p className="text-xs text-slate-500">Graph Nodes</p>
              <p className="text-2xl font-bold text-sky-400 mt-2">
                {result.nodes?.length || 0}
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <p className="text-xs text-slate-500">Connections</p>
              <p className="text-2xl font-bold text-violet-400 mt-2">
                {result.edges?.length || 0}
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <p className="text-xs text-slate-500">Network IPs</p>
              <p className="text-2xl font-bold text-sky-400 mt-2">
                {ipNodes.length}
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <p className="text-xs text-slate-500">Wallets</p>
              <p className="text-2xl font-bold text-emerald-400 mt-2">
                {walletNodes.length}
              </p>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-sm font-semibold">
                  Network ↔ Blockchain Correlation
                </h2>

                <p className="text-xs text-slate-500 mt-1">
                  Entity relationship generated by NetworkX.
                </p>
              </div>

              <span className="text-xs text-slate-500">
                {result.transaction_id}
              </span>
            </div>

            <div className="flex flex-col items-center">
              {ipNodes.map((node) => (
                <div key={node.id} className="flex flex-col items-center">
                  <NodeCard node={node} />

                  {observationEdges.map((edge, index) => (
                    <EdgeDetails
                      key={`${edge.key || index}`}
                      edge={edge}
                    />
                  ))}
                </div>
              ))}

              {transactionNodes.map((node) => (
                <div
                  key={node.id}
                  className="flex flex-col items-center"
                >
                  <NodeCard node={node} />

                  {associationEdges.map((edge, index) => (
                    <EdgeDetails
                      key={`${edge.key || index}`}
                      edge={edge}
                    />
                  ))}
                </div>
              ))}

              {walletNodes.map((node) => (
                <NodeCard key={node.id} node={node} />
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold mb-4">
                Network Observations
              </h2>

              <div className="space-y-3">
                {observationEdges.map((edge, index) => (
                  <div
                    key={edge.key || index}
                    className="bg-slate-800 rounded-lg p-4"
                  >
                    <div className="text-xs text-sky-300 font-semibold mb-2">
                      IP → Transaction
                    </div>

                    <div className="text-xs font-mono text-slate-300 break-all">
                      {edge.source}
                    </div>

                    <div className="text-xs text-slate-500 my-1">
                      OBSERVED
                    </div>

                    <div className="text-xs font-mono text-violet-300 break-all">
                      {edge.target}
                    </div>

                    <div className="flex flex-wrap gap-2 mt-3">
                      <span className="text-[11px] bg-slate-900 rounded px-2 py-1 text-sky-300">
                        Port: {edge.port_no}
                      </span>

                      <span className="text-[11px] bg-slate-900 rounded px-2 py-1 text-slate-400">
                        {edge.timestamp}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h2 className="text-sm font-semibold mb-4">
                Blockchain Associations
              </h2>

              <div className="space-y-3">
                {associationEdges.map((edge, index) => (
                  <div
                    key={edge.key || index}
                    className="bg-slate-800 rounded-lg p-4"
                  >
                    <div className="text-xs text-emerald-300 font-semibold mb-2">
                      Transaction → Wallet
                    </div>

                    <div className="text-xs font-mono text-violet-300 break-all">
                      {edge.source}
                    </div>

                    <div className="text-xs text-slate-500 my-1">
                      ASSOCIATED
                    </div>

                    <div className="text-xs font-mono text-emerald-300 break-all">
                      {edge.target}
                    </div>

                    <div className="flex flex-wrap gap-2 mt-3">
                      <span className="text-[11px] bg-slate-900 rounded px-2 py-1 text-emerald-300">
                        BTC: {edge.bitcoin_transferred}
                      </span>

                      <span className="text-[11px] bg-slate-900 rounded px-2 py-1 text-slate-400">
                        {edge.timestamp}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
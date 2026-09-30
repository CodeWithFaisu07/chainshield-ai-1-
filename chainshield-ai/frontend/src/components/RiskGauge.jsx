export default function RiskGauge({ score }) {
  const pct = Math.min(Math.max(score, 0), 100)
  const color =
    pct >= 70 ? '#f87171' : pct >= 40 ? '#fbbf24' : '#4ade80'
  const label = pct >= 70 ? 'HIGH RISK' : pct >= 40 ? 'MEDIUM RISK' : 'LOW RISK'

  const gaugeStyle = {
    width: 160,
    height: 160,
    background: 'conic-gradient(' + color + ' ' + (pct * 3.6) + 'deg, #1e293b 0deg)',
  }

  return (
    <div className="flex flex-col items-center justify-center py-6">
      <div className="relative flex items-center justify-center rounded-full" style={gaugeStyle}>
        <div className="flex flex-col items-center justify-center bg-slate-950 rounded-full w-32 h-32">
          <span className="text-3xl font-bold text-slate-100">{pct.toFixed(1)}</span>
          <span className="text-xs text-slate-400">/ 100</span>
        </div>
      </div>
      <span className="mt-3 text-sm font-semibold tracking-wide" style={{ color: color }}>
        {label}
      </span>
    </div>
  )
}
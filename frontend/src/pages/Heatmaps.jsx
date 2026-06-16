import { useState, useEffect } from 'react'

export default function Heatmaps() {
  const [heatmapData, setHeatmapData] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchHeatmapData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('http://localhost:8000/heatmaps')
      if (!response.ok) {
        throw new Error('Heatmap constituent matrix is currently unavailable - live broker connection required.')
      }
      const data = await response.json()
      setHeatmapData(data)
    } catch (err) {
      setError(err.message || 'Failed to fetch heatmap data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHeatmapData()
  }, [])

  const getHeatmapColor = (chg) => {
    if (chg >= 2.0) return 'bg-emerald-600 text-zinc-950 font-extrabold shadow-inner shadow-emerald-400/30'
    if (chg >= 0.7) return 'bg-emerald-800 text-emerald-100 font-bold'
    if (chg >= 0.1) return 'bg-emerald-950/80 text-emerald-300'
    if (chg <= -2.0) return 'bg-rose-600 text-zinc-950 font-extrabold shadow-inner shadow-rose-400/30'
    if (chg <= -0.7) return 'bg-rose-800 text-rose-100 font-bold'
    if (chg <= -0.1) return 'bg-rose-950/80 text-rose-300'
    return 'bg-zinc-900 text-zinc-400 border border-border-hairline/50'
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-cyan/25 border-t-cyan rounded-full animate-spin"></div>
        <p className="text-sm font-mono text-text-muted">Loading stock heatmap dashboard...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between space-y-4 xl:space-y-0 pb-2 border-b border-border-hairline">
          <div>
            <h1 className="text-xl font-bold font-sans text-text-heading tracking-tight flex items-center">
              <span>Market Heatmap Matrix</span>
              <span className="ml-2 px-1.5 py-0.5 text-[9px] font-semibold font-mono bg-cyan/10 text-cyan rounded border border-cyan/20 uppercase tracking-widest">
                Visual Grid
              </span>
            </h1>
            <p className="text-xs text-text-muted mt-0.5">
              Treemap-style sector heatmap representing performance of major index components.
            </p>
          </div>
        </div>

        <div className="bg-canvas-soft border border-error/20 rounded-lg p-8 text-center max-w-md mx-auto my-12 space-y-4 shadow-lg">
          <svg className="w-12 h-12 text-error mx-auto animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h3 className="text-base font-bold text-text-heading font-sans">Heatmap Engine Error</h3>
          <p className="text-xs text-text-body font-mono">{error}</p>
          <button onClick={fetchHeatmapData} className="px-4 py-2 bg-primary text-on-primary rounded text-xs hover:opacity-90 font-medium font-sans">
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between space-y-4 xl:space-y-0 pb-2 border-b border-border-hairline">
        <div>
          <h1 className="text-xl font-bold font-sans text-text-heading tracking-tight flex items-center">
            <span>Market Heatmap Matrix</span>
            <span className="ml-2 px-1.5 py-0.5 text-[9px] font-semibold font-mono bg-cyan/10 text-cyan rounded border border-cyan/20 uppercase tracking-widest">
              Visual Grid
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Treemap-style sector heatmap representing performance of major index components.
          </p>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(heatmapData).map(([sector, stocks]) => (
          <div key={sector} className="bg-canvas-soft border border-border-hairline rounded-lg p-5 shadow-lg space-y-4 flex flex-col justify-between">
            <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">{sector}</span>
            
            <div className="grid grid-cols-2 gap-3 flex-1 pt-2">
              {stocks.map((stk) => {
                const colorClass = getHeatmapColor(stk.change)
                return (
                  <div
                    key={stk.symbol}
                    className={`p-4 rounded-lg flex flex-col justify-between items-center text-center transition-all duration-300 hover:scale-[1.03] cursor-pointer shadow ${colorClass}`}
                    title={`${stk.symbol}: Rs. ${stk.price} (${stk.change >= 0 ? '+' : ''}${stk.change}%)`}
                  >
                    <div className="text-xs font-bold font-mono tracking-wide">{stk.symbol}</div>
                    <div className="text-[10px] font-mono mt-1 font-semibold">
                      {stk.change >= 0 ? '+' : ''}{stk.change.toFixed(2)}%
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

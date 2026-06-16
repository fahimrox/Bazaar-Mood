import { useState, useEffect } from 'react'

export default function SectorAnalytics() {
  const [sectors, setSectors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchSectorStrength = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('http://localhost:8000/sector-strength')
      if (!response.ok) {
        throw new Error(`Sector engine API failed: ${response.statusText}`)
      }
      const data = await response.json()
      // Sort sectors by percentage change
      setSectors(data.sort((a, b) => b.pct - a.pct))
    } catch (err) {
      setError(err.message || 'Failed to fetch sector rotation data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSectorStrength()
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-cyan/25 border-t-cyan rounded-full animate-spin"></div>
        <p className="text-sm font-mono text-text-muted">Loading sector rotation matrix...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-canvas-soft border border-error/20 rounded-lg p-8 text-center max-w-md mx-auto my-12 space-y-4 shadow-lg">
        <svg className="w-12 h-12 text-error mx-auto animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-base font-bold text-text-heading">Sector Analysis Error</h3>
        <p className="text-xs text-text-body">{error}</p>
        <button onClick={fetchSectorStrength} className="px-4 py-2 bg-primary text-on-primary rounded text-xs hover:opacity-90 font-medium">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between space-y-4 xl:space-y-0 pb-2 border-b border-border-hairline">
        <div>
          <h1 className="text-xl font-bold font-sans text-text-heading tracking-tight flex items-center">
            <span>Sector Rotation & Strength Grid</span>
            <span className="ml-2 px-1.5 py-0.5 text-[9px] font-semibold font-mono bg-violet/10 text-violet rounded border border-violet/20 uppercase tracking-widest">
              Market Weights
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Compare performance of major Indian stock market sectors in real-time.
          </p>
        </div>

        <button
          onClick={fetchSectorStrength}
          className="px-3 py-1.5 bg-canvas-soft-2 border border-border-hairline hover:bg-border-hairline/25 rounded-md text-xs font-mono font-semibold transition-all"
        >
          Refresh Feed
        </button>
      </div>

      {/* Bar Chart comparing sectors */}
      <div className="bg-canvas border border-border-hairline rounded-lg p-5 shadow-lg space-y-4">
        <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Relative Strength (Daily Performance %)</span>
        <div className="space-y-3 pt-2">
          {sectors.map((sec) => {
            const isPos = sec.pct >= 0
            const absPct = Math.abs(sec.pct)
            // Cap visual percentage width for clean UI layout
            const widthPct = Math.min(100, (absPct / 3) * 100)
            
            return (
              <div key={sec.sector} className="flex items-center space-x-4 text-xs font-mono">
                <span className="w-24 text-text-heading font-sans font-bold truncate">{sec.sector.replace('NIFTY ', '')}</span>
                <div className="flex-1 flex items-center relative h-6 bg-canvas-soft-2 rounded overflow-hidden px-1">
                  <div 
                    className={`h-4 rounded ${isPos ? 'bg-success/80' : 'bg-error/80'} absolute transition-all duration-500`}
                    style={{ 
                      width: `${widthPct}%`, 
                      left: isPos ? '50%' : 'auto',
                      right: !isPos ? '50%' : 'auto' 
                    }}
                  ></div>
                  <div className="absolute left-[50%] top-0 bottom-0 w-[1px] bg-border-hairline z-10"></div>
                </div>
                <span className={`w-14 text-right font-bold ${isPos ? 'text-success' : 'text-error'}`}>
                  {isPos ? '+' : ''}{sec.pct.toFixed(2)}%
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Grid of detailed Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sectors.map((sec) => {
          const isUp = sec.change >= 0
          return (
            <div key={sec.sector} className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col justify-between h-40 shadow-lg">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  <span>{sec.ticker}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${
                    sec.strength === 'Outperforming' ? 'bg-success/15 text-success' :
                    sec.strength === 'Strong' ? 'bg-success/10 text-success' :
                    sec.strength === 'Underperforming' ? 'bg-error/15 text-error' :
                    sec.strength === 'Weak' ? 'bg-error/10 text-error' : 'bg-canvas-soft-2 text-text-body'
                  }`}>{sec.strength}</span>
                </div>
                <h3 className="text-sm font-bold text-text-heading font-sans mt-3">{sec.sector}</h3>
              </div>

              <div className="flex justify-between items-baseline pt-4 border-t border-border-hairline">
                <span className="text-lg font-bold font-mono text-text-heading">
                  {sec.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
                <span className={`text-xs font-semibold font-mono ${isUp ? 'text-success' : 'text-error'}`}>
                  {isUp ? '+' : ''}{sec.pct.toFixed(2)}%
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

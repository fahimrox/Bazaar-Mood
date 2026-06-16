import { useState, useEffect } from 'react'

export default function Screeners() {
  const [activeScreener, setActiveScreener] = useState('VOLUME_SHOCKERS')
  const [screenerData, setScreenerData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const screeners = [
    { id: 'VOLUME_SHOCKERS', name: 'Volume Shockers', desc: 'Stocks with daily volume > 200% of 10-day average.' },
    { id: 'RSI_OVERSOLD', name: 'RSI Oversold', desc: 'Stocks with 14-period RSI below 30 (Potential Reversal).' },
    { id: 'RSI_OVERBOUGHT', name: 'RSI Overbought', desc: 'Stocks with 14-period RSI above 70 (Overextended).' },
    { id: 'OI_SPIKE', name: 'OI Spikers', desc: 'High Open Interest change coupled with price momentum.' }
  ]

  const fetchScreenerData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`http://localhost:8000/screeners?symbol=${activeScreener}`)
      if (!response.ok) {
        throw new Error('Screener metrics feed is currently unavailable - live broker connection required.')
      }
      const data = await response.json()
      setScreenerData(data)
    } catch (err) {
      setError(err.message || 'Failed to fetch screener metrics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchScreenerData()
  }, [activeScreener])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-cyan/25 border-t-cyan rounded-full animate-spin"></div>
        <p className="text-sm font-mono text-text-muted">Loading technical screeners...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between space-y-4 xl:space-y-0 pb-2 border-b border-border-hairline">
          <div>
            <h1 className="text-xl font-bold font-sans text-text-heading tracking-tight flex items-center">
              <span>Market Screeners & Scanners</span>
              <span className="ml-2 px-1.5 py-0.5 text-[9px] font-semibold font-mono bg-cyan/10 text-cyan rounded border border-cyan/20 uppercase tracking-widest">
                Live Technicals
              </span>
            </h1>
            <p className="text-xs text-text-muted mt-0.5">
              Identify momentum stock set ups using technical and derivatives filters.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {screeners.map((scr) => (
            <button
              key={scr.id}
              onClick={() => setActiveScreener(scr.id)}
              className={`text-left p-4 rounded-lg border transition-all duration-200 ${
                activeScreener === scr.id
                  ? 'bg-canvas-soft border-cyan shadow-md'
                  : 'bg-canvas border-border-hairline hover:border-text-body/30'
              }`}
            >
              <h3 className={`text-xs font-bold font-sans ${activeScreener === scr.id ? 'text-cyan' : 'text-text-heading'}`}>
                {scr.name}
              </h3>
              <p className="text-[10px] text-text-muted mt-1 leading-relaxed">{scr.desc}</p>
            </button>
          ))}
        </div>

        <div className="bg-canvas-soft border border-error/20 rounded-lg p-8 text-center max-w-md mx-auto my-12 space-y-4 shadow-lg">
          <svg className="w-12 h-12 text-error mx-auto animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h3 className="text-base font-bold text-text-heading font-sans">Screener Engine Error</h3>
          <p className="text-xs text-text-body font-mono">{error}</p>
          <button onClick={fetchScreenerData} className="px-4 py-2 bg-primary text-on-primary rounded text-xs hover:opacity-90 font-medium font-sans">
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
            <span>Market Screeners & Scanners</span>
            <span className="ml-2 px-1.5 py-0.5 text-[9px] font-semibold font-mono bg-cyan/10 text-cyan rounded border border-cyan/20 uppercase tracking-widest">
              Live Technicals
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Identify momentum stock set ups using technical and derivatives filters.
          </p>
        </div>
      </div>

      {/* Screeners Tabs Selector */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {screeners.map((scr) => (
          <button
            key={scr.id}
            onClick={() => setActiveScreener(scr.id)}
            className={`text-left p-4 rounded-lg border transition-all duration-200 ${
              activeScreener === scr.id
                ? 'bg-canvas-soft border-cyan shadow-md'
                : 'bg-canvas border-border-hairline hover:border-text-body/30'
            }`}
          >
            <h3 className={`text-xs font-bold font-sans ${activeScreener === scr.id ? 'text-cyan' : 'text-text-heading'}`}>
              {scr.name}
            </h3>
            <p className="text-[10px] text-text-muted mt-1 leading-relaxed">{scr.desc}</p>
          </button>
        ))}
      </div>

      {/* Screener Results */}
      <div className="bg-canvas border border-border-hairline rounded-lg shadow-xl overflow-hidden">
        <table className="w-full text-left border-collapse select-none">
          <thead>
            <tr className="bg-canvas-soft border-b border-border-hairline text-[10px] font-mono uppercase text-text-muted">
              <th className="py-3 px-5">Symbol</th>
              <th className="py-3 px-5">LTP (Rs.)</th>
              <th className="py-3 px-5">Price Change</th>
              <th className="py-3 px-5">{screeners.find(s => s.id === activeScreener).name} Metric</th>
              <th className="py-3 px-5">Description / Technical Note</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-hairline font-mono text-xs text-text-body">
            {screenerData.map((row) => (
              <tr key={row.symbol} className="hover:bg-canvas-soft-2/40">
                <td className="py-3.5 px-5 font-sans font-bold text-text-heading">{row.symbol}</td>
                <td className="py-3.5 px-5 font-semibold">{row.price.toLocaleString('en-IN', { minimumFractionDigits: 1 })}</td>
                <td className={`py-3.5 px-5 font-bold ${row.change >= 0 ? 'text-success' : 'text-error'}`}>
                  {row.change >= 0 ? '+' : ''}{row.change.toFixed(2)}%
                </td>
                <td className="py-3.5 px-5">
                  <span className="px-2 py-0.5 bg-cyan/15 text-cyan rounded text-[10px] font-bold">
                    {row.metricVal}
                  </span>
                </td>
                <td className="py-3.5 px-5 text-text-muted font-sans italic">{row.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'

export default function FOAnalytics() {
  const [activeFilter, setActiveFilter] = useState('ALL')
  const [stocks, setStocks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchFOData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('http://localhost:8000/oi-activity')
      if (!response.ok) {
        throw new Error('F&O derivatives buildup feed is currently unavailable - live broker feed required.')
      }
      const data = await response.json()
      setStocks(data || [])
    } catch (err) {
      setError(err.message || 'Failed to fetch F&O buildup details')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFOData()
  }, [])

  const filteredStocks = (stocks || []).filter(stock => {
    if (!stock) return false
    if (activeFilter === 'ALL') return true
    if (activeFilter === 'BULLISH') return stock.tone === 'bullish'
    if (activeFilter === 'BEARISH') return stock.tone === 'bearish'
    if (activeFilter === 'LONG_BUILDUP') return stock.type === 'Long Buildup'
    if (activeFilter === 'SHORT_BUILDUP') return stock.type === 'Short Buildup'
    return true
  })

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-cyan/25 border-t-cyan rounded-full animate-spin"></div>
        <p className="text-sm font-mono text-text-muted">Loading F&O analytics board...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-canvas-soft border border-error/20 rounded-lg p-8 text-center max-w-md mx-auto my-12 space-y-4 shadow-lg">
        <svg className="w-12 h-12 text-error mx-auto animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-base font-bold text-text-heading">F&O Derivatives Engine Error</h3>
        <p className="text-xs text-text-body">{error}</p>
        <button onClick={fetchFOData} className="px-4 py-2 bg-primary text-on-primary rounded text-xs hover:opacity-90 font-medium">
          Retry Connection
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
            <span>F&O Derivatives Dashboard</span>
            <span className="ml-2 px-1.5 py-0.5 text-[9px] font-semibold font-mono bg-success/10 text-success rounded border border-success/20 uppercase tracking-widest">
              Live Scan
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Buildup analysis of option chain strikes using price-action and open interest changes.
          </p>
        </div>

        {/* Filter controls */}
        <div className="flex flex-wrap gap-1 bg-canvas-soft-2 p-1 rounded-lg border border-border-hairline self-start">
          {[
            { label: 'All Contracts', value: 'ALL' },
            { label: 'Bullish Tone', value: 'BULLISH' },
            { label: 'Bearish Tone', value: 'BEARISH' },
            { label: 'Long Buildup', value: 'LONG_BUILDUP' },
            { label: 'Short Buildup', value: 'SHORT_BUILDUP' }
          ].map(btn => (
            <button
              key={btn.value}
              onClick={() => setActiveFilter(btn.value)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold font-mono transition-all duration-200 ${
                activeFilter === btn.value
                  ? 'bg-canvas text-text-heading shadow-md border border-border-hairline'
                  : 'text-text-body hover:text-text-heading hover:bg-canvas-soft/40'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>

      {/* Stocks Table */}
      <div className="bg-canvas border border-border-hairline rounded-lg shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse select-none">
            <thead>
              <tr className="bg-canvas-soft border-b border-border-hairline text-[10px] font-mono uppercase text-text-muted">
                <th className="py-3 px-5">Option Contract / Strike</th>
                <th className="py-3 px-5">OI Change</th>
                <th className="py-3 px-5">Market Tone</th>
                <th className="py-3 px-5">Derivative Buildup</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-hairline font-mono text-xs text-text-body">
              {filteredStocks.map((stock, idx) => (
                <tr key={stock?.strike || idx} className="hover:bg-canvas-soft-2/40">
                  <td className="py-3.5 px-5 font-sans font-bold text-text-heading">{stock?.strike || 'N/A'}</td>
                  <td className={`py-3.5 px-5 font-semibold ${stock?.tone === 'bullish' ? 'text-success' : 'text-error'}`}>
                    {stock?.oiChange || 'N/A'}
                  </td>
                  <td className="py-3.5 px-5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-bold uppercase ${
                      stock?.tone === 'bullish' ? 'bg-success/15 text-success' : 'bg-error/15 text-error'
                    }`}>
                      {stock?.tone || 'N/A'}
                    </span>
                  </td>
                  <td className="py-3.5 px-5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-bold tracking-wide ${
                      stock?.type === 'Long Buildup' ? 'bg-success/15 text-success' :
                      stock?.type === 'Short Covering' ? 'bg-cyan/15 text-cyan' :
                      stock?.type === 'Short Buildup' ? 'bg-error/15 text-error' : 'bg-warning/15 text-warning'
                    }`}>
                      {stock?.type || 'N/A'}
                    </span>
                  </td>
                </tr>
              ))}
              {filteredStocks.length === 0 && (
                <tr>
                  <td colSpan="4" className="py-8 text-center text-text-muted italic">
                    No buildup contracts match the selected filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}


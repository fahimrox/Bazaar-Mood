import { useState, useEffect } from 'react'

export default function OptionsAnalytics() {
  const [activeTab, setActiveTab] = useState('NIFTY')
  const [expiry, setExpiry] = useState('weekly')
  const indexTabs = ['NIFTY', 'BANKNIFTY', 'MIDCPNIFTY', 'SENSEX']
  
  const [optionChain, setOptionChain] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchOptionChain = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`http://localhost:8000/option-chain?symbol=${activeTab}&expiry=${expiry}`)
      if (!response.ok) {
        throw new Error(`Options engine request failed: ${response.statusText}`)
      }
      const data = await response.json()
      setOptionChain(data)
    } catch (err) {
      setError(err.message || 'Failed to fetch options chain data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOptionChain()
  }, [activeTab, expiry])

  if (loading && !optionChain) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-cyan/25 border-t-cyan rounded-full animate-spin"></div>
        <p className="text-sm font-mono text-text-muted">Loading options chain details...</p>
      </div>
    )
  }

  if (error && !optionChain) {
    return (
      <div className="bg-canvas-soft border border-error/20 rounded-lg p-8 text-center max-w-md mx-auto my-12 space-y-4 shadow-lg">
        <svg className="w-12 h-12 text-error mx-auto animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-base font-bold text-text-heading">Option Chain Engine Error</h3>
        <p className="text-xs text-text-body">{error}</p>
        <button onClick={fetchOptionChain} className="px-4 py-2 bg-primary text-on-primary rounded text-xs hover:opacity-90 font-medium">
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
            <span>Derivatives & Options Analytics</span>
            <span className="ml-2 px-1.5 py-0.5 text-[9px] font-semibold font-mono bg-cyan/10 text-cyan rounded border border-cyan/20 uppercase tracking-widest">
              Greeks Enabled
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Real-time Black-Scholes Greeks pricing, PCR, and option chain build-ups.
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Index switcher */}
          <div className="flex gap-1 bg-canvas-soft-2 p-1 rounded-lg border border-border-hairline">
            {indexTabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold font-mono transition-all duration-200 ${
                  activeTab === tab
                    ? 'bg-canvas text-text-heading shadow-md border border-border-hairline'
                    : 'text-text-body hover:text-text-heading hover:bg-canvas-soft/40'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {/* Expiry filter */}
          <div className="flex gap-1 bg-canvas-soft-2 p-1 rounded-lg border border-border-hairline">
            {['weekly', 'monthly'].map(exp => (
              <button
                key={exp}
                onClick={() => setExpiry(exp)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold font-mono transition-all duration-200 capitalize ${
                  expiry === exp
                    ? 'bg-canvas text-text-heading shadow-md border border-border-hairline'
                    : 'text-text-body hover:text-text-heading hover:bg-canvas-soft/40'
                }`}
              >
                {exp}
              </button>
            ))}
          </div>
        </div>
      </div>

      {optionChain && (
        <>
          {/* Top Cards: Summary Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Spot Price */}
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 shadow flex justify-between items-center">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Spot Price</span>
                <div className="text-xl font-bold font-mono text-text-heading mt-1">
                  {optionChain.spot.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>
              <span className="text-2xl">🎯</span>
            </div>

            {/* PCR */}
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 shadow flex justify-between items-center">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Put-Call Ratio (PCR)</span>
                <div className="text-xl font-bold font-mono text-text-heading mt-1 flex items-baseline space-x-2">
                  <span>{optionChain.pcr}</span>
                  <span className={`text-[10px] font-sans font-semibold px-1.5 py-0.5 rounded ${
                    optionChain.pcr > 1.25 ? 'bg-success/15 text-success' :
                    optionChain.pcr < 0.85 ? 'bg-error/15 text-error' : 'bg-canvas-soft-2 text-text-muted'
                  }`}>
                    {optionChain.pcr > 1.25 ? 'Oversold (Bullish)' : optionChain.pcr < 0.85 ? 'Overbought (Bearish)' : 'Neutral'}
                  </span>
                </div>
              </div>
              <span className="text-2xl">📊</span>
            </div>

            {/* Max Pain */}
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 shadow flex justify-between items-center">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Max Pain Strike</span>
                <div className="text-xl font-bold font-mono text-text-heading mt-1">
                  {optionChain.maxPain.toLocaleString('en-IN')}
                </div>
              </div>
              <span className="text-2xl">⚡</span>
            </div>
          </div>

          {/* Option Chain Grid */}
          <div className="bg-canvas border border-border-hairline rounded-lg shadow-xl overflow-hidden">
            <div className="p-4 bg-canvas-soft border-b border-border-hairline flex justify-between items-center text-xs font-mono">
              <span className="text-text-heading font-semibold">Option Chain - {optionChain.symbol} Expiry (Weekly/Monthly)</span>
              <span className="text-text-muted">IV: ~{(optionChain.spot * 0.0006).toFixed(1)}% | Calls on Left | Puts on Right</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-center border-collapse select-none">
                <thead>
                  <tr className="bg-canvas-soft-2 border-b border-border-hairline text-[10px] font-mono uppercase text-text-muted">
                    {/* Calls Header */}
                    <th className="py-2.5 px-2">OI (Lakhs)</th>
                    <th className="py-2.5 px-2">OI Chg (%)</th>
                    <th className="py-2.5 px-2">Vol</th>
                    <th className="py-2.5 px-2">Delta</th>
                    <th className="py-2.5 px-2 border-r border-border-hairline">LTP</th>
                    
                    {/* Strike */}
                    <th className="py-2.5 px-3 font-bold bg-canvas text-text-heading border-r border-border-hairline">Strike</th>
                    
                    {/* Puts Header */}
                    <th className="py-2.5 px-2">LTP</th>
                    <th className="py-2.5 px-2">Delta</th>
                    <th className="py-2.5 px-2">Vol</th>
                    <th className="py-2.5 px-2">OI Chg (%)</th>
                    <th className="py-2.5 px-2">OI (Lakhs)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-hairline font-mono text-[11px] text-text-body">
                  {optionChain.chain.map((row) => {
                    const isCallItm = optionChain.spot > row.strike
                    const isPutItm = optionChain.spot < row.strike
                    const isAtm = row.is_atm
                    
                    return (
                      <tr key={row.strike} className={`hover:bg-canvas-soft-2/50 ${isAtm ? 'bg-cyan/5 font-semibold text-text-heading' : ''}`}>
                        {/* Call OI columns */}
                        <td className={`py-2 px-2 ${isCallItm ? 'bg-success/5' : ''}`}>
                          {roundLakhs(row.call.oi)}
                        </td>
                        <td className={`py-2 px-2 ${isCallItm ? 'bg-success/5' : ''} ${row.call.oiChange >= 0 ? 'text-success' : 'text-error'}`}>
                          {row.call.oiChange >= 0 ? '+' : ''}{(row.call.oiChange / row.call.oi * 100).toFixed(1)}%
                        </td>
                        <td className={`py-2 px-2 text-text-muted ${isCallItm ? 'bg-success/5' : ''}`}>
                          {row.call.volume.toLocaleString()}
                        </td>
                        <td className={`py-2 px-2 text-text-muted ${isCallItm ? 'bg-success/5' : ''}`}>
                          {row.call.delta.toFixed(2)}
                        </td>
                        <td className={`py-2 px-2 font-bold text-text-heading border-r border-border-hairline ${isCallItm ? 'bg-success/10 text-success' : ''}`}>
                          {row.call.price.toFixed(2)}
                        </td>
                        
                        {/* Strike Center */}
                        <td className={`py-2 px-3 font-bold bg-canvas-soft text-text-heading border-r border-border-hairline ${isAtm ? 'border-x-2 border-cyan/30 text-cyan' : ''}`}>
                          {row.strike}
                        </td>
                        
                        {/* Put OI columns */}
                        <td className={`py-2 px-2 font-bold text-text-heading ${isPutItm ? 'bg-error/10 text-error' : ''}`}>
                          {row.put.price.toFixed(2)}
                        </td>
                        <td className={`py-2 px-2 text-text-muted ${isPutItm ? 'bg-error/5' : ''}`}>
                          {row.put.delta.toFixed(2)}
                        </td>
                        <td className={`py-2 px-2 text-text-muted ${isPutItm ? 'bg-error/5' : ''}`}>
                          {row.put.volume.toLocaleString()}
                        </td>
                        <td className={`py-2 px-2 ${isPutItm ? 'bg-error/5' : ''} ${row.put.oiChange >= 0 ? 'text-success' : 'text-error'}`}>
                          {row.put.oiChange >= 0 ? '+' : ''}{(row.put.oiChange / row.put.oi * 100).toFixed(1)}%
                        </td>
                        <td className={`py-2 px-2 ${isPutItm ? 'bg-error/5' : ''}`}>
                          {roundLakhs(row.put.oi)}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function roundLakhs(val) {
  const lakhs = val / 100000
  return `${lakhs.toFixed(2)}L`
}

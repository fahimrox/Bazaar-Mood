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
    setOptionChain(null) // Trigger skeleton loaders during state changes
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
    return <OptionsPageSkeleton />
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

  // Market Bias Style Helpers
  const biasColors = {
    Bullish: 'bg-success/10 text-success border border-success/20',
    Bearish: 'bg-error/10 text-error border border-error/20',
    Neutral: 'bg-warning/10 text-warning border border-warning/20',
  }
  const biasColorClass = optionChain ? (biasColors[optionChain?.market_bias] || 'bg-canvas-soft-2 text-text-muted border border-border-hairline') : ''

  // Trade Signal Style Helpers
  const signalColors = {
    'BUY CE': 'bg-success/15 text-success border border-success/30 font-bold',
    'BUY PE': 'bg-error/15 text-error border border-error/30 font-bold',
    'NO TRADE': 'bg-canvas-soft-2 text-text-muted border border-border-hairline font-semibold',
  }
  const signalColorClass = optionChain ? (signalColors[optionChain?.trade_signal] || 'bg-canvas-soft-2 text-text-muted border border-border-hairline') : ''

  // Format trade parameters safely
  const entryVal = optionChain && optionChain?.entry > 0 ? optionChain.entry.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : 'N/A'
  const slVal = optionChain && optionChain?.stop_loss > 0 ? optionChain.stop_loss.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : 'N/A'
  const tgtVal = optionChain && optionChain?.target > 0 ? optionChain.target.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : 'N/A'

  // Calculate Risk-to-Reward Ratio dynamically
  let rrRatio = '0.0'
  if (optionChain) {
    if (optionChain?.trade_signal === 'BUY CE' && optionChain?.entry > 0 && optionChain?.stop_loss > 0 && optionChain?.target > 0) {
      const risk = optionChain.entry - optionChain.stop_loss
      if (risk > 0) {
        rrRatio = ((optionChain.target - optionChain.entry) / risk).toFixed(1)
      }
    } else if (optionChain?.trade_signal === 'BUY PE' && optionChain?.entry > 0 && optionChain?.stop_loss > 0 && optionChain?.target > 0) {
      const risk = optionChain.stop_loss - optionChain.entry
      if (risk > 0) {
        rrRatio = ((optionChain.entry - optionChain.target) / risk).toFixed(1)
      }
    }
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
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 shadow flex justify-between items-center transition-all duration-300 hover:border-border-hairline/50">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Spot Price</span>
                <div className="text-xl font-bold font-mono text-text-heading mt-1">
                  {optionChain?.spot !== undefined ? optionChain.spot.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : 'N/A'}
                </div>
              </div>
              <span className="text-2xl">🎯</span>
            </div>

            {/* PCR */}
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 shadow flex justify-between items-center transition-all duration-300 hover:border-border-hairline/50">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Put-Call Ratio (PCR)</span>
                <div className="text-xl font-bold font-mono text-text-heading mt-1 flex items-baseline space-x-2">
                  <span>{optionChain?.pcr !== undefined ? optionChain.pcr : 'N/A'}</span>
                  <span className={`text-[10px] font-sans font-semibold px-1.5 py-0.5 rounded ${
                    optionChain?.pcr > 1.1 ? 'bg-success/15 text-success' :
                    optionChain?.pcr < 0.9 ? 'bg-error/15 text-error' : 'bg-canvas-soft-2 text-text-muted'
                  }`}>
                    {optionChain?.pcr > 1.1 ? 'Bullish' : optionChain?.pcr < 0.9 ? 'Bearish' : 'Neutral'}
                  </span>
                </div>
              </div>
              <span className="text-2xl">📊</span>
            </div>

            {/* Max Pain */}
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 shadow flex justify-between items-center transition-all duration-300 hover:border-border-hairline/50">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">Max Pain Strike</span>
                <div className="text-xl font-bold font-mono text-text-heading mt-1">
                  {optionChain?.maxPain !== undefined ? optionChain.maxPain.toLocaleString('en-IN') : 'N/A'}
                </div>
              </div>
              <span className="text-2xl">⚡</span>
            </div>
          </div>

          {/* V2 Analytics & Recommendations Dashboard Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Card 1: Option Analytics Profile */}
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-6 shadow-xl relative overflow-hidden transition-all duration-300 hover:border-cyan/30 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-border-hairline">
                  <div>
                    <h3 className="text-sm font-bold text-text-heading font-sans flex items-center">
                      <span className="mr-2">📊</span>
                      <span>Option Analytics Profile</span>
                    </h3>
                    <p className="text-[10px] text-text-muted mt-0.5">Real-time OI and volatility characteristics</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono uppercase ${biasColorClass}`}>
                    {optionChain?.market_bias || 'Neutral'} Bias
                  </span>
                </div>

                {/* Conviction Bar */}
                <div className="mt-4 pb-4 border-b border-border-hairline">
                  <div className="flex justify-between items-center text-[10px] mb-1 font-mono">
                    <span className="text-text-muted uppercase tracking-wider">Market Conviction</span>
                    <span className="font-bold text-text-heading">{(optionChain?.confidence_score || 0).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-canvas-soft-2 h-2 rounded overflow-hidden">
                    <div 
                      className="bg-gradient-to-r from-violet via-accent to-cyan h-full rounded transition-all duration-500" 
                      style={{ width: `${optionChain?.confidence_score || 0}%` }}
                    ></div>
                  </div>
                </div>

                {/* Sub-grid of details */}
                <div className="grid grid-cols-2 gap-x-6 gap-y-4 mt-4 text-[11px] font-mono">
                  {/* Left Column */}
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-text-muted">PCR:</span>
                      <span className="text-text-heading font-semibold">{optionChain?.pcr !== undefined ? optionChain.pcr : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Max Pain:</span>
                      <span className="text-text-heading font-semibold">{optionChain?.maxPain !== undefined ? optionChain.maxPain.toLocaleString('en-IN') : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">ATM Strike:</span>
                      <span className="text-text-heading font-semibold text-cyan">{optionChain?.atm_strike !== undefined ? optionChain.atm_strike.toLocaleString('en-IN') : 'N/A'}</span>
                    </div>
                  </div>

                  {/* Right Column */}
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-text-muted">Support (S1):</span>
                      <span className="text-text-heading font-semibold">
                        {optionChain?.support_1 !== undefined ? optionChain.support_1.toLocaleString('en-IN') : 'N/A'}
                        {optionChain?.support_confidence !== undefined && (
                          <span className="text-[9px] text-success ml-1">({optionChain.support_confidence.toFixed(0)}%)</span>
                        )}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Resistance (R1):</span>
                      <span className="text-text-heading font-semibold">
                        {optionChain?.resistance_1 !== undefined ? optionChain.resistance_1.toLocaleString('en-IN') : 'N/A'}
                        {optionChain?.resistance_confidence !== undefined && (
                          <span className="text-[9px] text-error ml-1">({optionChain.resistance_confidence.toFixed(0)}%)</span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Bottom Writing Section */}
                <div className="mt-4 pt-4 border-t border-border-hairline grid grid-cols-2 gap-4 text-[11px] font-mono">
                  <div>
                    <span className="text-[9px] text-text-muted uppercase tracking-wider block">Call Writing (Resistance)</span>
                    <span className={`font-semibold ${optionChain?.call_writing === 'Strong' ? 'text-error' : optionChain?.call_writing === 'Moderate' ? 'text-warning' : 'text-text-muted'}`}>
                      {optionChain?.call_writing || 'N/A'}
                    </span>
                    {optionChain?.call_writing_strike > 0 && (
                      <span className="text-[10px] text-text-heading ml-1.5 font-bold">@ {optionChain.call_writing_strike.toLocaleString('en-IN')}</span>
                    )}
                  </div>
                  <div>
                    <span className="text-[9px] text-text-muted uppercase tracking-wider block">Put Writing (Support)</span>
                    <span className={`font-semibold ${optionChain?.put_writing === 'Strong' ? 'text-success' : optionChain?.put_writing === 'Moderate' ? 'text-warning' : 'text-text-muted'}`}>
                      {optionChain?.put_writing || 'N/A'}
                    </span>
                    {optionChain?.put_writing_strike > 0 && (
                      <span className="text-[10px] text-text-heading ml-1.5 font-bold">@ {optionChain.put_writing_strike.toLocaleString('en-IN')}</span>
                    )}
                  </div>
                </div>

                {/* ATM Greeks Section */}
                <div className="mt-4 pt-4 border-t border-border-hairline">
                  <span className="text-[9px] text-text-muted uppercase tracking-wider block mb-2">ATM Greeks</span>
                  <div className="grid grid-cols-2 gap-4 text-[10px] font-mono">
                    <div className="bg-canvas-soft-2 p-2 rounded border border-border-hairline/50">
                      <div className="text-[8px] text-text-muted uppercase mb-1">Call ATM Greeks</div>
                      <div className="flex justify-between">
                        <span>IV:</span>
                        <span className="font-bold text-text-heading">
                          {optionChain?.atm_greeks?.ce_iv !== undefined ? `${optionChain.atm_greeks.ce_iv}%` : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Delta:</span>
                        <span className="font-bold text-success">
                          {optionChain?.atm_greeks?.ce_delta !== undefined ? optionChain.atm_greeks.ce_delta.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Theta:</span>
                        <span className="font-bold text-error">
                          {optionChain?.atm_greeks?.ce_theta !== undefined ? optionChain.atm_greeks.ce_theta.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                    </div>
                    <div className="bg-canvas-soft-2 p-2 rounded border border-border-hairline/50">
                      <div className="text-[8px] text-text-muted uppercase mb-1">Put ATM Greeks</div>
                      <div className="flex justify-between">
                        <span>IV:</span>
                        <span className="font-bold text-text-heading">
                          {optionChain?.atm_greeks?.pe_iv !== undefined ? `${optionChain.atm_greeks.pe_iv}%` : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Delta:</span>
                        <span className="font-bold text-error">
                          {optionChain?.atm_greeks?.pe_delta !== undefined ? optionChain.atm_greeks.pe_delta.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Theta:</span>
                        <span className="font-bold text-error">
                          {optionChain?.atm_greeks?.pe_theta !== undefined ? optionChain.atm_greeks.pe_theta.toFixed(2) : 'N/A'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>

            {/* Card 2: AI Trade Recommendation */}
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-6 shadow-xl relative overflow-hidden transition-all duration-300 hover:border-accent/30 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-3 border-b border-border-hairline">
                  <div>
                    <h3 className="text-sm font-bold text-text-heading font-sans flex items-center">
                      <span className="mr-2">⚡</span>
                      <span>AI Trade Recommendation</span>
                    </h3>
                    <p className="text-[10px] text-text-muted mt-0.5">Automated signal & risk positioning</p>
                  </div>
                  <span className={`px-2.5 py-0.5 rounded text-[10px] ${signalColorClass}`}>
                    {optionChain?.trade_signal || 'NO TRADE'}
                  </span>
                </div>

                {/* Trade Confidence Bar */}
                <div className="mt-4 pb-4 border-b border-border-hairline">
                  <div className="flex justify-between items-center text-[10px] mb-1 font-mono">
                    <span className="text-text-muted uppercase tracking-wider">Trade Conviction</span>
                    <span className="font-bold text-text-heading">{(optionChain?.trade_confidence || 0).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-canvas-soft-2 h-2 rounded overflow-hidden">
                    <div 
                      className={`h-full rounded transition-all duration-500 ${
                        optionChain?.trade_signal === 'BUY CE' ? 'bg-gradient-to-r from-success/50 to-success' :
                        optionChain?.trade_signal === 'BUY PE' ? 'bg-gradient-to-r from-error/50 to-error' :
                        'bg-text-muted/20'
                      }`}
                      style={{ width: `${optionChain?.trade_confidence || 0}%` }}
                    ></div>
                  </div>
                </div>

                {/* Levels Layout */}
                <div className="grid grid-cols-3 gap-3 mt-4 text-center font-mono">
                  <div className="bg-canvas-soft-2 p-2 rounded border border-border-hairline">
                    <span className="text-[8px] text-text-muted uppercase tracking-wider block mb-1">Entry (ATM)</span>
                    <span className="text-[11px] font-bold text-text-heading">{entryVal}</span>
                  </div>
                  <div className="bg-canvas-soft-2 p-2 rounded border border-border-hairline">
                    <span className="text-[8px] text-text-muted uppercase tracking-wider block mb-1">Stop Loss (SL)</span>
                    <span className="text-[11px] font-bold text-error">{slVal}</span>
                  </div>
                  <div className="bg-canvas-soft-2 p-2 rounded border border-border-hairline">
                    <span className="text-[8px] text-text-muted uppercase tracking-wider block mb-1">Target (Tgt)</span>
                    <span className="text-[11px] font-bold text-success">{tgtVal}</span>
                  </div>
                </div>

                {/* Risk to Reward Ratio */}
                {optionChain?.trade_signal !== 'NO TRADE' && (
                  <div className="mt-3 flex justify-between items-center text-[10px] font-mono px-1">
                    <span className="text-text-muted">Risk-to-Reward Ratio:</span>
                    <span className="font-bold text-cyan">1 : {rrRatio}</span>
                  </div>
                )}

                {/* Rationale List */}
                <div className="mt-4 pt-3 border-t border-border-hairline">
                  <span className="text-[9px] text-text-muted uppercase tracking-wider block mb-2 font-mono">Algorithmic Rationale</span>
                  <ul className="space-y-1.5">
                    {optionChain?.reason && optionChain.reason.length > 0 ? (
                      optionChain.reason.map((reason, idx) => (
                        <li key={idx} className="flex items-start text-[10px] text-text-body font-mono">
                          <span className="text-cyan mr-1.5">✓</span>
                          <span>{reason}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-[10px] text-text-muted italic font-mono">No recommendation reasons generated.</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Option Chain Grid */}
          <div className="bg-canvas border border-border-hairline rounded-lg shadow-xl overflow-hidden">
            <div className="p-4 bg-canvas-soft border-b border-border-hairline flex justify-between items-center text-xs font-mono">
              <span className="text-text-heading font-semibold">Option Chain - {optionChain?.symbol || ''} Expiry ({optionChain?.expiry || ''})</span>
              <span className="text-text-muted">IV: ~{((optionChain?.spot || 0) * 0.0006).toFixed(1)}% | Calls on Left | Puts on Right</span>
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
                  {(optionChain?.chain || []).map((row) => {
                    const isCallItm = (optionChain?.spot || 0) > row.strike
                    const isPutItm = (optionChain?.spot || 0) < row.strike
                    const isAtm = row.is_atm
                    
                    return (
                      <tr key={row.strike} className={`hover:bg-canvas-soft-2/50 ${isAtm ? 'bg-cyan/5 font-semibold text-text-heading' : ''}`}>
                        {/* Call OI columns */}
                        <td className={`py-2 px-2 ${isCallItm ? 'bg-success/5' : ''}`}>
                          {roundLakhs(row.call.oi)}
                        </td>
                        <td className={`py-2 px-2 ${isCallItm ? 'bg-success/5' : ''} ${row.call.oiChange >= 0 ? 'text-success' : 'text-error'}`}>
                          {row.call.oiChange >= 0 ? '+' : ''}{(row.call.oiChange / (row.call.oi || 1) * 100).toFixed(1)}%
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
                          {row.put.oiChange >= 0 ? '+' : ''}{(row.put.oiChange / (row.put.oi || 1) * 100).toFixed(1)}%
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

function OptionsPageSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header Skeleton */}
      <div className="pb-2 border-b border-border-hairline flex flex-col xl:flex-row justify-between space-y-4 xl:space-y-0">
        <div className="space-y-2">
          <div className="h-5 bg-canvas-soft-2 rounded w-64"></div>
          <div className="h-3 bg-canvas-soft-2 rounded w-96"></div>
        </div>
        <div className="h-8 bg-canvas-soft-2 rounded w-48"></div>
      </div>

      {/* Top Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-canvas-soft border border-border-hairline rounded-lg p-5 h-24 flex flex-col justify-between">
            <div className="h-3 bg-canvas-soft-2 rounded w-1/3"></div>
            <div className="h-6 bg-canvas-soft-2 rounded w-2/3"></div>
          </div>
        ))}
      </div>

      {/* Analytics & Recommendation Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Option Analytics Card Skeleton */}
        <div className="bg-canvas-soft border border-border-hairline rounded-lg p-6 h-96 flex flex-col justify-between">
          <div className="space-y-3 pb-3 border-b border-border-hairline">
            <div className="h-4 bg-canvas-soft-2 rounded w-1/2"></div>
            <div className="h-3 bg-canvas-soft-2 rounded w-3/4"></div>
          </div>
          <div className="space-y-4 my-4 flex-1 justify-center flex flex-col">
            <div className="space-y-2">
              <div className="h-3 bg-canvas-soft-2 rounded w-1/4"></div>
              <div className="h-2 bg-canvas-soft-2 rounded w-full"></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="h-10 bg-canvas-soft-2 rounded"></div>
              <div className="h-10 bg-canvas-soft-2 rounded"></div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="h-10 bg-canvas-soft-2 rounded"></div>
              <div className="h-10 bg-canvas-soft-2 rounded"></div>
            </div>
          </div>
          <div className="h-3 bg-canvas-soft-2 rounded w-1/4"></div>
        </div>

        {/* AI Trade Recommendation Card Skeleton */}
        <div className="bg-canvas-soft border border-border-hairline rounded-lg p-6 h-96 flex flex-col justify-between">
          <div className="space-y-3 pb-3 border-b border-border-hairline">
            <div className="h-4 bg-canvas-soft-2 rounded w-1/2"></div>
            <div className="h-3 bg-canvas-soft-2 rounded w-3/4"></div>
          </div>
          <div className="space-y-4 my-4 flex-1 justify-center flex flex-col">
            <div className="space-y-2">
              <div className="h-3 bg-canvas-soft-2 rounded w-1/4"></div>
              <div className="h-2 bg-canvas-soft-2 rounded w-full"></div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="h-10 bg-canvas-soft-2 rounded"></div>
              <div className="h-10 bg-canvas-soft-2 rounded"></div>
              <div className="h-10 bg-canvas-soft-2 rounded"></div>
            </div>
            <div className="space-y-2">
              <div className="h-3 bg-canvas-soft-2 rounded w-full"></div>
              <div className="h-3 bg-canvas-soft-2 rounded w-5/6"></div>
            </div>
          </div>
          <div className="h-3 bg-canvas-soft-2 rounded w-1/4"></div>
        </div>
      </div>

      {/* Table Skeleton */}
      <div className="bg-canvas border border-border-hairline rounded-lg overflow-hidden">
        <div className="p-4 bg-canvas-soft h-12 flex justify-between items-center">
          <div className="h-4 bg-canvas-soft-2 rounded w-48"></div>
          <div className="h-3 bg-canvas-soft-2 rounded w-32"></div>
        </div>
        <div className="p-4 space-y-3">
          <div className="h-6 bg-canvas-soft-2 rounded w-full"></div>
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-8 bg-canvas-soft-2/50 rounded w-full"></div>
          ))}
        </div>
      </div>
    </div>
  )
}


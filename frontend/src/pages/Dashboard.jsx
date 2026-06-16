import { useState, useEffect } from 'react'
import apiService from '../services/api'

// Helper component for loading skeleton
function CardSkeleton() {
  return (
    <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 h-56 shadow-lg animate-pulse flex flex-col justify-between">
      <div className="space-y-3">
        <div className="h-3 bg-canvas-soft-2 rounded w-1/3"></div>
        <div className="h-6 bg-canvas-soft-2 rounded w-1/2"></div>
        <div className="h-4 bg-canvas-soft-2 rounded w-3/4"></div>
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-canvas-soft-2 rounded w-full"></div>
        <div className="h-3 bg-canvas-soft-2 rounded w-5/6"></div>
      </div>
    </div>
  )
}

// Helper component for error state
function CardError({ message, onRetry }) {
  return (
    <div className="bg-canvas-soft border border-error/20 rounded-lg p-5 h-56 shadow-lg flex flex-col justify-between items-center text-center">
      <div className="my-auto space-y-2">
        <svg className="w-8 h-8 text-error mx-auto animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div className="text-xs font-semibold text-text-heading">Load Failed</div>
        <div className="text-[10px] text-error/85 max-w-[220px] mx-auto line-clamp-2 leading-relaxed">{message}</div>
      </div>
      <button
        onClick={onRetry}
        className="px-3 py-1 text-[10px] font-semibold bg-canvas-soft-2 border border-border-hairline rounded text-text-heading hover:bg-border-hairline/20 hover:text-white transition-all"
      >
        Retry
      </button>
    </div>
  )
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('NIFTY')
  const indexTabs = ['NIFTY', 'BANKNIFTY', 'MIDCPNIFTY', 'SENSEX', 'INDIA VIX']

  // Independant card data, loading, and error states
  const [cardData, setCardData] = useState({
    market: null,
    structure: null,
    breadth: null,
    sentiment: null,
    recommendation: null,
    levels: null,
    movers: null,
    oi: null
  })

  const [loading, setLoading] = useState({
    market: true,
    structure: true,
    breadth: true,
    sentiment: true,
    recommendation: true,
    levels: true,
    movers: true,
    oi: true
  })

  const [errors, setErrors] = useState({
    market: null,
    structure: null,
    breadth: null,
    sentiment: null,
    recommendation: null,
    levels: null,
    movers: null,
    oi: null
  })

  // Function to fetch a specific card's data
  const fetchCard = async (key, fetchFn) => {
    setLoading(prev => ({ ...prev, [key]: true }))
    setErrors(prev => ({ ...prev, [key]: null }))
    try {
      const data = await fetchFn(activeTab)
      setCardData(prev => ({ ...prev, [key]: data }))
    } catch (err) {
      setErrors(prev => ({ ...prev, [key]: err.message || 'API request failed' }))
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }))
    }
  }

  // Initial load & activeTab change triggers
  useEffect(() => {
    fetchCard('market', apiService.getMarketOverview)
    fetchCard('structure', apiService.getMarketStructure)
    fetchCard('breadth', apiService.getMarketBreadth)
    fetchCard('sentiment', apiService.getSentiment)
    fetchCard('recommendation', apiService.getRecommendation)
    fetchCard('levels', apiService.getSupportResistance)
    fetchCard('movers', apiService.getTopMovers)
    fetchCard('oi', apiService.getOiActivity)
  }, [activeTab])


  // Render a card with its loading, error, and content layout
  const renderCard = (key, renderContent, fetchFn) => {
    if (loading[key]) return <CardSkeleton />
    if (errors[key]) return <CardError message={errors[key]} onRetry={() => fetchCard(key, fetchFn)} />
    return renderContent(cardData[key])
  }

  return (
    <div className="space-y-6">
      {/* Index Switcher & Header */}
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between space-y-4 xl:space-y-0 pb-2 border-b border-border-hairline">
        <div>
          <h1 className="text-xl font-bold font-sans text-text-heading tracking-tight flex items-center">
            <span>Market Terminal</span>
            <span className="ml-2 px-1.5 py-0.5 text-[9px] font-semibold font-mono bg-success/10 text-success rounded border border-success/20 uppercase tracking-widest">
              Live Feed
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Indian indices intelligence, algorithmic market breadth, and option OI analysis.
          </p>
        </div>

        {/* Index Switcher Tabs */}
        <div className="flex flex-wrap gap-1 bg-canvas-soft-2 p-1 rounded-lg border border-border-hairline self-start">
          {indexTabs.map((tab) => {
            const isTabActive = activeTab === tab
            
            // Get index prices safely for tab labels
            let tabLabelText = '...'
            let isTabUp = true
            if (activeTab === tab && cardData.market) {
              tabLabelText = cardData.market.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })
              isTabUp = cardData.market.change >= 0
            }

            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold font-mono transition-all duration-200 flex items-center space-x-2 ${
                  isTabActive
                    ? 'bg-canvas text-text-heading shadow-md border border-border-hairline'
                    : 'text-text-body hover:text-text-heading hover:bg-canvas-soft/40'
                }`}
              >
                <span>{tab}</span>
                {isTabActive && (
                  <span className={`text-[10px] ${isTabUp ? 'text-success' : 'text-error'}`}>
                    {tabLabelText}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* 9-Grid Dashboard Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Card 1: Index Overview */}
        {renderCard('market', (marketData) => {
          const isUp = marketData.change >= 0
          return (
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col justify-between h-56 shadow-lg">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  <span>Index Overview</span>
                  <span className="text-cyan">Live</span>
                </div>
                <div className="mt-3">
                  <h2 className="text-lg font-bold text-text-heading font-sans">{marketData.name}</h2>
                  <div className="text-3xl font-bold font-mono text-text-heading mt-1 flex items-baseline space-x-2">
                    <span>{marketData.price.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                    <span className={`text-xs font-semibold ${isUp ? 'text-success' : 'text-error'}`}>
                      {isUp ? '▲' : '▼'} {isUp ? '+' : ''}{marketData.change.toFixed(2)} ({isUp ? '+' : ''}{marketData.pct.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="border-t border-border-hairline pt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-[10px] font-mono">
                <div className="flex justify-between">
                  <span className="text-text-muted">Open:</span>
                  <span className="text-text-heading font-semibold">{marketData.details.open.toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">High:</span>
                  <span className="text-text-heading font-semibold text-success">{marketData.details.high.toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Low:</span>
                  <span className="text-text-heading font-semibold text-error">{marketData.details.low.toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Prev Close:</span>
                  <span className="text-text-heading font-semibold">{marketData.details.prevClose.toLocaleString('en-IN')}</span>
                </div>
              </div>
            </div>
          )
        }, apiService.getMarketOverview)}

        {/* Card 2: Market Structure */}
        {renderCard('structure', (structureData) => {
          return (
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col justify-between h-56 shadow-lg">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  <span>Market Structure</span>
                  <span className="text-accent">Algorithm</span>
                </div>
                <div className="mt-4 space-y-4">
                  <div>
                    <span className="text-xs text-text-muted font-sans">Current State:</span>
                    <div className="text-xl font-bold text-text-heading font-sans mt-0.5">{structureData.state}</div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-[10px] text-text-muted font-sans uppercase">Trend Strength</span>
                      <div className="text-sm font-semibold font-mono text-text-heading mt-0.5">{structureData.strength}</div>
                    </div>
                    <div>
                      <span className="text-[10px] text-text-muted font-sans uppercase">Classification</span>
                      <div className={`text-sm font-bold font-sans mt-0.5 ${
                        structureData.classification === 'Bullish' ? 'text-success' :
                        structureData.classification === 'Bearish' ? 'text-error' : 'text-warning'
                      }`}>{structureData.classification}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )
        }, apiService.getMarketStructure)}

        {/* Card 3: Market Breadth */}
        {renderCard('breadth', (breadthData) => {
          return (
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col justify-between h-56 shadow-lg">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  <span>Market Breadth</span>
                  <span className="text-text-muted">Ratio</span>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold font-mono text-text-heading">
                    {breadthData.advances} : {breadthData.declines}
                  </div>
                  <span className="text-[10px] text-text-muted">Advances vs Declines</span>
                </div>
              </div>

              <div className="space-y-2.5">
                <div className="w-full bg-canvas-soft-2 h-2 rounded overflow-hidden flex">
                  <div className="bg-success h-full" style={{ width: `${(breadthData.advances / (breadthData.advances + breadthData.declines)) * 100}%` }}></div>
                  <div className="bg-error h-full" style={{ width: `${(breadthData.declines / (breadthData.advances + breadthData.declines)) * 100}%` }}></div>
                </div>
                <div className="flex justify-between items-center text-[10px] font-mono">
                  <span className="text-success font-semibold">Advances ({breadthData.advances})</span>
                  <span className="text-text-muted">Unchanged ({breadthData.unchanged})</span>
                  <span className="text-error font-semibold">Declines ({breadthData.declines})</span>
                </div>
              </div>
            </div>
          )
        }, apiService.getMarketBreadth)}

        {/* Card 4: AI Sentiment */}
        {renderCard('sentiment', (sentimentData) => {
          return (
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col justify-between h-56 shadow-lg">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  <span>AI Sentiment</span>
                  <span className="text-warning">Gauge</span>
                </div>
                <div className="mt-3">
                  <div className="text-2xl font-bold font-sans text-text-heading flex items-center space-x-2">
                    <span className={
                      sentimentData.bias.includes('Bullish') ? 'text-success' :
                      sentimentData.bias.includes('Bearish') ? 'text-error' : 'text-text-heading'
                    }>{sentimentData.bias}</span>
                  </div>
                  <p className="text-[10px] text-text-body mt-1">Short-term algorithmic prediction model bias.</p>
                </div>
              </div>

              <div className="border-t border-border-hairline pt-3 grid grid-cols-2 gap-4 text-[10px] font-mono">
                <div>
                  <span className="text-text-muted">Put-Call Ratio (PCR):</span>
                  <div className="text-sm font-bold text-text-heading mt-0.5">{sentimentData.pcr}</div>
                </div>
                <div>
                  <span className="text-text-muted">Signal Strength:</span>
                  <div className="text-sm font-bold text-cyan mt-0.5">{sentimentData.strength}% ({sentimentData.signal})</div>
                </div>
              </div>
            </div>
          )
        }, apiService.getSentiment)}

        {/* Card 5: AI Recommendation */}
        {renderCard('recommendation', (recData) => {
          return (
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col justify-between h-56 shadow-lg">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  <span>AI Recommendation</span>
                  <span className="text-cyan">Signals</span>
                </div>
                <div className="mt-3">
                  <div className="flex items-center space-x-3">
                    <span className={`px-2.5 py-1 rounded text-xs font-bold font-mono tracking-wider ${
                      recData.action === 'BUY' ? 'bg-success/15 text-success' :
                      recData.action === 'SELL' ? 'bg-error/15 text-error' : 'bg-canvas-soft-2 text-text-body'
                    }`}>{recData.action}</span>
                    <span className="text-xs text-text-body font-mono">
                      Tgt: <span className="text-text-heading font-semibold">{recData.target}</span> | SL: <span className="text-text-heading font-semibold">{recData.stopLoss}</span>
                    </span>
                  </div>
                  <p className="text-[10px] text-text-body mt-2.5 leading-relaxed italic line-clamp-3">
                    "{recData.rationale}"
                  </p>
                </div>
              </div>
              <div className="text-[9px] font-mono text-text-muted italic">
                *Algorithmic recommendations are for study purposes only.
              </div>
            </div>
          )
        }, apiService.getRecommendation)}

        {/* Card 6: Support / Resistance */}
        {renderCard('levels', (levelsData) => {
          return (
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col justify-between h-56 shadow-lg">
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted">
                  <span>Support / Resistance</span>
                  <span className="text-text-muted">Pivots</span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-y-2 text-xs font-mono">
                  <div className="space-y-1">
                    <div className="text-[10px] text-text-muted">R3: <span className="text-text-heading font-semibold">{levelsData.r3.toFixed(1)}</span></div>
                    <div className="text-[10px] text-text-muted">R2: <span className="text-text-heading font-semibold">{levelsData.r2.toFixed(1)}</span></div>
                    <div className="text-[10px] text-text-muted">R1: <span className="text-text-heading font-semibold">{levelsData.r1.toFixed(1)}</span></div>
                  </div>
                  <div className="space-y-1 text-right">
                    <div className="text-[10px] text-text-muted">S1: <span className="text-text-heading font-semibold">{levelsData.s1.toFixed(1)}</span></div>
                    <div className="text-[10px] text-text-muted">S2: <span className="text-text-heading font-semibold">{levelsData.s2.toFixed(1)}</span></div>
                    <div className="text-[10px] text-text-muted">S3: <span className="text-text-heading font-semibold">{levelsData.s3.toFixed(1)}</span></div>
                  </div>
                </div>
              </div>
              <div className="border-t border-border-hairline pt-2 flex justify-between items-center text-[10px] font-mono">
                <span className="text-text-muted">Daily Pivot Point:</span>
                <span className="text-accent font-bold">{levelsData.pivot.toFixed(1)}</span>
              </div>
            </div>
          )
        }, apiService.getSupportResistance)}

        {/* Card 7: Top Gainers */}
        {renderCard('movers', (moversData) => {
          return (
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col h-56 shadow-lg overflow-hidden">
              <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted pb-2 border-b border-border-hairline">
                <span>Top Components</span>
                <span className="text-success font-semibold">Gainers</span>
              </div>
              <div className="mt-2 divide-y divide-border-hairline overflow-y-auto flex-1 pr-1">
                {moversData.gainers.map((stock) => (
                  <div key={stock.symbol} className="py-2 flex items-center justify-between font-mono text-[11px]">
                    <span className="font-semibold text-text-heading">{stock.symbol}</span>
                    <div className="space-x-3">
                      <span className="text-text-muted">
                        {typeof stock.price === 'number' 
                          ? stock.price.toLocaleString('en-IN', { minimumFractionDigits: 1 })
                          : stock.price
                        }
                      </span>
                      <span className="text-success font-semibold">+{stock.pct.toFixed(2)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        }, apiService.getTopMovers)}

        {/* Card 8: Top Losers */}
        {renderCard('movers', (moversData) => {
          return (
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col h-56 shadow-lg overflow-hidden">
              <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted pb-2 border-b border-border-hairline">
                <span>Top Components</span>
                <span className="text-error font-semibold">Losers</span>
              </div>
              <div className="mt-2 divide-y divide-border-hairline overflow-y-auto flex-1 pr-1">
                {moversData.losers.map((stock) => (
                  <div key={stock.symbol} className="py-2 flex items-center justify-between font-mono text-[11px]">
                    <span className="font-semibold text-text-heading">{stock.symbol}</span>
                    <div className="space-x-3">
                      <span className="text-text-muted">
                        {typeof stock.price === 'number' 
                          ? stock.price.toLocaleString('en-IN', { minimumFractionDigits: 1 })
                          : stock.price
                        }
                      </span>
                      <span className="text-error font-semibold">{stock.pct.toFixed(2)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )
        }, apiService.getTopMovers)}

        {/* Card 9: OI Activity */}
        {renderCard('oi', (oiData) => {
          return (
            <div className="bg-canvas-soft border border-border-hairline rounded-lg p-5 flex flex-col h-56 shadow-lg overflow-hidden">
              <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted pb-2 border-b border-border-hairline">
                <span>OI Activity</span>
                <span className="text-cyan">Volume Build-up</span>
              </div>
              <div className="mt-2 divide-y divide-border-hairline overflow-y-auto flex-1 pr-1">
                {oiData.map((activity, index) => (
                  <div key={index} className="py-2 flex items-center justify-between font-mono text-[11px]">
                    <span className="font-semibold text-text-heading">{activity.strike}</span>
                    <span className={`text-[10px] font-sans px-1.5 py-0.5 rounded ${
                      activity.tone === 'bullish' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                    }`}>{activity.type}</span>
                    <span className="text-text-heading font-semibold">{activity.oiChange}</span>
                  </div>
                ))}
              </div>
            </div>
          )
        }, apiService.getOiActivity)}

      </div>
    </div>
  )
}

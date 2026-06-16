import { useState, useEffect, useRef } from 'react'
import apiService from '../services/api'

export default function IndexAnalytics() {
  const [activeTab, setActiveTab] = useState('NIFTY')
  const indexTabs = ['NIFTY', 'BANKNIFTY', 'MIDCPNIFTY', 'SENSEX', 'INDIA VIX']
  
  const [chartData, setChartData] = useState([])
  const [marketData, setMarketData] = useState(null)
  const [levelsData, setLevelsData] = useState(null)
  const [structureData, setStructureData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [timeframe, setTimeframe] = useState('1d')
  const [interval, setInterval] = useState('1m')
  const [indicators, setIndicators] = useState({
    sma: true,
    levels: true
  })
  
  const [hoveredPoint, setHoveredPoint] = useState(null)
  const [mouseX, setMouseX] = useState(null)
  const [mouseY, setMouseY] = useState(null)
  const chartRef = useRef(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Map timeframe and interval to match Yahoo expectations
      let yInterval = '1m'
      if (timeframe === '1w') yInterval = '15m'
      if (timeframe === '1m') yInterval = '60m'
      if (timeframe === '1y') yInterval = '1d'
      
      const [chart, market, levels, structure] = await Promise.all([
        fetch(`http://localhost:8000/chart?symbol=${activeTab}&range=${timeframe}&interval=${yInterval}`).then(r => r.json()),
        apiService.getMarketOverview(activeTab),
        apiService.getSupportResistance(activeTab),
        apiService.getMarketStructure(activeTab)
      ])
      
      setChartData(chart)
      setMarketData(market)
      setLevelsData(levels)
      setStructureData(structure)
    } catch (err) {
      setError(err.message || 'Failed to fetch index analytics details')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [activeTab, timeframe])


  if (loading && chartData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-cyan/25 border-t-cyan rounded-full animate-spin"></div>
        <p className="text-sm font-mono text-text-muted">Loading index analytics engine...</p>
      </div>
    )
  }

  if (error && chartData.length === 0) {
    return (
      <div className="bg-canvas-soft border border-error/20 rounded-lg p-8 text-center max-w-md mx-auto my-12 space-y-4 shadow-lg">
        <svg className="w-12 h-12 text-error mx-auto animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-base font-bold text-text-heading">Index Analytics Engine Error</h3>
        <p className="text-xs text-text-body">{error}</p>
        <button onClick={fetchData} className="px-4 py-2 bg-primary text-on-primary rounded text-xs hover:opacity-90 font-medium">
          Retry Connection
        </button>
      </div>
    )
  }

  const prices = chartData.map(d => d.close)
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const priceRange = (maxPrice - minPrice) || 10
  
  // Calculate standard indicators (SMA-20)
  const smaPeriod = 20
  const getSmaData = () => {
    return chartData.map((d, idx) => {
      if (idx < smaPeriod) return null
      const slice = prices.slice(idx - smaPeriod + 1, idx + 1)
      const sum = slice.reduce((a, b) => a + b, 0)
      return sum / smaPeriod
    })
  }
  const smaValues = getSmaData()

  // SVG parameters
  const width = 1000
  const height = 380
  const paddingX = 50
  const paddingY = 30

  const getCoordinates = () => {
    return chartData.map((point, index) => {
      const x = paddingX + (index / (chartData.length - 1)) * (width - 2 * paddingX)
      const y = height - paddingY - ((point.close - minPrice) / priceRange) * (height - 2 * paddingY)
      return { x, y, point, index }
    })
  }
  const coords = getCoordinates()

  const pathD = coords.reduce((acc, coord, idx) => {
    return idx === 0 ? `M ${coord.x} ${coord.y}` : `${acc} L ${coord.x} ${coord.y}`
  }, '')

  const areaD = coords.length > 0
    ? `${pathD} L ${coords[coords.length - 1].x} ${height - paddingY} L ${coords[0].x} ${height - paddingY} Z`
    : ''

  // Build SMA Path
  const smaCoords = coords.map((c, idx) => {
    const smaVal = smaValues[idx]
    if (smaVal === null) return null
    const y = height - paddingY - ((smaVal - minPrice) / priceRange) * (height - 2 * paddingY)
    return { x: c.x, y }
  }).filter(c => c !== null)

  const smaPathD = smaCoords.reduce((acc, coord, idx) => {
    return idx === 0 ? `M ${coord.x} ${coord.y}` : `${acc} L ${coord.x} ${coord.y}`
  }, '')

  // Build Pivot lines coordinate mapping
  const getLevelY = (val) => {
    if (!val) return null
    return height - paddingY - ((val - minPrice) / priceRange) * (height - 2 * paddingY)
  }

  const handleMouseMove = (e) => {
    if (!chartRef.current) return
    const rect = chartRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    const svgX = (x / rect.width) * width
    const svgY = (y / rect.height) * height
    setMouseX(svgX)
    setMouseY(svgY)

    let closest = null
    let minDiff = Infinity
    coords.forEach(c => {
      const diff = Math.abs(c.x - svgX)
      if (diff < minDiff) {
        minDiff = diff
        closest = c
      }
    })
    if (closest) {
      setHoveredPoint(closest)
    }
  }

  const handleMouseLeave = () => {
    setHoveredPoint(null)
    setMouseX(null)
    setMouseY(null)
  }

  const isUp = chartData.length > 0 && chartData[chartData.length - 1].close >= chartData[0].close
  const strokeColor = isUp ? 'stroke-success' : 'stroke-error'
  const fillColor = isUp ? 'url(#greenGradient)' : 'url(#redGradient)'

  // Generate gridlines
  const gridLines = []
  const gridCount = 5
  for (let i = 0; i <= gridCount; i++) {
    const yVal = paddingY + (i / gridCount) * (height - 2 * paddingY)
    const priceVal = maxPrice - (i / gridCount) * priceRange
    gridLines.push({ yVal, priceVal })
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between space-y-4 xl:space-y-0 pb-2 border-b border-border-hairline">
        <div>
          <h1 className="text-xl font-bold font-sans text-text-heading tracking-tight flex items-center">
            <span>Index Technical Terminal</span>
            <span className="ml-2 px-1.5 py-0.5 text-[9px] font-semibold font-mono bg-violet/10 text-violet rounded border border-violet/20 uppercase tracking-widest">
              Advanced Charting
            </span>
          </h1>
          <p className="text-xs text-text-muted mt-0.5">
            Technical analysis indicators, moving averages, and dynamic pivot point overlays.
          </p>
        </div>

        {/* Index switcher */}
        <div className="flex flex-wrap gap-1 bg-canvas-soft-2 p-1 rounded-lg border border-border-hairline self-start">
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
      </div>

      {/* Main Grid: Chart & Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Interactive SVG Chart */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-canvas-soft border border-border-hairline rounded-lg p-6 shadow-xl relative">
            
            {/* Chart Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0 mb-4">
              {marketData && (
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-text-heading text-lg font-bold">{marketData.name} Index</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold bg-success/10 text-success border border-success/20`}>LIVE</span>
                  </div>
                  <div className="text-2xl font-mono font-bold text-text-heading mt-1 flex items-baseline space-x-2">
                    <span>{marketData.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    <span className={`text-xs font-semibold ${marketData.change >= 0 ? 'text-success' : 'text-error'}`}>
                      {marketData.change >= 0 ? '▲' : '▼'} {marketData.change >= 0 ? '+' : ''}{marketData.change.toFixed(2)} ({marketData.change >= 0 ? '+' : ''}{marketData.pct.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              )}

              {/* Chart Controls */}
              <div className="flex items-center space-x-2 self-start sm:self-center">
                {/* Timeframe */}
                <div className="flex space-x-1 bg-canvas-soft-2 p-1 rounded border border-border-hairline">
                  {['1d', '1w', '1m', '1y'].map(tf => (
                    <button
                      key={tf}
                      onClick={() => setTimeframe(tf)}
                      className={`px-2 py-0.5 text-[10px] font-semibold font-mono rounded uppercase ${
                        timeframe === tf
                          ? 'bg-canvas text-text-heading shadow-sm'
                          : 'text-text-body hover:text-text-heading'
                      }`}
                    >
                      {tf}
                    </button>
                  ))}
                </div>

                {/* Overlays */}
                <div className="flex space-x-1 bg-canvas-soft-2 p-1 rounded border border-border-hairline">
                  <button
                    onClick={() => setIndicators(prev => ({ ...prev, sma: !prev.sma }))}
                    className={`px-2 py-0.5 text-[10px] font-semibold font-mono rounded ${
                      indicators.sma
                        ? 'bg-violet/15 text-violet border border-violet/20 font-bold'
                        : 'text-text-body hover:text-text-heading'
                    }`}
                  >
                    SMA-20
                  </button>
                  <button
                    onClick={() => setIndicators(prev => ({ ...prev, levels: !prev.levels }))}
                    className={`px-2 py-0.5 text-[10px] font-semibold font-mono rounded ${
                      indicators.levels
                        ? 'bg-cyan/15 text-cyan border border-cyan/20 font-bold'
                        : 'text-text-body hover:text-text-heading'
                    }`}
                  >
                    Pivots
                  </button>
                </div>
              </div>
            </div>

            {/* Chart SVG */}
            <div className="relative w-full overflow-hidden mt-6">
              <svg
                ref={chartRef}
                viewBox={`0 0 ${width} ${height}`}
                className="w-full h-auto cursor-crosshair select-none"
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
              >
                <defs>
                  <linearGradient id="greenGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
                  </linearGradient>
                  <linearGradient id="redGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ef4444" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Gridlines */}
                {gridLines.map((line, i) => (
                  <g key={i}>
                    <line
                      x1={paddingX}
                      y1={line.yVal}
                      x2={width - paddingX}
                      y2={line.yVal}
                      className="stroke-border-hairline"
                      strokeWidth="1"
                      strokeDasharray="4 4"
                    />
                    <text
                      x={width - paddingX + 5}
                      y={line.yVal + 4}
                      className="fill-text-muted text-[10px] font-mono"
                    >
                      {line.priceVal.toFixed(1)}
                    </text>
                  </g>
                ))}

                {/* Dynamic Pivot Point Overlays */}
                {indicators.levels && levelsData && !levelsData.fallback && (
                  <g opacity="0.3">
                    {/* Pivot Line */}
                    {getLevelY(levelsData.pivot) && (
                      <g>
                        <line x1={paddingX} y1={getLevelY(levelsData.pivot)} x2={width - paddingX} y2={getLevelY(levelsData.pivot)} stroke="#a1a1a1" strokeWidth="1" strokeDasharray="3 2" />
                        <text x={paddingX + 5} y={getLevelY(levelsData.pivot) - 3} className="fill-text-muted text-[8px] font-mono">P: {levelsData.pivot.toFixed(1)}</text>
                      </g>
                    )}
                    {/* Resistance Line R1 */}
                    {getLevelY(levelsData.r1) && (
                      <g>
                        <line x1={paddingX} y1={getLevelY(levelsData.r1)} x2={width - paddingX} y2={getLevelY(levelsData.r1)} stroke="#ef4444" strokeWidth="1" />
                        <text x={paddingX + 5} y={getLevelY(levelsData.r1) - 3} className="fill-error text-[8px] font-mono">R1: {levelsData.r1.toFixed(1)}</text>
                      </g>
                    )}
                    {/* Support Line S1 */}
                    {getLevelY(levelsData.s1) && (
                      <g>
                        <line x1={paddingX} y1={getLevelY(levelsData.s1)} x2={width - paddingX} y2={getLevelY(levelsData.s1)} stroke="#10b981" strokeWidth="1" />
                        <text x={paddingX + 5} y={getLevelY(levelsData.s1) - 3} className="fill-success text-[8px] font-mono">S1: {levelsData.s1.toFixed(1)}</text>
                      </g>
                    )}
                  </g>
                )}

                {/* Area Gradient Fill */}
                {areaD && <path d={areaD} fill={fillColor} />}

                {/* Line Path */}
                {pathD && <path d={pathD} fill="none" className={`${strokeColor}`} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />}

                {/* SMA Path */}
                {indicators.sma && smaPathD && (
                  <path
                    d={smaPathD}
                    fill="none"
                    stroke="#7928ca"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity="0.85"
                  />
                )}

                {/* Last Dot */}
                {coords.length > 0 && (
                  <g>
                    <circle cx={coords[coords.length - 1].x} cy={coords[coords.length - 1].y} r="5" className={isUp ? 'fill-success' : 'fill-error'} />
                  </g>
                )}

                {/* Hover overlay crosshair */}
                {hoveredPoint && mouseX !== null && (
                  <g>
                    <line x1={hoveredPoint.x} y1={paddingY} x2={hoveredPoint.x} y2={height - paddingY} className="stroke-text-muted/30" strokeWidth="1" strokeDasharray="3 3" />
                    <line x1={paddingX} y1={hoveredPoint.y} x2={width - paddingX} y2={hoveredPoint.y} className="stroke-text-muted/30" strokeWidth="1" strokeDasharray="3 3" />
                    <circle cx={hoveredPoint.x} cy={hoveredPoint.y} r="4" className={`stroke-canvas ${isUp ? 'fill-success' : 'fill-error'}`} strokeWidth="1.5" />
                    
                    {/* Tooltip */}
                    <foreignObject
                      x={hoveredPoint.x > width / 2 ? hoveredPoint.x - 145 : hoveredPoint.x + 15}
                      y={hoveredPoint.y > height / 2 ? hoveredPoint.y - 75 : hoveredPoint.y + 15}
                      width="130"
                      height="60"
                    >
                      <div className="bg-canvas border border-border-hairline p-2 rounded shadow-lg text-[10px] font-mono text-text-heading flex flex-col space-y-0.5">
                        <div className="text-text-muted font-sans font-medium">Time: {new Date(hoveredPoint.point.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                        <div className="font-bold flex justify-between">
                          <span>Val:</span>
                          <span>{hoveredPoint.point.close.toFixed(2)}</span>
                        </div>
                        {indicators.sma && smaValues[hoveredPoint.index] && (
                          <div className="flex justify-between text-violet">
                            <span>SMA:</span>
                            <span>{smaValues[hoveredPoint.index].toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    </foreignObject>
                  </g>
                )}
              </svg>
            </div>
            
            {/* Chart footer timestamps */}
            <div className="flex justify-between items-center mt-3 text-[10px] text-text-muted font-mono border-t border-border-hairline pt-3">
              <span>{chartData.length > 0 && new Date(chartData[0].timestamp * 1000).toLocaleDateString()}</span>
              <span>NSE / BSE Real-time Chart Data</span>
              <span>{chartData.length > 0 && new Date(chartData[chartData.length - 1].timestamp * 1000).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        {/* Right Column: Quantitative & Technical Indicators */}
        <div className="space-y-6">
          {/* Support & Resistance Table */}
          {levelsData && (
            <div className="bg-canvas border border-border-hairline rounded-lg p-5 shadow-lg space-y-4">
              <div className="text-[10px] font-mono uppercase tracking-wider text-text-muted flex justify-between items-center pb-2 border-b border-border-hairline">
                <span>Daily Pivot Point Levels</span>
                <span className="px-1.5 py-0.5 rounded bg-cyan/10 text-cyan text-[8px] font-mono font-semibold uppercase">Floor Pivots</span>
              </div>
              <div className="space-y-2 font-mono text-[11px]">
                <div className="flex justify-between py-1 border-b border-border-hairline/40 text-error">
                  <span>Resistance 3 (R3)</span>
                  <span className="font-bold">{levelsData.r3.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border-hairline/40 text-error/85">
                  <span>Resistance 2 (R2)</span>
                  <span className="font-bold">{levelsData.r2.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border-hairline/40 text-error/70">
                  <span>Resistance 1 (R1)</span>
                  <span className="font-bold">{levelsData.r1.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1.5 bg-canvas-soft-2 px-2 rounded text-text-heading border border-border-hairline">
                  <span className="font-sans font-semibold">Central Pivot (PP)</span>
                  <span className="font-bold">{levelsData.pivot.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border-hairline/40 text-success/70">
                  <span>Support 1 (S1)</span>
                  <span className="font-bold">{levelsData.s1.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-border-hairline/40 text-success/85">
                  <span>Support 2 (S2)</span>
                  <span className="font-bold">{levelsData.s2.toFixed(2)}</span>
                </div>
                <div className="flex justify-between py-1 text-success">
                  <span>Support 3 (S3)</span>
                  <span className="font-bold">{levelsData.s3.toFixed(2)}</span>
                </div>
              </div>
            </div>
          )}

          {/* Market Structure Details */}
          {structureData && (
            <div className="bg-canvas border border-border-hairline rounded-lg p-5 shadow-lg space-y-4">
              <div className="text-[10px] font-mono uppercase tracking-wider text-text-muted pb-2 border-b border-border-hairline">
                <span>Quantitative Structural Insights</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-[10px] text-text-muted uppercase">Trend State</div>
                  <div className="text-sm font-bold text-text-heading mt-1">{structureData.state}</div>
                </div>
                <div>
                  <div className="text-[10px] text-text-muted uppercase">Momentum Strength</div>
                  <div className="text-sm font-bold text-cyan mt-1">{structureData.strength}</div>
                </div>
              </div>
              <div className="border-t border-border-hairline/60 pt-3 flex justify-between items-center">
                <span className="text-xs text-text-body font-medium">Algorithmic Bias</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider ${
                  structureData.classification === 'Bullish' ? 'bg-success/15 text-success' :
                  structureData.classification === 'Bearish' ? 'bg-error/15 text-error' : 'bg-canvas-soft-2 text-text-body'
                }`}>{structureData.classification}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

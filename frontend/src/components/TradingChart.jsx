import { useState, useRef, useEffect } from 'react'

export default function TradingChart() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  const [hoveredPoint, setHoveredPoint] = useState(null)
  const [mouseX, setMouseX] = useState(null)
  const [mouseY, setMouseY] = useState(null)
  const chartRef = useRef(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('http://localhost:8000/chart?symbol=NIFTY&range=1d&interval=15m')
      if (!response.ok) {
        throw new Error('Technical chart feed currently unavailable - live broker connection required.')
      }
      const rawData = await response.json()
      if (!rawData || rawData.length === 0) {
        throw new Error('Empty dataset returned from technical feed.')
      }
      const formatted = rawData.map(item => ({
        time: new Date(item.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        price: item.close
      }))
      setData(formatted)
    } catch (err) {
      setError(err.message || 'Failed to fetch chart data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="w-full bg-canvas-soft border border-border-hairline rounded-lg p-6 shadow-xl flex flex-col items-center justify-center h-[380px] space-y-4">
        <div className="w-8 h-8 border-2 border-cyan/25 border-t-cyan rounded-full animate-spin"></div>
        <p className="text-xs font-mono text-text-muted">Loading technical chart data...</p>
      </div>
    )
  }

  if (error || data.length === 0) {
    return (
      <div className="w-full bg-canvas-soft border border-border-hairline rounded-lg p-6 shadow-xl flex flex-col items-center justify-center h-[380px] text-center space-y-3">
        <svg className="w-10 h-10 text-error animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <h3 className="text-xs font-bold text-text-heading font-sans">Chart Data Error</h3>
        <p className="text-[10px] text-error font-mono max-w-xs">{error || 'No data points returned'}</p>
        <button onClick={fetchData} className="mt-2 px-3 py-1 bg-canvas-soft-2 border border-border-hairline hover:bg-border-hairline/25 rounded text-[10px] text-text-heading transition-all">
          Retry
        </button>
      </div>
    )
  }

  const prices = data.map(d => d.price)
  const minPrice = Math.min(...prices) - 5
  const maxPrice = Math.max(...prices) + 5
  const priceRange = maxPrice - minPrice

  // Map coordinates to SVG viewbox (1000 x 300)
  const width = 1000
  const height = 300
  const paddingX = 40
  const paddingY = 20

  const getCoordinates = () => {
    return data.map((point, index) => {
      const x = paddingX + (index / (data.length - 1)) * (width - 2 * paddingX)
      const y = height - paddingY - ((point.price - minPrice) / priceRange) * (height - 2 * paddingY)
      return { x, y, point }
    })
  }

  const coords = getCoordinates()
  
  // Build SVG path string
  const pathD = coords.reduce((acc, coord, idx) => {
    return idx === 0 ? `M ${coord.x} ${coord.y}` : `${acc} L ${coord.x} ${coord.y}`
  }, '')

  // Build closing path for the area gradient fill
  const areaD = coords.length > 0
    ? `${pathD} L ${coords[coords.length - 1].x} ${height - paddingY} L ${coords[0].x} ${height - paddingY} Z`
    : ''

  const handleMouseMove = (e) => {
    if (!chartRef.current) return
    const rect = chartRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    // Scale local x to SVG viewbox x
    const svgX = (x / rect.width) * width
    const svgY = (y / rect.height) * height
    setMouseX(svgX)
    setMouseY(svgY)

    // Find closest data point by X coordinate
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

  // Generate gridlines
  const gridLines = []
  const gridCount = 5
  for (let i = 0; i <= gridCount; i++) {
    const yVal = paddingY + (i / gridCount) * (height - 2 * paddingY)
    const priceVal = maxPrice - (i / gridCount) * priceRange
    gridLines.push({ yVal, priceVal })
  }

  const isUp = data[data.length - 1].price >= data[0].price
  const strokeColor = isUp ? 'stroke-success' : 'stroke-error'
  const fillColor = isUp ? 'url(#greenGradient)' : 'url(#redGradient)'

  return (
    <div className="w-full bg-canvas-soft border border-border-hairline rounded-lg p-6 shadow-xl relative">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-text-heading text-lg font-bold">NIFTY 50 Index</span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan/15 text-cyan tracking-wider">INDEX</span>
            <span className="text-xs text-text-muted">15m Interval</span>
          </div>
          <div className="text-2xl font-mono font-bold text-text-heading mt-1 flex items-baseline space-x-2">
            <span>
              {data[data.length - 1].price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
            <span className={`text-sm font-semibold ${isUp ? 'text-success' : 'text-error'}`}>
              {isUp ? '▲' : '▼'}{' '}
              {Math.abs(data[data.length - 1].price - data[0].price).toFixed(2)} (
              {((data[data.length - 1].price - data[0].price) / data[0].price * 100).toFixed(2)}%)
            </span>
          </div>
        </div>
        
        {/* Toggle options */}
        <div className="flex space-x-1.5 bg-canvas-soft-2 p-1 rounded-md border border-border-hairline">
          {['1D'].map(timeframe => (
            <button
              key={timeframe}
              className="px-2.5 py-1 text-xs font-semibold rounded bg-canvas text-text-heading shadow-sm"
            >
              {timeframe}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Interactive Chart Canvas */}
      <div className="relative w-full overflow-hidden">
        <svg
          ref={chartRef}
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto cursor-crosshair select-none"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          <defs>
            {/* Area Gradient Defs */}
            <linearGradient id="greenGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="redGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines & Price Labels */}
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
                {line.priceVal.toFixed(0)}
              </text>
            </g>
          ))}

          {/* Area Gradient Fill */}
          {areaD && (
            <path
              d={areaD}
              fill={fillColor}
            />
          )}

          {/* Line Path */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              className={`${strokeColor}`}
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Live tracking glowing pulse dot at the last point */}
          {coords.length > 0 && (
            <g>
              <circle
                cx={coords[coords.length - 1].x}
                cy={coords[coords.length - 1].y}
                r="6"
                className={isUp ? 'fill-success/40' : 'fill-error/40'}
              />
              <circle
                cx={coords[coords.length - 1].x}
                cy={coords[coords.length - 1].y}
                r="3"
                className={isUp ? 'fill-success' : 'fill-error'}
              />
            </g>
          )}

          {/* Interactive Crosshair & Tooltip Overlay */}
          {hoveredPoint && mouseX !== null && mouseY !== null && (
            <g>
              {/* Vertical crosshair line */}
              <line
                x1={hoveredPoint.x}
                y1={paddingY}
                x2={hoveredPoint.x}
                y2={height - paddingY}
                className="stroke-text-muted/40"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
              {/* Horizontal crosshair line */}
              <line
                x1={paddingX}
                y1={hoveredPoint.y}
                x2={width - paddingX}
                y2={hoveredPoint.y}
                className="stroke-text-muted/40"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
              {/* Dot on line */}
              <circle
                cx={hoveredPoint.x}
                cy={hoveredPoint.y}
                r="5"
                className={`stroke-canvas ${isUp ? 'fill-success' : 'fill-error'}`}
                strokeWidth="1.5"
              />
              
              {/* Tooltip background & text */}
              <foreignObject
                x={hoveredPoint.x > width / 2 ? hoveredPoint.x - 145 : hoveredPoint.x + 15}
                y={hoveredPoint.y > height / 2 ? hoveredPoint.y - 75 : hoveredPoint.y + 15}
                width="130"
                height="60"
              >
                <div className="bg-canvas border border-border-hairline p-2 rounded shadow-lg text-[11px] font-mono text-text-heading flex flex-col space-y-0.5">
                  <div className="text-text-muted font-sans font-medium">{hoveredPoint.point.time}</div>
                  <div className="font-bold flex items-center justify-between">
                    <span>Val:</span>
                    <span>{hoveredPoint.point.price.toFixed(2)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Diff:</span>
                    <span className={hoveredPoint.point.price >= data[0].price ? 'text-success' : 'text-error'}>
                      {(hoveredPoint.point.price - data[0].price).toFixed(2)}
                    </span>
                  </div>
                </div>
              </foreignObject>
            </g>
          )}
        </svg>
      </div>

      {/* Footer labels */}
      <div className="flex items-center justify-between border-t border-border-hairline pt-3 mt-1 text-[10px] text-text-muted font-mono">
        <span>{data[0].time}</span>
        <span>NSE Trading Hours (09:15 AM - 03:30 PM)</span>
        <span>{data[data.length - 1].time}</span>
      </div>
    </div>
  )
}

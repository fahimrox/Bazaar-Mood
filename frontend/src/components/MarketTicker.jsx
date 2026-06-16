import { useEffect, useState } from 'react'

export default function MarketTicker() {
  const [indices, setIndices] = useState([])
  const [activeTickIdx, setActiveTickIdx] = useState(null)
  const [tickDirection, setTickDirection] = useState('up')
  const [error, setError] = useState(false)

  const fetchIndices = async (prevIndices = null) => {
    try {
      const response = await fetch('http://localhost:8000/indices')
      if (!response.ok) {
        throw new Error('Unavailable')
      }
      const data = await response.json()
      
      // Compare values to find what changed and trigger active tick glow
      if (prevIndices && prevIndices.length === data.length) {
        for (let i = 0; i < data.length; i++) {
          if (data[i].price !== prevIndices[i].price) {
            const diff = data[i].price - prevIndices[i].price
            setActiveTickIdx(i)
            setTickDirection(diff >= 0 ? 'up' : 'down')
            setTimeout(() => {
              setActiveTickIdx(null)
            }, 800)
            break
          }
        }
      }
      
      // Map keys to match the component expectations: name, value, change, pct
      const mapped = data.map(item => ({
        name: item.name === 'INDIA VIX' ? 'INDIA VIX' : (item.symbol === 'NIFTY' ? 'NIFTY 50' : item.symbol),
        value: item.price,
        change: item.change,
        pct: item.pct
      }))
      
      setIndices(mapped)
      setError(false)
    } catch (err) {
      setError(true)
    }
  }

  useEffect(() => {
    fetchIndices()
    const timer = setInterval(() => {
      setIndices(current => {
        fetchIndices(current)
        return current
      })
    }, 15000) // Poll real market data every 15 seconds

    return () => clearInterval(timer)
  }, [])

  const renderTickerList = () => {
    if (error || indices.length === 0) {
      return (
        <div className="flex items-center px-6 py-2.5 text-xs font-mono text-error select-none">
          Market index live feed currently unavailable - live broker connection required.
        </div>
      )
    }
    
    // Repeat items to fill marquee seamlessly
    const repeated = Array(4).fill(indices).flat()
    return repeated.map((item, idx) => {
      const isUp = item.change >= 0
      const isCurrentlyTicking = activeTickIdx === (idx % indices.length)
      
      let tickBg = ''
      if (isCurrentlyTicking) {
        tickBg = tickDirection === 'up' ? 'bg-success/20 text-success' : 'bg-error/20 text-error'
      }

      return (
        <div
          key={`${item.name}-${idx}`}
          className={`flex items-center space-x-2 px-6 py-2.5 border-r border-border-hairline text-xs font-mono select-none transition-colors duration-300 ${tickBg}`}
        >
          <span className="text-text-muted font-sans font-medium">{item.name}</span>
          <span className="text-text-heading font-semibold">
            {item.value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          <span className={`flex items-center font-medium ${isUp ? 'text-success' : 'text-error'}`}>
            <svg
              className={`w-3 h-3 mr-0.5 transform transition-transform ${isUp ? '' : 'rotate-180'}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth="3"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
            </svg>
            {isUp ? '+' : ''}
            {item.change.toFixed(2)} ({isUp ? '+' : ''}
            {item.pct.toFixed(2)}%)
          </span>
        </div>
      )
    })
  }

  return (
    <div className="w-full bg-canvas border-b border-border-hairline overflow-hidden flex items-center relative z-40 h-10">
      <div className="flex whitespace-nowrap animate-ticker hover:[animation-play-state:paused]">
        {renderTickerList()}
      </div>
    </div>
  )
}

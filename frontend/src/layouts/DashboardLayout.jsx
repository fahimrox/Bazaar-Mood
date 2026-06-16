import MarketTicker from '../components/MarketTicker'
import Navbar from '../components/Navbar'

export default function DashboardLayout({ children, activeTab, setActiveTab }) {
  return (
    <div className="min-h-screen bg-canvas flex flex-col text-text-body">
      {/* Top Banner: Market Ticker */}
      <MarketTicker />

      {/* Header: JustTicks Navbar */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main content viewport */}
      <main className="flex-1 w-full max-w-[1400px] mx-auto px-4 sm:px-6 py-6 overflow-x-hidden">
        {children}
      </main>

      {/* Subtle bottom footer */}
      <footer className="border-t border-border-hairline py-4 px-6 text-center text-[10px] text-text-muted font-mono bg-canvas-soft">
        Bazaar Mood Trading Intelligence. NSE/BSE delayed feeds. Built with React & Tailwind CSS v4.
      </footer>
    </div>
  )
}

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = ['Dashboard', 'Market', 'Options', 'F&O', 'Sector', 'Screener', 'Heatmap']

  return (
    <nav className="h-16 px-6 bg-canvas-soft border-b border-border-hairline flex items-center justify-between sticky top-0 z-50">
      {/* Left: Brand Logo & Links */}
      <div className="flex items-center space-x-8">
        <a href="/" className="flex items-center space-x-2 text-text-heading font-sans font-semibold tracking-tight text-lg">
          <div className="relative w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan to-violet flex items-center justify-center text-on-primary shadow-lg shadow-cyan/15">
            <svg className="w-5 h-5 text-zinc-950 font-bold" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
            </svg>
            <div className="absolute -inset-0.5 rounded-lg bg-gradient-to-tr from-cyan to-violet opacity-30 blur-sm -z-10 animate-pulse-fast"></div>
          </div>
          <span>Bazaar Mood</span>
        </a>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center space-x-1">
          {navItems.map((item) => {
            const isActive = activeTab === item
            return (
              <button
                key={item}
                onClick={() => setActiveTab(item)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'text-text-heading bg-canvas-soft-2 border border-border-hairline shadow-inner'
                    : 'text-text-body hover:text-text-heading hover:bg-canvas-soft-2/50'
                }`}
              >
                {item}
              </button>
            )
          })}
        </div>
      </div>

      {/* Right: Market Status, Search & User */}
      <div className="flex items-center space-x-4">
        {/* Status Indicator */}
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-success/10 border border-success/20 text-xs font-semibold text-success uppercase tracking-wider">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-success"></span>
          </span>
          <span className="hidden sm:inline">NSE Live</span>
        </div>

        {/* Search Input */}
        <div className="relative hidden lg:block w-64">
          <input
            type="text"
            placeholder="Search stocks, options, indices..."
            className="w-full h-9 pl-9 pr-4 text-sm bg-canvas-soft-2 border border-border-hairline rounded-md text-text-heading placeholder-text-muted focus:outline-none focus:border-cyan transition-colors"
          />
          <svg className="absolute left-3 top-2.5 w-4 h-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        {/* User Profile */}
        <button className="flex items-center space-x-2 focus:outline-none">
          <div className="w-8 h-8 rounded-full border border-border-hairline bg-canvas-soft-2 flex items-center justify-center text-text-heading hover:border-text-body transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
        </button>
      </div>
    </nav>
  )
}

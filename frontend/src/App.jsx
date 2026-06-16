import { useState } from 'react'
import DashboardLayout from './layouts/DashboardLayout'
import Dashboard from './pages/Dashboard'
import IndexAnalytics from './pages/IndexAnalytics'
import OptionsAnalytics from './pages/OptionsAnalytics'
import FOAnalytics from './pages/FOAnalytics'
import SectorAnalytics from './pages/SectorAnalytics'
import Screeners from './pages/Screeners'
import Heatmaps from './pages/Heatmaps'

function App() {
  const [currentPage, setCurrentPage] = useState('Dashboard')

  const renderPage = () => {
    switch (currentPage) {
      case 'Dashboard':
        return <Dashboard />
      case 'Market':
        return <IndexAnalytics />
      case 'Options':
        return <OptionsAnalytics />
      case 'F&O':
        return <FOAnalytics />
      case 'Sector':
        return <SectorAnalytics />
      case 'Screener':
        return <Screeners />
      case 'Heatmap':
        return <Heatmaps />
      default:
        return <Dashboard />
    }
  }

  return (
    <DashboardLayout activeTab={currentPage} setActiveTab={setCurrentPage}>
      {renderPage()}
    </DashboardLayout>
  )
}

export default App

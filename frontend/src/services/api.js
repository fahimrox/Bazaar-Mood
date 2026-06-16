const BASE_URL = 'http://localhost:8000'

async function fetchFromApi(endpoint, symbol) {
  const url = `${BASE_URL}${endpoint}?symbol=${encodeURIComponent(symbol)}`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`Failed to fetch from ${endpoint}: ${response.statusText}`)
  }
  return response.json()
}

export const apiService = {
  getMarketOverview: (symbol) => fetchFromApi('/market', symbol),
  getMarketBreadth: (symbol) => fetchFromApi('/market-breadth', symbol),
  getSentiment: (symbol) => fetchFromApi('/sentiment', symbol),
  getRecommendation: (symbol) => fetchFromApi('/trade-recommendation', symbol),
  getTopMovers: (symbol) => fetchFromApi('/top-movers', symbol),
  getOiActivity: (symbol) => fetchFromApi('/oi-activity', symbol),
  getSupportResistance: (symbol) => fetchFromApi('/support-resistance', symbol),
  getMarketStructure: (symbol) => fetchFromApi('/market-structure', symbol),
  getScreeners: () => fetchFromApi('/screeners', ''),
  getHeatmaps: () => fetchFromApi('/heatmaps', ''),
}
export default apiService

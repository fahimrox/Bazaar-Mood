# ⚙️ Backend

## Overview
The backend layer houses all core analytical engines, data pipelines, and REST/WebSocket APIs powering Bazaar Mood.

## Engines
| Engine             | Responsibility                                      |
|--------------------|-----------------------------------------------------|
| `data_engine`      | Market data ingestion, normalization & storage      |
| `option_engine`    | Options chain parsing, greeks & OI analysis         |
| `sentiment_engine` | News scraping, NLP sentiment scoring                |
| `sector_engine`    | Sector rotation tracking & heatmap generation       |
| `support_engine`   | Support/resistance detection using price action     |

## Planned Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Task Queue**: Celery + Redis
- **Data Sources**: NSE, BSE, Yahoo Finance, Angel One API

## Getting Started
> Setup instructions coming soon.

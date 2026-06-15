# 📡 Data Engine

## Overview
Responsible for ingesting, normalizing, and storing all market data from NSE, BSE, and third-party providers. Acts as the single source of truth for OHLCV, F&O, and index data across the platform.

## Responsibilities
- Live & historical OHLCV data ingestion (NSE/BSE)
- WebSocket price feed management
- Data normalization & deduplication
- Storage to TimescaleDB / PostgreSQL
- Redis caching for hot data (live prices, last traded price)

## Planned Modules
- `fetcher.py` — API clients for NSE, Yahoo Finance, Angel One
- `normalizer.py` — Standardizes raw data into unified schema
- `scheduler.py` — Cron-based & event-driven data refresh
- `cache.py` — Redis cache manager

## Getting Started
> Setup instructions coming soon.

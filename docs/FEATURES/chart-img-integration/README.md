# chart-img.com Integration

![Status](https://img.shields.io/badge/status-planned-yellow)
![Priority](https://img.shields.io/badge/priority-high-red)
![Phase](https://img.shields.io/badge/phase-5C-blue)

## Overview

Integration der chart-img.com API zur dynamischen Generierung von TradingView-Charts für alle AI Agents (ChartWatcher, MorningPlanner, JournalBot, TradeMonitor).

### Key Features

- **Flexible Symbol Configuration**: User können Symbole, Timeframes und Indikatoren konfigurieren
- **4 Agent Integrations**: ChartWatcher, MorningPlanner, JournalBot, TradeMonitor
- **Snapshot Storage**: Chart-Snapshots in Database mit Metadaten
- **Rate Limiting**: Intelligentes Rate-Limiting (1,000/Tag, 15/Sek)
- **Multi-Timeframe**: Support für M5, M15, H1, H4, D1
- **Custom Indicators**: RSI, MACD, Bollinger Bands, Volume

## Use Cases

1. **ChartWatcher**: Lädt aktuelle Charts für Analyse-Tasks
2. **MorningPlanner**: Generiert Setup-Charts für Daily Report
3. **JournalBot**: Fügt Chart-Snapshots zu Journal-Entries hinzu
4. **TradeMonitor**: Live-Monitoring Charts (Optional)

## API Details

- **Provider**: chart-img.com
- **Plan**: MEGA ($10/month)
- **Daily Limit**: 1,000 requests
- **Rate Limit**: 15 requests/second
- **Max Resolution**: 1920x1600
- **Storage Duration**: 60 days
- **API Key**: Stored in environment variables

## Quick Links

| Document | Description |
|----------|-------------|
| [Architecture](./01_ARCHITECTURE.md) | System design, components, data flow |
| [Database Schema](./02_DATABASE_SCHEMA.md) | Tables, JSONB configs, RLS policies |
| [API Endpoints](./03_API_ENDPOINTS.md) | FastAPI routes, request/response schemas |
| [Frontend Components](./04_FRONTEND_COMPONENTS.md) | React components, user flows |
| [Agent Integration](./05_AGENT_INTEGRATION.md) | ChartWatcher, MorningPlanner, JournalBot |
| [Deployment](./06_DEPLOYMENT.md) | Hetzner deployment, env vars, migration |
| [Testing](./07_TESTING.md) | Test checklists, scenarios |
| [Troubleshooting](./08_TROUBLESHOOTING.md) | Common issues, solutions |
| [Implementation Checklist](./IMPLEMENTATION_CHECKLIST.md) | Master checklist (6 phases) |
| [Session Context](./SESSION_CONTEXT.md) | Quick start for new sessions |

## Architecture Diagram

```
┌─────────────────┐
│  Next.js Frontend│
│  Symbol Config UI│
└────────┬─────────┘
         │ (saves config)
         ▼
┌─────────────────┐
│  Supabase DB    │
│  market_symbols │  ← chart_config (JSONB)
│  chart_snapshots│  ← URL, metadata, timestamp
└────────┬─────────┘
         │ (reads config)
         ▼
┌─────────────────┐
│  AI Agents      │
│  (Python/Celery)│
│  ├─ChartWatcher │
│  ├─MorningPlanner│
│  ├─JournalBot   │
│  └─TradeMonitor │
└────────┬─────────┘
         │ (generates URL)
         ▼
┌─────────────────┐
│  chart-img.com  │
│  API            │  ← GET https://api.chart-img.com/tradingview/advanced-chart
└─────────────────┘
```

## Implementation Phases

### Phase 1: Database Setup (1h)
- [x] Extend `market_symbols` table with `chart_config` JSONB
- [x] Create `chart_snapshots` table
- [x] Add RLS policies
- [x] Create indexes

### Phase 2: Backend API (2h)
- [ ] FastAPI endpoints for chart generation
- [ ] chart-img.com API client
- [ ] Rate-limiting middleware
- [ ] Snapshot storage service

### Phase 3: Frontend UI (3h)
- [ ] Symbol configuration modal
- [ ] Timeframe selector
- [ ] Indicator checkboxes
- [ ] Chart preview component

### Phase 4: Agent Integration (3h)
- [ ] ChartWatcher update (fix lines 554-560)
- [ ] MorningPlanner integration
- [ ] JournalBot integration
- [ ] TradeMonitor (optional)

### Phase 5: Testing (2h)
- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E tests
- [ ] Manual testing

### Phase 6: Deployment (1h)
- [ ] Environment variables
- [ ] Database migration
- [ ] Hetzner deployment
- [ ] Verification

**Total Estimated Time**: 12 hours

## Current Status

- **Database Schema**: ✅ Designed
- **API Client**: ⏳ In Progress
- **Frontend UI**: 📋 Planned
- **Agent Integration**: 📋 Planned
- **Testing**: 📋 Planned
- **Deployment**: 📋 Planned

## Dependencies

- Supabase (Database)
- FastAPI (Backend)
- Next.js (Frontend)
- Celery (Agent Execution)
- chart-img.com API (External Service)

## Related Features

- [EOD Levels System](../eod-levels-system/README.md)
- [Liquidity Alerts](../liquidity-alerts/README.md)
- [AI Agents](../ai-agents/README.md)

## Team Notes

- **API Key Security**: Never commit API key to Git. Use environment variables only.
- **Rate Limiting**: Implement aggressive caching to stay within 1,000/day limit.
- **Symbol Mapping**: TradeMatrix uses Yahoo symbols (^GDAXI), chart-img uses TradingView symbols (XETR:DAX).
- **Error Handling**: Graceful fallback if API limit exceeded.

## Next Steps

1. Read [SESSION_CONTEXT.md](./SESSION_CONTEXT.md) for quick start
2. Review [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md)
3. Start with Phase 1 (Database Setup)

---

**Last Updated**: 2025-11-02
**Author**: TradeMatrix Team
**Status**: Planning Phase

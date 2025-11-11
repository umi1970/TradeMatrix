# ❌ DEPRECATED: chart-img.com Integration

**Decision Date:** 2025-11-11
**Status:** ABORTED - Too Expensive

---

## Why This Feature Was Abandoned

### Cost Analysis
- **MEGA Plan:** $10/month
- **Request Limit:** 1000 requests/day (~33 requests/hour)
- **OpenAI Vision API:** Additional cost per image analysis
- **Scalability:** Not viable for multi-user SaaS

### Issues Identified
1. **Limited Throughput:** 33 requests/hour insufficient for production
2. **High Cost:** $10/mo + Vision API costs per analysis
3. **Rate Limiting:** Would need complex caching/queue system
4. **Not Cost-Effective:** User has TradingView Premium already

---

## Alternative Solution: Phase 5E - TradingView CSV Upload

**Chosen Approach:** Manual CSV upload from TradingView Premium

### Why This Is Better
- ✅ **User Control:** Full access to TradingView Premium features
  - 20K historical bars
  - Second-based intervals
  - All indicators (custom Pine Scripts)
  - Custom timeframes
- ✅ **Zero API Costs:** No external API fees
- ✅ **No Rate Limits:** User uploads when needed
- ✅ **Better Data Quality:** User configures exactly what they need
- ✅ **Simple Architecture:** No complex caching/queue needed

### Implementation Status
- **Backend:** FastAPI CSV parser (25 indicators)
- **Frontend:** CSV upload, chart viewer, analyses table
- **Deployment:** Hetzner server (FastAPI + python-multipart)
- **Status:** LIVE (100% complete)

See `claude.md` for full implementation details.

---

## Historical Context

This feature was explored in Phase 5D after Phase 5C (TradingView Widgets) proved inadequate for real index data (TVC:DJI requires Premium).

Testing showed chart-img.com worked technically, but economic analysis revealed it was not viable for SaaS pricing model.

---

## Files in This Directory

All files in this directory are **historical records only** and should not be used for implementation.

For current chart functionality, see:
- `apps/web/src/components/dashboard/csv-upload-zone.tsx`
- `apps/web/src/components/dashboard/csv-chart-viewer.tsx`
- `hetzner-deploy/src/services/tv_csv_parser.py`

---

**Last Updated:** 2025-11-11

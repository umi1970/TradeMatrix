# Archived Documentation

This folder contains documentation that is no longer actively maintained but preserved for historical reference.

## Archived on: October 29, 2025

### Reason for Archival
These documents describe the original system architecture before the transition to Supabase. They are now superseded by the current documentation but kept for reference purposes.

---

## Archived Files

### Original Documentation (Pre-Supabase)
- **00_README.md** - Original project README
  - Superseded by: [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)

- **01_System_Architecture.md** - Old system architecture (custom backend)
  - Superseded by: [ARCHITECTURE.md](../ARCHITECTURE.md)

- **02_Agents_and_Modules.md** - Original agent concepts
  - Superseded by: [00_MASTER_ROADMAP.md](../00_MASTER_ROADMAP.md) Phase 3

- **07_Trade_Flows.md** - YAML-based trade flows
  - Concepts retained in: [04_Trading_Rules.md](../04_Trading_Rules.md)

- **08_Reporting_Workflow.md** - Original reporting workflow
  - Superseded by: [00_MASTER_ROADMAP.md](../00_MASTER_ROADMAP.md) Phase 3 (JournalBot)

- **09_Macro_Integration.md** - Macro event integration
  - To be reimplemented in Phase 2/3

### Initial Prompt
- **initial_prompt.txt** (formerly anleitung.txt)
  - Original project requirements and vision
  - Historical reference only

---

## Current Documentation

For up-to-date documentation, see:

### Primary References
- **[00_MASTER_ROADMAP.md](../00_MASTER_ROADMAP.md)** - Complete project roadmap (START HERE!)
- **[CLAUDE.md](../../CLAUDE.md)** - Session onboarding guide
- **[PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md)** - Project overview
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - Current architecture (Supabase-based)

### Active Documentation
- [03_AI_Analyzer.md](../03_AI_Analyzer.md) - AI analysis concepts
- [04_Trading_Rules.md](../04_Trading_Rules.md) - Trading rules
- [05_Validation_Engine.md](../05_Validation_Engine.md) - Validation logic
- [06_Risk_Management.md](../06_Risk_Management.md) - Risk management
- [10_Branding_and_Design.md](../10_Branding_and_Design.md) - Design system

---

## Major Changes from Archived Architecture

### What Changed
1. **Backend:** Custom SQLAlchemy + Alembic → **Supabase** (PostgreSQL + Auth + Storage)
2. **Authentication:** Custom JWT → **Supabase Auth**
3. **File Storage:** Custom S3/local → **Supabase Storage**
4. **CRUD APIs:** FastAPI endpoints → **Auto-generated Supabase REST APIs**
5. **Webhooks:** FastAPI endpoints → **Supabase Edge Functions**

### What Stayed the Same
1. **Frontend:** Next.js + TypeScript + Tailwind
2. **AI Agents:** FastAPI + Celery + LangChain + OpenAI
3. **Trading Logic:** Rules-based validation and risk management
4. **Business Model:** SaaS subscription tiers

### Why the Change
- **Simplicity:** Supabase eliminates ~60% of backend boilerplate
- **Cost:** Free tier supports MVP, ~$5-10/mo for 1000 users
- **Speed:** Auto-generated APIs accelerate development
- **Security:** Built-in RLS and auth best practices
- **Scalability:** Managed infrastructure scales automatically

---

## Using Archived Documentation

**When to reference archived docs:**
- Understanding original project vision
- Comparing old vs new architecture
- Learning about deprecated features
- Historical context for decisions

**When NOT to use archived docs:**
- Implementing new features (use current docs!)
- Setting up development environment
- Understanding current architecture
- Writing code

---

**Last Updated:** October 29, 2025
**Archive Curator:** Claude + umi1970

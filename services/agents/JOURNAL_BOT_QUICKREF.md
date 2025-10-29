# JournalBot Agent - Quick Reference

**AI-Powered Trading Report Generator**

Generates automated daily/weekly/monthly reports with AI insights in PDF and DOCX formats.

---

## Overview

**Purpose:** Create professional trading reports with AI-powered analysis
**Schedule:** Daily at 21:00 MEZ (end of trading day)
**File:** `services/agents/src/journal_bot.py`
**Output:** PDF + DOCX reports uploaded to Supabase Storage

---

## Report Sections

### 1. Performance Summary
- Total trades (wins/losses)
- Win rate percentage
- Total P&L
- Average R-multiple

### 2. AI-Powered Insights
- **Summary:** Overall performance overview (LangChain GPT-4)
- **Insights:** Key patterns and observations
- **Recommendations:** Actionable improvement suggestions

### 3. Trade Details
- Complete trade list table
- Entry/exit prices
- P&L color-coded (green/red)
- Strategy tags

### 4. Performance Metrics
- Charts and statistics
- Win/loss analysis
- Strategy performance breakdown

---

## Main Methods

### `__init__(supabase_client, openai_api_key)`
Initialize JournalBot with database and AI connections.

```python
from config.supabase import get_supabase_admin
from config import settings

bot = JournalBot(
    supabase_client=get_supabase_admin(),
    openai_api_key=settings.OPENAI_API_KEY
)
```

---

### `fetch_trades(user_id, date_range)`
Fetch trades for reporting period.

**Parameters:**
- `user_id`: UUID or None (None = all users)
- `date_range`: Tuple of (start_date, end_date) as datetime objects

**Returns:** List of trade records with symbol data

**Example:**
```python
from datetime import datetime, timedelta
import pytz

berlin_tz = pytz.timezone('Europe/Berlin')
today = datetime.now(berlin_tz).date()

date_range = (
    datetime.combine(today, datetime.min.time(), tzinfo=berlin_tz),
    datetime.combine(today, datetime.max.time(), tzinfo=berlin_tz)
)

trades = bot.fetch_trades(user_id=None, date_range=date_range)
# Returns: [{'id': ..., 'symbol_id': ..., 'pnl': 50.0, ...}, ...]
```

---

### `generate_ai_summary(trades_data)`
Generate AI-powered insights using LangChain + OpenAI GPT-4.

**Parameters:**
- `trades_data`: List of trade records

**Returns:** Dictionary with AI-generated content
```python
{
    'summary': 'Overall trading performance summary',
    'insights': 'Key patterns and observations',
    'recommendations': 'Actionable suggestions'
}
```

**Example:**
```python
trades = bot.fetch_trades()
ai_summary = bot.generate_ai_summary(trades)

print(ai_summary['summary'])
# "3 trades executed with 66.7% win rate and +60 total P&L"

print(ai_summary['insights'])
# "Strong performance on DAX trades. Asia sweep strategy showing best results."

print(ai_summary['recommendations'])
# "Continue using current strategies. Consider increasing position size..."
```

**AI Model:** GPT-4 (temperature: 0.7)
**Context:** Last 20 trades + performance metrics
**Fallback:** Returns basic summary if AI fails

---

### `create_docx_report(report_data, filename)`
Generate DOCX report using python-docx library.

**Parameters:**
- `report_data`: Dictionary with report content
- `filename`: Output filename (without .docx extension)

**Report Data Structure:**
```python
report_data = {
    'title': 'Daily Trading Report - 2025-10-29',
    'date': datetime.now().date(),
    'metrics': {
        'total_trades': 3,
        'winning_trades': 2,
        'losing_trades': 1,
        'win_rate': 66.7,
        'total_pnl': 60.0,
        'avg_r_multiple': 1.2
    },
    'ai_summary': {
        'summary': '...',
        'insights': '...',
        'recommendations': '...'
    },
    'trades': [...]  # List of trade records
}
```

**Returns:** Path to created DOCX file or None on error

**Example:**
```python
file_path = bot.create_docx_report(report_data, 'daily_report_20251029')
# Returns: '/tmp/daily_report_20251029.docx'
```

**Features:**
- Professional Arial font
- Colored P&L (green/red)
- Formatted tables
- Section headings
- TradeMatrix.ai branding

---

### `create_pdf_report(report_data, filename)`
Generate PDF report using reportlab library.

**Parameters:**
- `report_data`: Dictionary with report content (same as DOCX)
- `filename`: Output filename (without .pdf extension)

**Returns:** Path to created PDF file or None on error

**Example:**
```python
file_path = bot.create_pdf_report(report_data, 'daily_report_20251029')
# Returns: '/tmp/daily_report_20251029.pdf'
```

**Features:**
- A4 page size
- Professional typography
- Table formatting
- Color-coded metrics
- TradeMatrix.ai footer

---

### `upload_to_storage(file_path, bucket='reports')`
Upload report file to Supabase Storage.

**Parameters:**
- `file_path`: Local path to file (PDF or DOCX)
- `bucket`: Supabase storage bucket name (default: 'reports')

**Returns:** Public URL of uploaded file or None on error

**Storage Path:** `reports/{YYYY}/{MM}/{filename}`

**Example:**
```python
pdf_path = '/tmp/daily_report_20251029.pdf'
url = bot.upload_to_storage(pdf_path, bucket='reports')

# Returns: 'https://xxxxxx.supabase.co/storage/v1/object/public/reports/2025/10/daily_report_20251029.pdf'
```

**Access:** Public URL (no authentication required)

---

### `create_report_record(report_metadata)`
Save report metadata to 'reports' table in database.

**Parameters:**
- `report_metadata`: Dictionary with report details

**Metadata Structure:**
```python
report_metadata = {
    'user_id': UUID or None,
    'report_type': 'daily' | 'weekly' | 'monthly',
    'report_date': date.today(),
    'file_url_pdf': 'https://...',
    'file_url_docx': 'https://...',
    'metrics': {
        'total_trades': 3,
        'win_rate': 66.7,
        'total_pnl': 60.0,
        ...
    }
}
```

**Returns:** UUID of created report record or None on error

**Example:**
```python
report_id = bot.create_report_record(metadata)
# Returns: UUID('550e8400-e29b-41d4-a716-446655440000')
```

**Database Table:** `reports`
**User Access:** Filtered by RLS policies

---

### `generate_daily_report(user_id=None)`
Generate complete daily trading report.

**Main Workflow:**
1. Fetch today's trades from database
2. Calculate performance metrics
3. Generate AI summary using LangChain
4. Create PDF report
5. Create DOCX report
6. Upload both files to Supabase Storage
7. Save report metadata to database
8. Cleanup temporary files

**Parameters:**
- `user_id`: Optional user UUID (None = all users combined)

**Returns:** Dictionary with generation results

**Example:**
```python
result = bot.generate_daily_report(user_id=None)

print(result)
# {
#     'success': True,
#     'report_id': '550e8400-e29b-41d4-a716-446655440000',
#     'report_date': '2025-10-29',
#     'metrics': {
#         'total_trades': 3,
#         'winning_trades': 2,
#         'losing_trades': 1,
#         'win_rate': 66.7,
#         'total_pnl': 60.0,
#         'avg_r_multiple': 1.2
#     },
#     'pdf_url': 'https://...',
#     'docx_url': 'https://...',
#     'trades_analyzed': 3
# }
```

**Error Handling:** Returns `{'success': False, 'error': '...'}` on failure

---

### `run()`
Main execution method - called by Celery scheduler.

**Schedule:** Daily at 21:00 MEZ (Celery Beat)

**Process:**
1. Fetch all active users (future enhancement)
2. Generate daily report for each user
3. Return execution summary

**Returns:** Execution summary dictionary

**Example:**
```python
result = bot.run()

print(result)
# {
#     'execution_time': '2025-10-29T21:00:00Z',
#     'execution_duration_ms': 4523,
#     'reports_generated': 1,
#     'reports': [
#         {
#             'success': True,
#             'report_id': '...',
#             'metrics': {...},
#             'pdf_url': '...',
#             'docx_url': '...'
#         }
#     ]
# }
```

**Logging:** All operations logged to `logger` (INFO/ERROR levels)

---

## Celery Task Integration

**File:** `services/agents/src/tasks.py`

**Task Definition:**
```python
@celery.task(name='journal_bot_task', bind=True)
def journal_bot_task(self):
    """
    Generate automated trading reports (PDF/DOCX) with AI insights
    Runs daily at 21:00 MEZ (end of trading day)
    """
    logger.info("Starting JournalBot execution")

    try:
        bot = JournalBot(
            supabase_client=supabase_admin,
            openai_api_key=settings.OPENAI_API_KEY
        )

        result = bot.run()

        logger.info(f"JournalBot completed: {result['reports_generated']} reports generated")
        return result

    except Exception as e:
        logger.error(f"Error in journal_bot_task: {str(e)}")
        self.retry(exc=e, countdown=300, max_retries=3)
```

**Schedule Configuration:**
```python
celery.conf.beat_schedule = {
    'journal-bot': {
        'task': 'journal_bot_task',
        'schedule': crontab(hour=21, minute=0, day_of_week='0-4'),  # Mon-Fri
        'options': {
            'expires': 600.0,  # 10 minutes to complete
        }
    },
}
```

**Execution:** Automatic via Celery Beat at 21:00 MEZ daily (Mon-Fri)

---

## Database Tables

### `reports` Table (Metadata Storage)
```sql
CREATE TABLE reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id),
  report_type TEXT,  -- 'daily', 'weekly', 'monthly'
  report_date DATE,
  file_url_pdf TEXT,
  file_url_docx TEXT,
  metrics JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Note:** This table needs to be created via migration if not exists.

### `trades` Table (Source Data)
Existing table with trade records:
- `id`, `user_id`, `symbol_id`
- `entry_price`, `exit_price`, `pnl`
- `r_multiple`, `strategy`, `side`
- `created_at`

---

## Supabase Storage

**Bucket:** `reports`
**Access:** Public (read-only)
**Path Structure:** `reports/YYYY/MM/filename.{pdf|docx}`

**Setup:**
```sql
-- Create bucket (via Supabase Dashboard or SQL)
INSERT INTO storage.buckets (id, name, public)
VALUES ('reports', 'reports', true);

-- Set policies (allow public read)
CREATE POLICY "Public Access"
ON storage.objects FOR SELECT
USING (bucket_id = 'reports');
```

---

## Dependencies

**Python Libraries:**
```txt
# Document generation
python-docx==0.8.11
reportlab==4.0.7

# AI/ML (already in requirements.txt)
openai==1.10.0
langchain==0.1.4
langchain-openai==0.0.5
```

**Install:**
```bash
cd services/agents
pip install python-docx reportlab
```

---

## Testing

**Test File:** `services/agents/tests/test_journal_bot.py`

**Run All Tests:**
```bash
cd services/agents
pytest tests/test_journal_bot.py -v
```

**Run Specific Test:**
```bash
pytest tests/test_journal_bot.py::test_fetch_trades_success -v
```

**Test Coverage:**
- `test_fetch_trades_*` - Trades fetching
- `test_generate_ai_summary_*` - AI insights generation
- `test_create_docx_report_*` - DOCX creation
- `test_create_pdf_report_*` - PDF creation
- `test_upload_to_storage_*` - Supabase upload
- `test_create_report_record_*` - Database persistence
- `test_generate_daily_report_*` - Full workflow
- `test_run_*` - Celery execution

---

## Environment Variables

**Required in `.env`:**
```bash
# Supabase (already configured)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI (for AI summaries)
OPENAI_API_KEY=sk-...

# Celery (already configured)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Manual Execution

**For Testing:**
```python
# From services/agents directory
from src.journal_bot import JournalBot
from config.supabase import get_supabase_admin
from config import settings

# Initialize
bot = JournalBot(
    supabase_client=get_supabase_admin(),
    openai_api_key=settings.OPENAI_API_KEY
)

# Generate single report
result = bot.generate_daily_report(user_id=None)
print(result)

# Or run full execution
result = bot.run()
print(result)
```

**Trigger Celery Task Manually:**
```python
from tasks import journal_bot_task

# Trigger async
task = journal_bot_task.delay()
print(f"Task ID: {task.id}")

# Wait for result
result = task.get(timeout=300)
print(result)
```

---

## Example Output

### Daily Report Example

**Filename:** `daily_report_20251029.pdf` / `daily_report_20251029.docx`

**Content:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         Daily Trading Report
            2025-10-29
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Performance Summary
───────────────────
Total Trades:        3
Winning Trades:      2
Losing Trades:       1
Win Rate:            66.7%
Total P&L:           +60.00
Average R-Multiple:  1.2R

AI-Powered Insights
───────────────────
Summary:
3 trades executed with 66.7% win rate and +60 total P&L

Key Insights:
Strong performance on DAX trades. Asia sweep strategy
showing best results with 1.5R average. One losing trade
on ORB strategy indicates need for better entry timing.

Recommendations:
Continue using current strategies. Consider increasing
position size on high-confidence Asia sweep setups.
Review ORB entry criteria to reduce false breakouts.

Trade Details
─────────────
Time   Symbol  Side   Entry    Exit     P&L
08:15  DAX     LONG   19400.0  19450.0  +50.00
10:30  DAX     SHORT  19500.0  19480.0  +20.00
14:45  DAX     LONG   19420.0  19410.0  -10.00

Generated by TradeMatrix.ai JournalBot
```

---

## Troubleshooting

### Issue: "Module 'python-docx' not found"
**Solution:**
```bash
pip install python-docx
```

### Issue: "Module 'reportlab' not found"
**Solution:**
```bash
pip install reportlab
```

### Issue: "OpenAI API key not found"
**Solution:**
Add to `.env`:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### Issue: "Storage bucket 'reports' not found"
**Solution:**
Create bucket in Supabase Dashboard:
1. Go to Storage section
2. Click "New bucket"
3. Name: "reports"
4. Public: Yes
5. Create

### Issue: "Table 'reports' does not exist"
**Solution:**
Create migration:
```sql
-- In new migration file
CREATE TABLE reports (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id),
  report_type TEXT,
  report_date DATE,
  file_url_pdf TEXT,
  file_url_docx TEXT,
  metrics JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_date ON reports(report_date DESC);
```

### Issue: AI summary is generic/not helpful
**Solution:**
- Ensure OpenAI API key is valid and has credits
- Check LangChain prompt configuration
- Verify trades data has enough context (20+ trades recommended)

---

## Future Enhancements

**Planned Features:**
1. **Weekly Reports** - Aggregate 5 trading days
2. **Monthly Reports** - Comprehensive monthly review
3. **Per-User Reports** - Individual reports for each active user
4. **Email Delivery** - Send reports via email
5. **WhatsApp Integration** - Send to Expert tier users
6. **Chart Embedding** - Include TradingView charts in reports
7. **Custom Templates** - User-configurable report layouts
8. **Multi-Language** - German/English report generation

---

## Related Documentation

- [MORNING_PLANNER_QUICKREF.md](./MORNING_PLANNER_QUICKREF.md) - Morning trading setups
- [ALERT_ENGINE_QUICKREF.md](./ALERT_ENGINE_QUICKREF.md) - Real-time alerts
- [US_OPEN_PLANNER_QUICKREF.md](./US_OPEN_PLANNER_QUICKREF.md) - US session setups
- [README.md](./README.md) - Agents overview

---

**Last Updated:** 2025-10-29
**Version:** 1.0.0
**Status:** Production Ready

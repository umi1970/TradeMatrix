"""
JournalBot Agent Tests
======================

Tests for the JournalBot agent including:
- fetch_trades() - Fetch trades for reporting period
- generate_ai_summary() - LangChain AI insights generation
- create_docx_report() - DOCX report creation
- create_pdf_report() - PDF report creation
- upload_to_storage() - Supabase Storage upload
- create_report_record() - Report metadata persistence
- generate_daily_report() - Full daily report workflow
- run() - Main execution workflow

Run:
    pytest tests/test_journal_bot.py -v
    pytest tests/test_journal_bot.py::test_fetch_trades_success -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime, timedelta, date
from decimal import Decimal
from uuid import UUID, uuid4
import pytz
import os
import tempfile

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.journal_bot import JournalBot


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    return Mock()


@pytest.fixture
def mock_openai_key():
    """Mock OpenAI API key"""
    return "sk-test-key-123"


@pytest.fixture
def test_user_id():
    """Test user UUID"""
    return uuid4()


@pytest.fixture
def sample_trades():
    """Sample trades data"""
    symbol_id = uuid4()
    return [
        {
            'id': str(uuid4()),
            'user_id': str(uuid4()),
            'symbol_id': str(symbol_id),
            'side': 'long',
            'entry_price': 19400.0,
            'exit_price': 19450.0,
            'pnl': 50.0,
            'r_multiple': 1.5,
            'strategy': 'asia_sweep',
            'created_at': datetime.now(pytz.UTC).isoformat(),
            'market_symbols': {'symbol': 'DAX', 'alias': 'DAX 40'}
        },
        {
            'id': str(uuid4()),
            'user_id': str(uuid4()),
            'symbol_id': str(symbol_id),
            'side': 'short',
            'entry_price': 19500.0,
            'exit_price': 19480.0,
            'pnl': 20.0,
            'r_multiple': 0.8,
            'strategy': 'y_low_rebound',
            'created_at': datetime.now(pytz.UTC).isoformat(),
            'market_symbols': {'symbol': 'DAX', 'alias': 'DAX 40'}
        },
        {
            'id': str(uuid4()),
            'user_id': str(uuid4()),
            'symbol_id': str(symbol_id),
            'side': 'long',
            'entry_price': 19420.0,
            'exit_price': 19410.0,
            'pnl': -10.0,
            'r_multiple': -0.5,
            'strategy': 'orb',
            'created_at': datetime.now(pytz.UTC).isoformat(),
            'market_symbols': {'symbol': 'DAX', 'alias': 'DAX 40'}
        }
    ]


@pytest.mark.unit
@pytest.mark.agent
class TestJournalBotFetchTrades:
    """Tests for fetch_trades() method"""

    def test_fetch_trades_success(self, mock_supabase, mock_openai_key, test_user_id, sample_trades):
        """Test successful trades fetching"""
        # Mock Supabase response
        mock_result = Mock()
        mock_result.data = sample_trades

        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_result

        mock_supabase.table.return_value = mock_table

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        # Fetch trades
        today = datetime.now(pytz.timezone('Europe/Berlin')).date()
        date_range = (
            datetime.combine(today, datetime.min.time()),
            datetime.combine(today, datetime.max.time())
        )

        trades = bot.fetch_trades(user_id=test_user_id, date_range=date_range)

        assert len(trades) == 3
        assert all(isinstance(t, dict) for t in trades)
        assert 'pnl' in trades[0]
        assert 'market_symbols' in trades[0]

    def test_fetch_trades_no_user_filter(self, mock_supabase, mock_openai_key, sample_trades):
        """Test fetching trades without user filter (all users)"""
        mock_result = Mock()
        mock_result.data = sample_trades

        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_result

        mock_supabase.table.return_value = mock_table

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        trades = bot.fetch_trades(user_id=None)

        assert len(trades) == 3
        # Verify eq() was not called for user_id
        assert not any(call[0][0] == 'user_id' for call in mock_table.eq.call_args_list)

    def test_fetch_trades_empty_result(self, mock_supabase, mock_openai_key):
        """Test when no trades found"""
        mock_result = Mock()
        mock_result.data = []

        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_result

        mock_supabase.table.return_value = mock_table

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        trades = bot.fetch_trades()

        assert trades == []

    def test_fetch_trades_database_error(self, mock_supabase, mock_openai_key):
        """Test when database query fails"""
        mock_supabase.table.side_effect = Exception("Database connection error")

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        trades = bot.fetch_trades()

        assert trades == []


@pytest.mark.unit
@pytest.mark.agent
class TestJournalBotAISummary:
    """Tests for generate_ai_summary() method"""

    @patch('src.journal_bot.ChatOpenAI')
    def test_generate_ai_summary_success(self, mock_chat_openai, mock_supabase, mock_openai_key, sample_trades):
        """Test successful AI summary generation"""
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = """
        {
            "summary": "3 trades executed with 66.7% win rate and +60 total P&L",
            "insights": "Strong performance on DAX trades. Asia sweep strategy showing best results.",
            "recommendations": "Continue using current strategies. Consider increasing position size on high-confidence setups."
        }
        """

        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_llm_response
        mock_chat_openai.return_value = mock_llm_instance

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        summary = bot.generate_ai_summary(sample_trades)

        assert 'summary' in summary
        assert 'insights' in summary
        assert 'recommendations' in summary
        assert len(summary['summary']) > 0

    @patch('src.journal_bot.ChatOpenAI')
    def test_generate_ai_summary_llm_error(self, mock_chat_openai, mock_supabase, mock_openai_key, sample_trades):
        """Test AI summary generation when LLM fails"""
        mock_chat_openai.side_effect = Exception("OpenAI API error")

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        summary = bot.generate_ai_summary(sample_trades)

        # Should return fallback summary
        assert 'summary' in summary
        assert 'insights' in summary
        assert 'recommendations' in summary
        assert 'Unable to generate' in summary['insights']

    @patch('src.journal_bot.ChatOpenAI')
    def test_generate_ai_summary_empty_trades(self, mock_chat_openai, mock_supabase, mock_openai_key):
        """Test AI summary with no trades"""
        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        summary = bot.generate_ai_summary([])

        assert 'summary' in summary
        assert '0 trades' in summary['summary'] or 'Analyzed 0' in summary['summary']


@pytest.mark.unit
@pytest.mark.agent
class TestJournalBotReportCreation:
    """Tests for create_docx_report() and create_pdf_report() methods"""

    @patch('src.journal_bot.Document')
    def test_create_docx_report_success(self, mock_document, mock_supabase, mock_openai_key, sample_trades):
        """Test successful DOCX report creation"""
        mock_doc_instance = Mock()
        mock_document.return_value = mock_doc_instance

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        report_data = {
            'title': 'Daily Trading Report',
            'date': datetime.now().date(),
            'metrics': {
                'total_trades': 3,
                'winning_trades': 2,
                'losing_trades': 1,
                'win_rate': 66.7,
                'total_pnl': 60.0,
                'avg_r_multiple': 0.6
            },
            'ai_summary': {
                'summary': 'Good performance today',
                'insights': 'Strong Asia sweep execution',
                'recommendations': 'Continue monitoring'
            },
            'trades': sample_trades
        }

        file_path = bot.create_docx_report(report_data, 'test_report')

        assert file_path is not None
        assert file_path.endswith('.docx')
        assert 'test_report' in file_path

    @patch('src.journal_bot.SimpleDocTemplate')
    def test_create_pdf_report_success(self, mock_pdf_doc, mock_supabase, mock_openai_key, sample_trades):
        """Test successful PDF report creation"""
        mock_doc_instance = Mock()
        mock_pdf_doc.return_value = mock_doc_instance

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        report_data = {
            'title': 'Daily Trading Report',
            'date': datetime.now().date(),
            'metrics': {
                'total_trades': 3,
                'winning_trades': 2,
                'losing_trades': 1,
                'win_rate': 66.7,
                'total_pnl': 60.0,
                'avg_r_multiple': 0.6
            },
            'ai_summary': {
                'summary': 'Good performance today',
                'insights': 'Strong Asia sweep execution',
                'recommendations': 'Continue monitoring'
            },
            'trades': sample_trades
        }

        file_path = bot.create_pdf_report(report_data, 'test_report')

        assert file_path is not None
        assert file_path.endswith('.pdf')
        assert 'test_report' in file_path


@pytest.mark.unit
@pytest.mark.agent
class TestJournalBotStorage:
    """Tests for upload_to_storage() method"""

    def test_upload_to_storage_success(self, mock_supabase, mock_openai_key):
        """Test successful file upload to Supabase Storage"""
        # Mock storage upload
        mock_storage = Mock()
        mock_bucket = Mock()
        mock_bucket.upload.return_value = {'path': 'reports/2025/10/test_report.pdf'}
        mock_bucket.get_public_url.return_value = 'https://storage.supabase.co/reports/test_report.pdf'
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf') as f:
            f.write('Test PDF content')
            temp_file = f.name

        try:
            url = bot.upload_to_storage(temp_file, bucket='reports')

            assert url is not None
            assert url.startswith('https://')
            assert 'storage.supabase.co' in url
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_upload_to_storage_file_not_found(self, mock_supabase, mock_openai_key):
        """Test upload when file doesn't exist"""
        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        url = bot.upload_to_storage('/nonexistent/file.pdf')

        assert url is None

    def test_upload_to_storage_api_error(self, mock_supabase, mock_openai_key):
        """Test upload when Supabase API fails"""
        mock_storage = Mock()
        mock_storage.from_.side_effect = Exception("Storage API error")
        mock_supabase.storage = mock_storage

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pdf') as f:
            f.write('Test content')
            temp_file = f.name

        try:
            url = bot.upload_to_storage(temp_file)

            assert url is None
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)


@pytest.mark.unit
@pytest.mark.agent
class TestJournalBotReportRecord:
    """Tests for create_report_record() method"""

    def test_create_report_record_success(self, mock_supabase, mock_openai_key, test_user_id):
        """Test successful report record creation"""
        report_id = uuid4()

        mock_result = Mock()
        mock_result.data = [{'id': str(report_id)}]

        mock_table = Mock()
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_result

        mock_supabase.table.return_value = mock_table

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        metadata = {
            'user_id': test_user_id,
            'report_type': 'daily',
            'report_date': date.today(),
            'file_url_pdf': 'https://storage.supabase.co/reports/test.pdf',
            'file_url_docx': 'https://storage.supabase.co/reports/test.docx',
            'metrics': {'total_trades': 3, 'win_rate': 66.7}
        }

        created_id = bot.create_report_record(metadata)

        assert created_id is not None
        assert isinstance(created_id, UUID)
        assert created_id == report_id

    def test_create_report_record_database_error(self, mock_supabase, mock_openai_key):
        """Test report record creation when database insert fails"""
        mock_result = Mock()
        mock_result.data = []  # Empty data = failure

        mock_table = Mock()
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_result

        mock_supabase.table.return_value = mock_table

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        metadata = {
            'report_type': 'daily',
            'report_date': date.today(),
            'metrics': {}
        }

        created_id = bot.create_report_record(metadata)

        assert created_id is None


@pytest.mark.unit
@pytest.mark.agent
class TestJournalBotGenerateDailyReport:
    """Tests for generate_daily_report() method"""

    @patch('src.journal_bot.ChatOpenAI')
    @patch('src.journal_bot.Document')
    @patch('src.journal_bot.SimpleDocTemplate')
    def test_generate_daily_report_success(
        self,
        mock_pdf_doc,
        mock_docx_doc,
        mock_chat_openai,
        mock_supabase,
        mock_openai_key,
        sample_trades
    ):
        """Test successful daily report generation"""
        # Mock fetch_trades
        mock_trades_result = Mock()
        mock_trades_result.data = sample_trades

        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = mock_trades_result

        mock_supabase.table.return_value = mock_table

        # Mock storage
        mock_storage = Mock()
        mock_bucket = Mock()
        mock_bucket.upload.return_value = {'path': 'reports/test.pdf'}
        mock_bucket.get_public_url.return_value = 'https://storage.supabase.co/reports/test.pdf'
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage

        # Mock LLM
        mock_llm_response = Mock()
        mock_llm_response.content = "AI summary content"
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_llm_response
        mock_chat_openai.return_value = mock_llm_instance

        # Mock document creation
        mock_docx_instance = Mock()
        mock_docx_doc.return_value = mock_docx_instance

        mock_pdf_instance = Mock()
        mock_pdf_doc.return_value = mock_pdf_instance

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        result = bot.generate_daily_report()

        assert result['success'] is True
        assert 'metrics' in result
        assert result['metrics']['total_trades'] == 3
        assert result['metrics']['winning_trades'] == 2
        assert result['metrics']['losing_trades'] == 1

    @patch('src.journal_bot.ChatOpenAI')
    def test_generate_daily_report_no_trades(self, mock_chat_openai, mock_supabase, mock_openai_key):
        """Test daily report generation with no trades"""
        # Mock empty trades
        mock_result = Mock()
        mock_result.data = []

        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = mock_result

        mock_supabase.table.return_value = mock_table

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        result = bot.generate_daily_report()

        # Should still succeed with 0 trades
        assert 'metrics' in result
        assert result['metrics']['total_trades'] == 0


@pytest.mark.unit
@pytest.mark.agent
class TestJournalBotRun:
    """Tests for run() method - main execution"""

    @patch.object(JournalBot, 'generate_daily_report')
    def test_run_success(self, mock_generate_report, mock_supabase, mock_openai_key):
        """Test successful run execution"""
        mock_generate_report.return_value = {
            'success': True,
            'report_id': str(uuid4()),
            'metrics': {'total_trades': 5}
        }

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        result = bot.run()

        assert 'execution_time' in result
        assert 'reports_generated' in result
        assert result['reports_generated'] == 1
        assert len(result['reports']) == 1

    @patch.object(JournalBot, 'generate_daily_report')
    def test_run_handles_exceptions(self, mock_generate_report, mock_supabase, mock_openai_key):
        """Test run handles exceptions gracefully"""
        mock_generate_report.side_effect = Exception("Report generation error")

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        result = bot.run()

        assert 'error' in result
        assert result['reports_generated'] == 0


@pytest.mark.integration
@pytest.mark.agent
class TestJournalBotIntegration:
    """Integration tests for complete workflows"""

    @patch('src.journal_bot.ChatOpenAI')
    @patch('src.journal_bot.Document')
    @patch('src.journal_bot.SimpleDocTemplate')
    def test_complete_daily_report_workflow(
        self,
        mock_pdf_doc,
        mock_docx_doc,
        mock_chat_openai,
        mock_supabase,
        mock_openai_key,
        sample_trades
    ):
        """Test complete daily report workflow from start to finish"""
        # Setup mocks for entire workflow
        report_id = uuid4()

        # Mock trades fetch
        mock_trades_result = Mock()
        mock_trades_result.data = sample_trades

        # Mock report record insert
        mock_insert_result = Mock()
        mock_insert_result.data = [{'id': str(report_id)}]

        def mock_execute():
            # Return trades for first call, report record for second
            if hasattr(mock_execute, 'call_count'):
                mock_execute.call_count += 1
                return mock_insert_result
            else:
                mock_execute.call_count = 1
                return mock_trades_result

        mock_table = Mock()
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.lte.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.insert.return_value = mock_table
        mock_table.execute = mock_execute

        mock_supabase.table.return_value = mock_table

        # Mock storage
        mock_storage = Mock()
        mock_bucket = Mock()
        mock_bucket.upload.return_value = {'path': 'reports/test.pdf'}
        mock_bucket.get_public_url.return_value = 'https://storage.supabase.co/reports/test.pdf'
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage

        # Mock LLM
        mock_llm_response = Mock()
        mock_llm_response.content = "Comprehensive AI analysis"
        mock_llm_instance = Mock()
        mock_llm_instance.invoke.return_value = mock_llm_response
        mock_chat_openai.return_value = mock_llm_instance

        # Mock document creation
        mock_docx_instance = Mock()
        mock_docx_doc.return_value = mock_docx_instance

        mock_pdf_instance = Mock()
        mock_pdf_doc.return_value = mock_pdf_instance

        bot = JournalBot(supabase_client=mock_supabase, openai_api_key=mock_openai_key)

        # Execute complete workflow
        result = bot.run()

        # Verify workflow completed successfully
        assert 'execution_time' in result
        assert 'reports_generated' in result
        assert isinstance(result['reports'], list)

"""
Test Suite for Risk Calculator

Tests all risk management calculations including:
- Position sizing
- 1% risk rule
- R-Multiple calculations
- KO-product calculations
- Break-even logic
- Trade validation

Author: TradeMatrix.ai
Date: 2025-10-29
"""

import pytest
from risk_calculator import RiskCalculator


class TestRiskCalculatorInit:
    """Test RiskCalculator initialization."""

    def test_init_default_risk(self):
        """Test initialization with default 1% risk."""
        calc = RiskCalculator(account_balance=10000)
        assert calc.account_balance == 10000
        assert calc.risk_per_trade == 0.01
        assert calc.max_risk_amount == 100.0

    def test_init_custom_risk(self):
        """Test initialization with custom risk percentage."""
        calc = RiskCalculator(account_balance=10000, risk_per_trade=0.02)
        assert calc.risk_per_trade == 0.02
        assert calc.max_risk_amount == 200.0

    def test_init_invalid_balance(self):
        """Test that negative balance raises error."""
        with pytest.raises(ValueError, match="Account balance must be positive"):
            RiskCalculator(account_balance=-1000)

    def test_init_zero_balance(self):
        """Test that zero balance raises error."""
        with pytest.raises(ValueError, match="Account balance must be positive"):
            RiskCalculator(account_balance=0)

    def test_init_invalid_risk_percentage(self):
        """Test that invalid risk percentage raises error."""
        with pytest.raises(ValueError, match="Risk per trade must be between"):
            RiskCalculator(account_balance=10000, risk_per_trade=0.0)

        with pytest.raises(ValueError, match="Risk per trade must be between"):
            RiskCalculator(account_balance=10000, risk_per_trade=0.15)


class TestPositionSizing:
    """Test position sizing calculations."""

    def setup_method(self):
        """Setup test calculator with 10,000 EUR account."""
        self.calc = RiskCalculator(account_balance=10000, risk_per_trade=0.01)

    def test_position_size_long_trade(self):
        """Test position sizing for long trade."""
        result = self.calc.calculate_position_size(
            entry=19500.0,
            stop_loss=19450.0
        )

        # Risk amount = 10000 * 0.01 = 100 EUR
        # Risk per unit = 19500 - 19450 = 50 EUR
        # Position size = 100 / 50 = 2.0 units
        assert result['position_size'] == 2.0
        assert result['risk_amount'] == 100.0
        assert result['risk_per_unit'] == 50.0
        assert result['risk_percentage'] == 1.0

    def test_position_size_short_trade(self):
        """Test position sizing for short trade."""
        result = self.calc.calculate_position_size(
            entry=18000.0,
            stop_loss=18100.0
        )

        # Risk per unit = 18100 - 18000 = 100 EUR
        # Position size = 100 / 100 = 1.0 units
        assert result['position_size'] == 1.0
        assert result['risk_amount'] == 100.0
        assert result['risk_per_unit'] == 100.0

    def test_position_size_custom_risk(self):
        """Test position sizing with custom risk amount."""
        result = self.calc.calculate_position_size(
            entry=19500.0,
            stop_loss=19450.0,
            risk_amount=50.0
        )

        # Position size = 50 / 50 = 1.0 units
        assert result['position_size'] == 1.0
        assert result['risk_amount'] == 50.0

    def test_position_size_invalid_entry(self):
        """Test that invalid entry raises error."""
        with pytest.raises(ValueError, match="Entry and stop loss must be positive"):
            self.calc.calculate_position_size(entry=-100, stop_loss=50)

    def test_position_size_equal_entry_sl(self):
        """Test that entry == stop loss raises error."""
        with pytest.raises(ValueError, match="Entry and stop loss cannot be equal"):
            self.calc.calculate_position_size(entry=19500, stop_loss=19500)


class TestStopLossCalculation:
    """Test stop loss calculations."""

    def setup_method(self):
        """Setup test calculator."""
        self.calc = RiskCalculator(account_balance=10000)

    def test_stop_loss_long_default(self):
        """Test stop loss calculation for long trade with default 0.25% risk."""
        result = self.calc.calculate_stop_loss(entry=19500.0)

        # Distance = 19500 * 0.0025 = 48.75
        # SL = 19500 - 48.75 = 19451.25
        assert result['stop_loss'] == 19451.25
        assert result['distance'] == 48.75
        assert result['distance_percentage'] == 0.25
        assert result['direction'] == 'long'

    def test_stop_loss_short_default(self):
        """Test stop loss calculation for short trade."""
        result = self.calc.calculate_stop_loss(
            entry=18000.0,
            direction='short'
        )

        # Distance = 18000 * 0.0025 = 45.0
        # SL = 18000 + 45.0 = 18045.0
        assert result['stop_loss'] == 18045.0
        assert result['distance'] == 45.0
        assert result['direction'] == 'short'

    def test_stop_loss_custom_percentage(self):
        """Test stop loss with custom risk percentage."""
        result = self.calc.calculate_stop_loss(
            entry=19500.0,
            risk_percentage=0.005  # 0.5%
        )

        # Distance = 19500 * 0.005 = 97.5
        assert result['distance'] == 97.5
        assert result['stop_loss'] == 19402.5

    def test_stop_loss_invalid_entry(self):
        """Test that invalid entry raises error."""
        with pytest.raises(ValueError, match="Entry must be positive"):
            self.calc.calculate_stop_loss(entry=-100)


class TestTakeProfitCalculation:
    """Test take profit / R-Multiple calculations."""

    def setup_method(self):
        """Setup test calculator."""
        self.calc = RiskCalculator(account_balance=10000)

    def test_take_profit_long_2r(self):
        """Test take profit for long trade at 2R."""
        result = self.calc.calculate_take_profit(
            entry=19500.0,
            stop_loss=19450.0,
            risk_reward_ratio=2.0
        )

        # 1R = 19500 - 19450 = 50
        # TP = 19500 + (2 * 50) = 19600
        assert result['one_r'] == 50.0
        assert result['take_profit'] == 19600.0
        assert result['profit_distance'] == 100.0
        assert result['risk_reward_ratio'] == 2.0
        assert result['direction'] == 'long'

    def test_take_profit_short_2r(self):
        """Test take profit for short trade at 2R."""
        result = self.calc.calculate_take_profit(
            entry=18000.0,
            stop_loss=18100.0,
            risk_reward_ratio=2.0
        )

        # 1R = 18100 - 18000 = 100
        # TP = 18000 - (2 * 100) = 17800
        assert result['one_r'] == 100.0
        assert result['take_profit'] == 17800.0
        assert result['direction'] == 'short'

    def test_take_profit_3r(self):
        """Test take profit at 3R."""
        result = self.calc.calculate_take_profit(
            entry=19500.0,
            stop_loss=19450.0,
            risk_reward_ratio=3.0
        )

        # TP = 19500 + (3 * 50) = 19650
        assert result['take_profit'] == 19650.0
        assert result['risk_reward_ratio'] == 3.0

    def test_take_profit_invalid_rr_ratio(self):
        """Test that negative RR ratio raises error."""
        with pytest.raises(ValueError, match="Risk-reward ratio must be positive"):
            self.calc.calculate_take_profit(
                entry=19500,
                stop_loss=19450,
                risk_reward_ratio=-1.0
            )


class TestLeverageCalculation:
    """Test leverage calculations."""

    def setup_method(self):
        """Setup test calculator."""
        self.calc = RiskCalculator(account_balance=10000)

    def test_leverage_cfd(self):
        """Test leverage for CFD product."""
        result = self.calc.calculate_leverage(
            position_size=50000.0,  # Position value
            product_type='CFD'
        )

        # Leverage = 50000 / 10000 = 5x
        assert result['leverage'] == 5.0
        assert result['product_type'] == 'CFD'
        assert result['max_allowed_leverage'] == 30.0
        assert result['is_safe'] is True

    def test_leverage_ko(self):
        """Test leverage for KO product."""
        result = self.calc.calculate_leverage(
            position_size=50000.0,
            product_type='KO'
        )

        # Leverage = 5x, max for KO = 10x
        assert result['leverage'] == 5.0
        assert result['max_allowed_leverage'] == 10.0
        assert result['is_safe'] is True

    def test_leverage_too_high(self):
        """Test that excessive leverage is flagged."""
        result = self.calc.calculate_leverage(
            position_size=350000.0,  # 35x leverage
            product_type='CFD'
        )

        assert result['leverage'] == 35.0
        assert result['is_safe'] is False

    def test_leverage_invalid_position_size(self):
        """Test that negative position size raises error."""
        with pytest.raises(ValueError, match="Position size must be positive"):
            self.calc.calculate_leverage(position_size=-1000)


class TestKOProductCalculation:
    """Test KO (Knock-Out) product calculations."""

    def setup_method(self):
        """Setup test calculator."""
        self.calc = RiskCalculator(account_balance=10000)

    def test_ko_long_trade(self):
        """Test KO threshold for long trade."""
        result = self.calc.calculate_ko_product(
            entry=19500.0,
            stop_loss=19450.0,
            direction='long',
            safety_buffer=0.005  # 0.5%
        )

        # KO = 19450 * (1 - 0.005) = 19450 * 0.995 = 19352.75
        assert result['ko_threshold'] == 19352.75
        assert result['entry'] == 19500.0
        assert result['stop_loss'] == 19450.0
        assert result['direction'] == 'long'

        # Leverage = 19500 / (19500 - 19352.75) = 19500 / 147.25 ≈ 132.43
        assert result['leverage'] > 100

    def test_ko_short_trade(self):
        """Test KO threshold for short trade."""
        result = self.calc.calculate_ko_product(
            entry=18000.0,
            stop_loss=18100.0,
            direction='short',
            safety_buffer=0.005
        )

        # KO = 18100 * (1 + 0.005) = 18100 * 1.005 = 18190.5
        assert result['ko_threshold'] == 18190.5
        assert result['direction'] == 'short'

    def test_ko_high_leverage_warning(self):
        """Test that high leverage triggers warning."""
        result = self.calc.calculate_ko_product(
            entry=19500.0,
            stop_loss=19490.0,  # Very tight stop
            direction='long'
        )

        # Should have leverage warning
        assert len(result['warnings']) > 0
        assert any('leverage' in w.lower() for w in result['warnings'])

    def test_ko_invalid_prices(self):
        """Test that invalid prices raise error."""
        with pytest.raises(ValueError, match="Entry and stop loss must be positive"):
            self.calc.calculate_ko_product(
                entry=-100,
                stop_loss=50,
                direction='long'
            )


class TestBreakEvenCalculation:
    """Test break-even calculations."""

    def setup_method(self):
        """Setup test calculator."""
        self.calc = RiskCalculator(account_balance=10000)

    def test_break_even_no_commission(self):
        """Test break-even with no commission."""
        result = self.calc.calculate_break_even(entry=19500.0)

        # No commission = break-even at entry
        assert result['break_even_price'] == 19500.0
        assert result['commission_cost'] == 0.0
        assert result['total_cost'] == 0.0

    def test_break_even_with_commission(self):
        """Test break-even with commission."""
        result = self.calc.calculate_break_even(
            entry=19500.0,
            commission_percentage=0.001  # 0.1%
        )

        # Commission = 19500 * 0.001 = 19.5
        # Total commission (entry + exit) = 2 * 19.5 = 39.0
        # Break-even = 19500 + 39 = 19539.0
        assert result['commission_cost'] == 39.0
        assert result['break_even_price'] == 19539.0

    def test_break_even_with_spread(self):
        """Test break-even with spread."""
        result = self.calc.calculate_break_even(
            entry=19500.0,
            spread=5.0
        )

        # Break-even = 19500 + 5 = 19505.0
        assert result['break_even_price'] == 19505.0
        assert result['spread'] == 5.0

    def test_break_even_commission_and_spread(self):
        """Test break-even with both commission and spread."""
        result = self.calc.calculate_break_even(
            entry=19500.0,
            commission_percentage=0.001,
            spread=5.0
        )

        # Total cost = 39.0 (commission) + 5.0 (spread) = 44.0
        assert result['total_cost'] == 44.0
        assert result['break_even_price'] == 19544.0


class TestTradeValidation:
    """Test trade risk validation."""

    def setup_method(self):
        """Setup test calculator."""
        self.calc = RiskCalculator(account_balance=10000, risk_per_trade=0.01)

    def test_validate_valid_trade(self):
        """Test validation of valid trade."""
        result = self.calc.validate_trade_risk(
            entry=19500.0,
            stop_loss=19450.0,
            position_size=2.0
        )

        # Risk = 2.0 * 50 = 100 EUR = 1%
        assert result['is_valid'] is True
        assert result['risk_amount'] == 100.0
        assert result['risk_percentage'] == 1.0
        assert len(result['warnings']) == 0

    def test_validate_excessive_risk(self):
        """Test validation flags excessive risk."""
        result = self.calc.validate_trade_risk(
            entry=19500.0,
            stop_loss=19450.0,
            position_size=5.0  # 5 * 50 = 250 EUR = 2.5%
        )

        assert result['is_valid'] is False
        assert result['risk_amount'] == 250.0
        assert result['risk_percentage'] == 2.5
        assert any('exceeds max allowed' in w for w in result['warnings'])

    def test_validate_high_leverage(self):
        """Test validation flags high leverage."""
        result = self.calc.validate_trade_risk(
            entry=19500.0,
            stop_loss=19450.0,
            position_size=0.2  # Small position but high price
        )

        # Position value = 0.2 * 19500 = 3900
        # Leverage = 3900 / 10000 = 0.39x (safe)
        assert result['leverage'] < 1.0
        assert result['is_valid'] is True

    def test_validate_invalid_prices(self):
        """Test validation with invalid prices."""
        result = self.calc.validate_trade_risk(
            entry=-100,
            stop_loss=50,
            position_size=1.0
        )

        assert result['is_valid'] is False
        assert any('must be positive' in w for w in result['warnings'])

    def test_validate_equal_entry_sl(self):
        """Test validation with entry == stop loss."""
        result = self.calc.validate_trade_risk(
            entry=19500,
            stop_loss=19500,
            position_size=1.0
        )

        assert result['is_valid'] is False
        assert any('cannot be equal' in w for w in result['warnings'])


class TestBreakEvenLogic:
    """Test break-even move logic."""

    def setup_method(self):
        """Setup test calculator."""
        self.calc = RiskCalculator(account_balance=10000)

    def test_should_move_to_break_even_yes(self):
        """Test that +0.5R triggers break-even move."""
        result = self.calc.should_move_to_break_even(
            entry=19500.0,
            current_price=19525.0,  # +25 EUR = +0.5R
            stop_loss=19450.0
        )

        # 1R = 50, current profit = 25 = 0.5R
        assert result['current_r'] == 0.5
        assert result['should_move'] is True
        assert result['new_stop_loss'] == 19500.0
        assert 'break-even' in result['reason'].lower()

    def test_should_move_to_break_even_no(self):
        """Test that below threshold doesn't trigger move."""
        result = self.calc.should_move_to_break_even(
            entry=19500.0,
            current_price=19510.0,  # +10 EUR = +0.2R
            stop_loss=19450.0
        )

        # Current profit = 0.2R (below 0.5R threshold)
        assert result['current_r'] == 0.2
        assert result['should_move'] is False
        assert result['new_stop_loss'] == 19450.0

    def test_should_move_short_trade(self):
        """Test break-even logic for short trade."""
        result = self.calc.should_move_to_break_even(
            entry=18000.0,
            current_price=17950.0,  # -50 EUR profit (short)
            stop_loss=18100.0
        )

        # 1R = 100, profit = 50 = 0.5R
        assert result['current_r'] == 0.5
        assert result['should_move'] is True
        assert result['direction'] == 'short'

    def test_should_move_above_threshold(self):
        """Test move at +1R (well above threshold)."""
        result = self.calc.should_move_to_break_even(
            entry=19500.0,
            current_price=19550.0,  # +50 EUR = +1R
            stop_loss=19450.0
        )

        assert result['current_r'] == 1.0
        assert result['should_move'] is True


class TestFullTradePlan:
    """Test complete trade plan generation."""

    def setup_method(self):
        """Setup test calculator."""
        self.calc = RiskCalculator(account_balance=10000)

    def test_full_trade_plan_long_cfd(self):
        """Test complete trade plan for long CFD trade."""
        plan = self.calc.calculate_full_trade_plan(
            entry=19500.0,
            stop_loss=19450.0,
            direction='long',
            risk_reward_ratio=2.0,
            product_type='CFD'
        )

        assert plan['entry'] == 19500.0
        assert plan['stop_loss'] == 19450.0
        assert plan['take_profit'] == 19600.0
        assert plan['direction'] == 'long'
        assert plan['position_size'] == 2.0
        assert plan['risk_amount'] == 100.0
        assert plan['one_r'] == 50.0
        assert plan['risk_reward_ratio'] == 2.0
        assert plan['product_type'] == 'CFD'
        assert plan['is_valid'] is True

    def test_full_trade_plan_short_ko(self):
        """Test complete trade plan for short KO trade."""
        plan = self.calc.calculate_full_trade_plan(
            entry=18000.0,
            stop_loss=18100.0,
            direction='short',
            risk_reward_ratio=2.0,
            product_type='KO'
        )

        assert plan['direction'] == 'short'
        assert plan['take_profit'] == 17800.0
        assert plan['product_type'] == 'KO'
        assert plan['ko_data'] is not None
        assert plan['ko_data']['ko_threshold'] > plan['stop_loss']

    def test_full_trade_plan_with_commission(self):
        """Test trade plan includes commission costs."""
        plan = self.calc.calculate_full_trade_plan(
            entry=19500.0,
            stop_loss=19450.0,
            direction='long',
            commission_percentage=0.001
        )

        # Break-even should include commission
        assert plan['break_even_price'] > plan['entry']

    def test_full_trade_plan_3r(self):
        """Test trade plan with 3R target."""
        plan = self.calc.calculate_full_trade_plan(
            entry=19500.0,
            stop_loss=19450.0,
            direction='long',
            risk_reward_ratio=3.0
        )

        # TP = 19500 + (3 * 50) = 19650
        assert plan['take_profit'] == 19650.0
        assert plan['risk_reward_ratio'] == 3.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Setup test calculator."""
        self.calc = RiskCalculator(account_balance=10000)

    def test_very_small_position(self):
        """Test with very small position size."""
        result = self.calc.calculate_position_size(
            entry=19500.0,
            stop_loss=19000.0,  # Large stop = small position
            risk_amount=10.0
        )

        # Risk per unit = 500, position = 10/500 = 0.02
        assert result['position_size'] == 0.02

    def test_very_tight_stop(self):
        """Test with very tight stop loss."""
        result = self.calc.calculate_position_size(
            entry=19500.0,
            stop_loss=19499.0,  # 1 EUR stop
            risk_amount=100.0
        )

        # Position = 100 / 1 = 100 units
        assert result['position_size'] == 100.0

    def test_large_account_balance(self):
        """Test with large account balance."""
        calc = RiskCalculator(account_balance=1000000)
        result = calc.calculate_position_size(
            entry=19500.0,
            stop_loss=19450.0
        )

        # Max risk = 1M * 0.01 = 10,000
        # Position = 10,000 / 50 = 200 units
        assert result['position_size'] == 200.0
        assert result['risk_amount'] == 10000.0

    def test_fractional_prices(self):
        """Test with fractional prices (Forex-like)."""
        result = self.calc.calculate_position_size(
            entry=1.0850,
            stop_loss=1.0800
        )

        # Risk per unit = 0.005
        # Position = 100 / 0.005 = 20,000
        assert result['position_size'] == 20000.0


def run_all_tests():
    """Run all tests and print summary."""
    import sys

    print("Running Risk Calculator Test Suite...")
    print("=" * 60)

    # Run pytest
    exit_code = pytest.main([__file__, '-v', '--tb=short'])

    return exit_code


if __name__ == "__main__":
    exit_code = run_all_tests()
    exit(exit_code)

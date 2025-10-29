"""
Manual test runner for Risk Calculator (without pytest dependency)

Runs all test cases and reports results.
"""

from risk_calculator import RiskCalculator


def run_test(test_name, test_func):
    """Run a single test and report result."""
    try:
        test_func()
        print(f"✓ {test_name}")
        return True
    except AssertionError as e:
        print(f"✗ {test_name}: {str(e)}")
        return False
    except Exception as e:
        print(f"✗ {test_name}: ERROR - {str(e)}")
        return False


def test_init_default():
    """Test initialization with default risk."""
    calc = RiskCalculator(account_balance=10000)
    assert calc.account_balance == 10000
    assert calc.risk_per_trade == 0.01
    assert calc.max_risk_amount == 100.0


def test_init_custom_risk():
    """Test initialization with custom risk."""
    calc = RiskCalculator(account_balance=10000, risk_per_trade=0.02)
    assert calc.risk_per_trade == 0.02
    assert calc.max_risk_amount == 200.0


def test_position_size_long():
    """Test position sizing for long trade."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.calculate_position_size(entry=19500.0, stop_loss=19450.0)
    assert result['position_size'] == 2.0
    assert result['risk_amount'] == 100.0
    assert result['risk_per_unit'] == 50.0


def test_position_size_short():
    """Test position sizing for short trade."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.calculate_position_size(entry=18000.0, stop_loss=18100.0)
    assert result['position_size'] == 1.0
    assert result['risk_per_unit'] == 100.0


def test_stop_loss_long():
    """Test stop loss calculation for long."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.calculate_stop_loss(entry=19500.0)
    assert result['stop_loss'] == 19451.25
    assert result['distance'] == 48.75


def test_take_profit_2r():
    """Test take profit at 2R."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.calculate_take_profit(entry=19500.0, stop_loss=19450.0, risk_reward_ratio=2.0)
    assert result['one_r'] == 50.0
    assert result['take_profit'] == 19600.0
    assert result['direction'] == 'long'


def test_leverage_calculation():
    """Test leverage calculation."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.calculate_leverage(position_size=50000.0, product_type='CFD')
    assert result['leverage'] == 5.0
    assert result['is_safe'] is True


def test_ko_long():
    """Test KO threshold for long."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.calculate_ko_product(entry=19500.0, stop_loss=19450.0, direction='long', safety_buffer=0.005)
    assert result['ko_threshold'] == 19352.75


def test_break_even_no_commission():
    """Test break-even with no commission."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.calculate_break_even(entry=19500.0)
    assert result['break_even_price'] == 19500.0


def test_break_even_with_commission():
    """Test break-even with commission."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.calculate_break_even(entry=19500.0, commission_percentage=0.001)
    assert result['commission_cost'] == 39.0
    assert result['break_even_price'] == 19539.0


def test_validate_valid_trade():
    """Test validation of valid trade."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.validate_trade_risk(entry=19500.0, stop_loss=19450.0, position_size=2.0)
    assert result['is_valid'] is True
    assert result['risk_amount'] == 100.0
    assert result['risk_percentage'] == 1.0


def test_validate_excessive_risk():
    """Test validation flags excessive risk."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.validate_trade_risk(entry=19500.0, stop_loss=19450.0, position_size=5.0)
    assert result['is_valid'] is False
    assert result['risk_amount'] == 250.0


def test_should_move_be_yes():
    """Test break-even move at +0.5R."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.should_move_to_break_even(entry=19500.0, current_price=19525.0, stop_loss=19450.0)
    assert result['current_r'] == 0.5
    assert result['should_move'] is True


def test_should_move_be_no():
    """Test no move below threshold."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.should_move_to_break_even(entry=19500.0, current_price=19510.0, stop_loss=19450.0)
    assert result['current_r'] == 0.2
    assert result['should_move'] is False


def test_full_trade_plan_long():
    """Test complete trade plan."""
    calc = RiskCalculator(account_balance=10000)
    plan = calc.calculate_full_trade_plan(
        entry=19500.0,
        stop_loss=19450.0,
        direction='long',
        risk_reward_ratio=2.0,
        product_type='CFD'
    )
    assert plan['entry'] == 19500.0
    assert plan['take_profit'] == 19600.0
    assert plan['position_size'] == 2.0
    assert plan['is_valid'] is True


def test_1_percent_rule():
    """Test 1% risk rule enforcement."""
    calc = RiskCalculator(account_balance=10000, risk_per_trade=0.01)

    # Valid: exactly 1% risk
    result = calc.calculate_position_size(entry=19500.0, stop_loss=19450.0)
    assert result['risk_amount'] == 100.0  # 1% of 10,000

    # Validation should pass
    validation = calc.validate_trade_risk(
        entry=19500.0,
        stop_loss=19450.0,
        position_size=result['position_size']
    )
    assert validation['is_valid'] is True


def test_ko_leverage():
    """Test KO product leverage calculation."""
    calc = RiskCalculator(account_balance=10000)
    result = calc.calculate_ko_product(
        entry=19500.0,
        stop_loss=19450.0,
        direction='long',
        safety_buffer=0.005
    )
    # KO leverage should be calculated
    assert result['leverage'] > 0
    assert 'ko_threshold' in result


def test_r_multiple_calculation():
    """Test R-multiple calculations."""
    calc = RiskCalculator(account_balance=10000)

    # 1R = 50 EUR
    result = calc.calculate_take_profit(entry=19500.0, stop_loss=19450.0, risk_reward_ratio=2.0)
    assert result['one_r'] == 50.0

    # 2R profit = 100 EUR
    assert result['profit_distance'] == 100.0

    # 3R target
    result_3r = calc.calculate_take_profit(entry=19500.0, stop_loss=19450.0, risk_reward_ratio=3.0)
    assert result_3r['take_profit'] == 19650.0  # Entry + 3 * 50


def test_break_even_rule():
    """Test break-even rule at +0.5R."""
    calc = RiskCalculator(account_balance=10000)

    # At +0.5R should trigger BE move
    result_05r = calc.should_move_to_break_even(
        entry=19500.0,
        current_price=19525.0,  # +25 = +0.5R
        stop_loss=19450.0
    )
    assert result_05r['should_move'] is True
    assert result_05r['new_stop_loss'] == 19500.0

    # Below +0.5R should not trigger
    result_below = calc.should_move_to_break_even(
        entry=19500.0,
        current_price=19520.0,  # +20 = +0.4R
        stop_loss=19450.0
    )
    assert result_below['should_move'] is False


def main():
    """Run all tests."""
    print("Risk Calculator Test Suite")
    print("=" * 60)

    tests = [
        ("Initialization - Default", test_init_default),
        ("Initialization - Custom Risk", test_init_custom_risk),
        ("Position Size - Long", test_position_size_long),
        ("Position Size - Short", test_position_size_short),
        ("Stop Loss - Long", test_stop_loss_long),
        ("Take Profit - 2R", test_take_profit_2r),
        ("Leverage Calculation", test_leverage_calculation),
        ("KO Product - Long", test_ko_long),
        ("Break-Even - No Commission", test_break_even_no_commission),
        ("Break-Even - With Commission", test_break_even_with_commission),
        ("Validation - Valid Trade", test_validate_valid_trade),
        ("Validation - Excessive Risk", test_validate_excessive_risk),
        ("Break-Even Move - Yes", test_should_move_be_yes),
        ("Break-Even Move - No", test_should_move_be_no),
        ("Full Trade Plan", test_full_trade_plan_long),
        ("1% Risk Rule", test_1_percent_rule),
        ("KO Leverage", test_ko_leverage),
        ("R-Multiple Calculation", test_r_multiple_calculation),
        ("Break-Even Rule (+0.5R)", test_break_even_rule),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())

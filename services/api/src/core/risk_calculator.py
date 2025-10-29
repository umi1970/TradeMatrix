"""
Risk Calculator for TradeMatrix.ai

Implements position sizing, risk management, and KO-product calculations
according to the 1% risk rule and break-even strategy.

Author: TradeMatrix.ai
Date: 2025-10-29
"""

from typing import Dict, List, Optional, Literal
from decimal import Decimal, ROUND_HALF_UP


class RiskCalculator:
    """
    Position sizing and risk management calculator.

    Implements:
    - 1% Risk Rule (max 1% account balance per trade)
    - R-Multiple calculations (1R = Entry to SL distance)
    - KO-Product calculations (Knock-Out certificates)
    - Break-even rules (+0.5% profit triggers BE move)
    - Position sizing based on risk parameters
    """

    def __init__(self, account_balance: float, risk_per_trade: float = 0.01):
        """
        Initialize Risk Calculator.

        Args:
            account_balance: Total account balance in EUR
            risk_per_trade: Risk percentage per trade (default: 0.01 = 1%)

        Raises:
            ValueError: If account_balance <= 0 or risk_per_trade not in (0, 0.1]
        """
        if account_balance <= 0:
            raise ValueError("Account balance must be positive")

        if not 0 < risk_per_trade <= 0.1:
            raise ValueError("Risk per trade must be between 0 and 10% (0.1)")

        self.account_balance = float(account_balance)
        self.risk_per_trade = float(risk_per_trade)
        self.max_risk_amount = self.account_balance * self.risk_per_trade

    def calculate_position_size(
        self,
        entry: float,
        stop_loss: float,
        risk_amount: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate position size based on entry, stop loss, and risk amount.

        Formula: Position Size = Risk Amount / |Entry - Stop Loss|

        Args:
            entry: Entry price
            stop_loss: Stop loss price
            risk_amount: Custom risk amount (default: use max_risk_amount)

        Returns:
            dict with position_size, risk_amount, and risk_per_unit

        Raises:
            ValueError: If entry or stop_loss <= 0, or entry == stop_loss
        """
        if entry <= 0 or stop_loss <= 0:
            raise ValueError("Entry and stop loss must be positive")

        if entry == stop_loss:
            raise ValueError("Entry and stop loss cannot be equal")

        # Use default risk amount if not provided
        risk_amt = risk_amount if risk_amount is not None else self.max_risk_amount

        # Calculate risk per unit
        risk_per_unit = abs(entry - stop_loss)

        # Calculate position size
        position_size = risk_amt / risk_per_unit

        return {
            'position_size': round(position_size, 2),
            'risk_amount': round(risk_amt, 2),
            'risk_per_unit': round(risk_per_unit, 4),
            'account_balance': round(self.account_balance, 2),
            'risk_percentage': round((risk_amt / self.account_balance) * 100, 2)
        }

    def calculate_stop_loss(
        self,
        entry: float,
        risk_percentage: float = 0.0025,
        direction: Literal['long', 'short'] = 'long'
    ) -> Dict[str, float]:
        """
        Calculate stop loss based on entry price and risk percentage.

        Default risk_percentage = 0.0025 (0.25% distance from entry)

        Args:
            entry: Entry price
            risk_percentage: Distance from entry as percentage (default: 0.25%)
            direction: Trade direction ('long' or 'short')

        Returns:
            dict with stop_loss, distance, and distance_percentage

        Raises:
            ValueError: If entry <= 0 or risk_percentage <= 0
        """
        if entry <= 0:
            raise ValueError("Entry must be positive")

        if risk_percentage <= 0:
            raise ValueError("Risk percentage must be positive")

        # Calculate stop loss distance
        distance = entry * risk_percentage

        # Calculate stop loss based on direction
        if direction == 'long':
            stop_loss = entry - distance
        else:  # short
            stop_loss = entry + distance

        return {
            'stop_loss': round(stop_loss, 4),
            'distance': round(distance, 4),
            'distance_percentage': round(risk_percentage * 100, 3),
            'entry': round(entry, 4),
            'direction': direction
        }

    def calculate_take_profit(
        self,
        entry: float,
        stop_loss: float,
        risk_reward_ratio: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate take profit based on R-Multiple.

        Formula: TP = Entry + (R-Multiple × |Entry - SL|)

        Args:
            entry: Entry price
            stop_loss: Stop loss price
            risk_reward_ratio: Risk-reward ratio (default: 2.0 = 2R)

        Returns:
            dict with take_profit, one_r, profit_distance, and risk_reward_ratio

        Raises:
            ValueError: If prices <= 0, entry == stop_loss, or RR ratio <= 0
        """
        if entry <= 0 or stop_loss <= 0:
            raise ValueError("Entry and stop loss must be positive")

        if entry == stop_loss:
            raise ValueError("Entry and stop loss cannot be equal")

        if risk_reward_ratio <= 0:
            raise ValueError("Risk-reward ratio must be positive")

        # Determine direction
        direction = 'long' if entry > stop_loss else 'short'

        # Calculate 1R (distance from entry to stop loss)
        one_r = abs(entry - stop_loss)

        # Calculate take profit
        if direction == 'long':
            take_profit = entry + (risk_reward_ratio * one_r)
        else:  # short
            take_profit = entry - (risk_reward_ratio * one_r)

        profit_distance = abs(take_profit - entry)

        return {
            'take_profit': round(take_profit, 4),
            'one_r': round(one_r, 4),
            'profit_distance': round(profit_distance, 4),
            'risk_reward_ratio': round(risk_reward_ratio, 2),
            'direction': direction
        }

    def calculate_leverage(
        self,
        position_size: float,
        account_balance: Optional[float] = None,
        product_type: Literal['CFD', 'KO', 'Futures'] = 'CFD'
    ) -> Dict[str, float]:
        """
        Calculate leverage required for position.

        Formula: Leverage = Position Size / Account Balance

        Args:
            position_size: Position size in EUR
            account_balance: Account balance (default: use instance balance)
            product_type: Type of product (CFD, KO, Futures)

        Returns:
            dict with leverage, position_size, account_balance, and product_type

        Raises:
            ValueError: If position_size or account_balance <= 0
        """
        if position_size <= 0:
            raise ValueError("Position size must be positive")

        balance = account_balance if account_balance is not None else self.account_balance

        if balance <= 0:
            raise ValueError("Account balance must be positive")

        leverage = position_size / balance

        # Typical max leverage by product type
        max_leverage_by_type = {
            'CFD': 30.0,      # EU regulation (ESMA)
            'KO': 10.0,       # Conservative for KO products
            'Futures': 20.0   # Futures leverage
        }

        max_allowed = max_leverage_by_type.get(product_type, 10.0)
        is_safe = leverage <= max_allowed

        return {
            'leverage': round(leverage, 2),
            'position_size': round(position_size, 2),
            'account_balance': round(balance, 2),
            'product_type': product_type,
            'max_allowed_leverage': max_allowed,
            'is_safe': is_safe
        }

    def calculate_ko_product(
        self,
        entry: float,
        stop_loss: float,
        direction: Literal['long', 'short'],
        safety_buffer: float = 0.005
    ) -> Dict[str, float]:
        """
        Calculate KO threshold for Knock-Out certificates.

        KO threshold should be below stop loss (long) or above stop loss (short)
        to provide safety buffer.

        Formula:
        - Long: KO = SL × (1 - safety_buffer)
        - Short: KO = SL × (1 + safety_buffer)
        - Leverage = Entry / |Entry - KO|

        Args:
            entry: Entry price
            stop_loss: Stop loss price
            direction: Trade direction ('long' or 'short')
            safety_buffer: Safety buffer percentage (default: 0.5%)

        Returns:
            dict with ko_threshold, leverage, safety_distance, and warnings

        Raises:
            ValueError: If prices <= 0 or safety_buffer < 0
        """
        if entry <= 0 or stop_loss <= 0:
            raise ValueError("Entry and stop loss must be positive")

        if safety_buffer < 0:
            raise ValueError("Safety buffer cannot be negative")

        warnings = []

        # Calculate KO threshold with safety buffer
        if direction == 'long':
            ko_threshold = stop_loss * (1 - safety_buffer)
            if ko_threshold <= 0:
                warnings.append("KO threshold too close to zero, increase entry or reduce buffer")
        else:  # short
            ko_threshold = stop_loss * (1 + safety_buffer)

        # Calculate KO leverage
        ko_distance = abs(entry - ko_threshold)
        leverage = entry / ko_distance if ko_distance > 0 else float('inf')

        # Safety checks
        if leverage > 20:
            warnings.append(f"High leverage ({leverage:.1f}x) - consider wider stop loss")

        # Distance between SL and KO
        safety_distance = abs(stop_loss - ko_threshold)
        safety_distance_pct = (safety_distance / entry) * 100

        return {
            'ko_threshold': round(ko_threshold, 4),
            'leverage': round(leverage, 2),
            'entry': round(entry, 4),
            'stop_loss': round(stop_loss, 4),
            'safety_distance': round(safety_distance, 4),
            'safety_distance_pct': round(safety_distance_pct, 3),
            'direction': direction,
            'warnings': warnings
        }

    def calculate_break_even(
        self,
        entry: float,
        commission_percentage: float = 0.0,
        spread: float = 0.0
    ) -> Dict[str, float]:
        """
        Calculate break-even price including commissions and spread.

        Break-Even Rule: Move SL to break-even when trade is +0.5R in profit

        Args:
            entry: Entry price
            commission_percentage: Commission as percentage (e.g., 0.001 = 0.1%)
            spread: Spread in price units

        Returns:
            dict with break_even_price, commission_cost, and total_cost

        Raises:
            ValueError: If entry <= 0 or commission/spread < 0
        """
        if entry <= 0:
            raise ValueError("Entry must be positive")

        if commission_percentage < 0 or spread < 0:
            raise ValueError("Commission and spread cannot be negative")

        # Calculate commission cost
        commission_cost = entry * commission_percentage

        # Break-even includes commission on both entry and exit
        total_commission = 2 * commission_cost

        # Break-even price (assuming long position)
        break_even_price = entry + total_commission + spread

        return {
            'break_even_price': round(break_even_price, 4),
            'entry': round(entry, 4),
            'commission_cost': round(total_commission, 4),
            'spread': round(spread, 4),
            'total_cost': round(total_commission + spread, 4),
            'cost_percentage': round(((total_commission + spread) / entry) * 100, 3)
        }

    def validate_trade_risk(
        self,
        entry: float,
        stop_loss: float,
        position_size: float,
        account_balance: Optional[float] = None
    ) -> Dict[str, any]:
        """
        Validate if trade meets risk management rules.

        Checks:
        1. Risk amount <= max_risk_amount (1% rule)
        2. Position size > 0
        3. Valid price levels
        4. Reasonable leverage

        Args:
            entry: Entry price
            stop_loss: Stop loss price
            position_size: Position size in units
            account_balance: Account balance (default: use instance balance)

        Returns:
            dict with is_valid, risk_amount, warnings, and validation details
        """
        balance = account_balance if account_balance is not None else self.account_balance
        warnings = []
        is_valid = True

        # Validate prices
        if entry <= 0 or stop_loss <= 0:
            warnings.append("Entry and stop loss must be positive")
            is_valid = False

        if entry == stop_loss:
            warnings.append("Entry and stop loss cannot be equal")
            is_valid = False

        if position_size <= 0:
            warnings.append("Position size must be positive")
            is_valid = False

        # Calculate risk amount
        risk_per_unit = abs(entry - stop_loss) if entry != stop_loss else 0
        risk_amount = position_size * risk_per_unit
        risk_percentage = (risk_amount / balance) * 100 if balance > 0 else 0

        # Check 1% rule
        max_allowed_risk = balance * self.risk_per_trade
        if risk_amount > max_allowed_risk:
            warnings.append(
                f"Risk amount ({risk_amount:.2f} EUR) exceeds max allowed "
                f"({max_allowed_risk:.2f} EUR, {self.risk_per_trade * 100:.1f}%)"
            )
            is_valid = False

        # Calculate leverage
        position_value = position_size * entry if entry > 0 else 0
        leverage = position_value / balance if balance > 0 else 0

        if leverage > 30:
            warnings.append(f"Leverage ({leverage:.1f}x) exceeds EU regulation limit (30x)")
            is_valid = False
        elif leverage > 10:
            warnings.append(f"High leverage ({leverage:.1f}x) - consider reducing position size")

        # Check if risk is too small (< 0.1%)
        if risk_percentage < 0.1:
            warnings.append(f"Risk too small ({risk_percentage:.2f}%) - consider increasing position")

        return {
            'is_valid': is_valid,
            'risk_amount': round(risk_amount, 2),
            'risk_percentage': round(risk_percentage, 2),
            'max_allowed_risk': round(max_allowed_risk, 2),
            'max_risk_percentage': round(self.risk_per_trade * 100, 1),
            'leverage': round(leverage, 2),
            'position_value': round(position_value, 2),
            'warnings': warnings
        }

    def should_move_to_break_even(
        self,
        entry: float,
        current_price: float,
        stop_loss: float,
        threshold_r: float = 0.5
    ) -> Dict[str, any]:
        """
        Check if trade should move stop loss to break-even.

        Break-Even Rule: Move SL to entry when trade is +0.5R (default) in profit

        Args:
            entry: Entry price
            current_price: Current market price
            stop_loss: Current stop loss price
            threshold_r: R-multiple threshold (default: 0.5R)

        Returns:
            dict with should_move, current_r, threshold_r, and new_stop_loss
        """
        if entry <= 0 or current_price <= 0 or stop_loss <= 0:
            return {
                'should_move': False,
                'reason': 'Invalid prices',
                'current_r': 0,
                'threshold_r': threshold_r
            }

        # Determine direction
        direction = 'long' if entry > stop_loss else 'short'

        # Calculate 1R
        one_r = abs(entry - stop_loss)

        # Calculate current profit in R
        if direction == 'long':
            current_profit = current_price - entry
        else:  # short
            current_profit = entry - current_price

        current_r = current_profit / one_r if one_r > 0 else 0

        # Check if threshold is met
        should_move = current_r >= threshold_r

        result = {
            'should_move': should_move,
            'current_r': round(current_r, 2),
            'threshold_r': threshold_r,
            'current_price': round(current_price, 4),
            'entry': round(entry, 4),
            'current_stop_loss': round(stop_loss, 4),
            'direction': direction
        }

        if should_move:
            result['new_stop_loss'] = round(entry, 4)
            result['reason'] = f"Trade at +{current_r:.2f}R, moving SL to break-even"
        else:
            result['new_stop_loss'] = round(stop_loss, 4)
            result['reason'] = f"Trade at +{current_r:.2f}R, below threshold (+{threshold_r}R)"

        return result

    def calculate_full_trade_plan(
        self,
        entry: float,
        stop_loss: float,
        direction: Literal['long', 'short'],
        risk_reward_ratio: float = 2.0,
        product_type: Literal['CFD', 'KO', 'Futures'] = 'CFD',
        commission_percentage: float = 0.0
    ) -> Dict[str, any]:
        """
        Calculate complete trade plan with all risk parameters.

        This is a convenience method that combines all calculations.

        Args:
            entry: Entry price
            stop_loss: Stop loss price
            direction: Trade direction ('long' or 'short')
            risk_reward_ratio: Risk-reward ratio (default: 2.0)
            product_type: Product type (CFD, KO, Futures)
            commission_percentage: Commission percentage

        Returns:
            Comprehensive dict with all trade plan details
        """
        # Position sizing
        position = self.calculate_position_size(entry, stop_loss)

        # Take profit
        take_profit = self.calculate_take_profit(entry, stop_loss, risk_reward_ratio)

        # Leverage
        leverage = self.calculate_leverage(
            position['position_size'] * entry,
            product_type=product_type
        )

        # KO calculation (if applicable)
        ko_data = None
        if product_type == 'KO':
            ko_data = self.calculate_ko_product(entry, stop_loss, direction)

        # Break-even
        break_even = self.calculate_break_even(entry, commission_percentage)

        # Validation
        validation = self.validate_trade_risk(
            entry, stop_loss, position['position_size']
        )

        return {
            'entry': round(entry, 4),
            'stop_loss': round(stop_loss, 4),
            'take_profit': round(take_profit['take_profit'], 4),
            'direction': direction,
            'position_size': position['position_size'],
            'risk_amount': position['risk_amount'],
            'risk_percentage': position['risk_percentage'],
            'one_r': take_profit['one_r'],
            'risk_reward_ratio': risk_reward_ratio,
            'leverage': leverage['leverage'],
            'break_even_price': break_even['break_even_price'],
            'product_type': product_type,
            'ko_data': ko_data,
            'is_valid': validation['is_valid'],
            'warnings': validation['warnings'],
            'account_balance': self.account_balance,
            'max_risk_amount': self.max_risk_amount
        }


# Example usage and helper functions
def format_trade_plan(trade_plan: Dict) -> str:
    """Format trade plan for display."""
    output = []
    output.append("=" * 60)
    output.append("TRADE PLAN")
    output.append("=" * 60)
    output.append(f"Direction: {trade_plan['direction'].upper()}")
    output.append(f"Entry: {trade_plan['entry']:.4f} EUR")
    output.append(f"Stop Loss: {trade_plan['stop_loss']:.4f} EUR")
    output.append(f"Take Profit: {trade_plan['take_profit']:.4f} EUR")
    output.append(f"Break-Even: {trade_plan['break_even_price']:.4f} EUR")
    output.append("")
    output.append(f"Position Size: {trade_plan['position_size']:.2f} units")
    output.append(f"Risk Amount: {trade_plan['risk_amount']:.2f} EUR ({trade_plan['risk_percentage']:.2f}%)")
    output.append(f"1R Distance: {trade_plan['one_r']:.4f} EUR")
    output.append(f"Risk:Reward: 1:{trade_plan['risk_reward_ratio']:.1f}")
    output.append(f"Leverage: {trade_plan['leverage']:.2f}x")
    output.append("")

    if trade_plan.get('ko_data'):
        output.append(f"KO Threshold: {trade_plan['ko_data']['ko_threshold']:.4f} EUR")
        output.append(f"KO Leverage: {trade_plan['ko_data']['leverage']:.2f}x")
        output.append("")

    output.append(f"Valid: {'YES' if trade_plan['is_valid'] else 'NO'}")
    if trade_plan['warnings']:
        output.append("\nWARNINGS:")
        for warning in trade_plan['warnings']:
            output.append(f"  - {warning}")

    output.append("=" * 60)
    return "\n".join(output)


if __name__ == "__main__":
    # Example usage
    print("Risk Calculator - Example Calculations\n")

    # Initialize with 10,000 EUR account
    calc = RiskCalculator(account_balance=10000, risk_per_trade=0.01)

    # Example 1: DAX Long Trade
    print("Example 1: DAX Long Trade")
    print("-" * 60)

    trade_plan = calc.calculate_full_trade_plan(
        entry=19500.0,
        stop_loss=19450.0,
        direction='long',
        risk_reward_ratio=2.0,
        product_type='CFD',
        commission_percentage=0.0001
    )

    print(format_trade_plan(trade_plan))
    print("\n")

    # Example 2: NASDAQ Short with KO Product
    print("Example 2: NASDAQ Short with KO Product")
    print("-" * 60)

    trade_plan_ko = calc.calculate_full_trade_plan(
        entry=18000.0,
        stop_loss=18100.0,
        direction='short',
        risk_reward_ratio=2.0,
        product_type='KO',
        commission_percentage=0.0
    )

    print(format_trade_plan(trade_plan_ko))

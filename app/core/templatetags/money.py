from decimal import Decimal, ROUND_CEILING, InvalidOperation
from django import template

register = template.Library()

@register.filter
def ceil2(value):
    """
    Round UP to 2 decimals (ceiling).
    Example: 101.3001 -> 101.31
    """
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return value
    return d.quantize(Decimal("0.01"), rounding=ROUND_CEILING)

@register.filter
def fmt2(value):
    """
    Format to 2 decimals (normal).
    """
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return value
    return f"{d.quantize(Decimal('0.01')):.2f}"
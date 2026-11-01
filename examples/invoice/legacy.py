"""Executable legacy invoice calculator. Synthetic demonstration application."""
from decimal import Decimal, ROUND_HALF_UP


def invoice(items):
    if not items:
        return {"error": "empty_invoice"}
    total = Decimal("0")
    for item in items:
        quantity = item["quantity"]
        price = Decimal(str(item["price"]))
        if quantity < 0 or price < 0:
            return {"error": "negative_value"}
        total += price * quantity
    return {"total": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)), "currency": "USD"}

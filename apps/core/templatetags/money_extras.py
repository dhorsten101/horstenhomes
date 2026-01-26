from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


def _to_decimal(value) -> Decimal | None:
	if value is None or value == "":
		return None
	if isinstance(value, Decimal):
		return value
	try:
		return Decimal(str(value))
	except (InvalidOperation, ValueError, TypeError):
		return None


def _strip_trailing_zeros(s: str) -> str:
	if "." in s:
		s = s.rstrip("0").rstrip(".")
	return s


def _short_number(amount: Decimal) -> str:
	abs_amount = abs(amount)

	million = Decimal("1000000")
	billion = Decimal("1000000000")
	thousand = Decimal("1000")

	def fmt_suffix(n: Decimal, suffix: str) -> str:
		# Keep up to 2 decimal places, but trim trailing zeros:
		#  - 11.10 -> 11.1
		#  - 11.11 -> 11.11
		#  - 11.00 -> 11
		s = _strip_trailing_zeros(format(n.quantize(Decimal("0.01")), "f"))
		return f"{'-' if amount < 0 else ''}{s}{suffix}"

	# Billions
	if abs_amount >= billion:
		return fmt_suffix(abs_amount / billion, "bil")

	# Millions
	if abs_amount >= million:
		return fmt_suffix(abs_amount / million, "mil")

	# Thousands
	if abs_amount >= thousand:
		return fmt_suffix(abs_amount / thousand, "k")

	# Under 1,000: keep up to 2 decimals, trim trailing zeros
	s = _strip_trailing_zeros(format(abs_amount.quantize(Decimal("0.01")), "f"))
	return f"{'-' if amount < 0 else ''}{s}"


@register.filter(name="usd")
def usd(value) -> str:
	"""
	Format money as USD with short units:
	- 1_100_000 -> "$ 1.1mil"
	- 11_100_000 -> "$ 11.1mil"
	"""

	d = _to_decimal(value)
	if d is None:
		return "—"
	return f"$ {_short_number(d)}"


# Backwards-compat alias (deprecated): keep older templates from breaking.
@register.filter(name="zar")
def zar(value) -> str:
	return usd(value)


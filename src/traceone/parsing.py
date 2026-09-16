from __future__ import annotations

import json
from dataclasses import dataclass


VALUE_MIN = 1
VALUE_MAX = 355
EXPECTED_COUNT = 315


@dataclass(frozen=True)
class ParseResult:
    """A strict parse plus an explicitly diagnosed usable subsequence.

    ``numbers`` contains only integer values inside the declared range.  Values
    are never coerced, and every dropped item is represented in ``errors``.
    This lets attribution continue after a small format error without calling
    the original response format-compliant.
    """

    numbers: tuple[int, ...]
    valid: bool
    errors: tuple[str, ...]
    observed_items: int = 0
    integer_items: int = 0


def _validate_numbers(payload: list[object], expected_count: int) -> ParseResult:
    errors: list[str] = []
    numbers: list[int] = []
    for index, value in enumerate(payload):
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append(f"item_{index}_not_integer")
            continue
        if not VALUE_MIN <= value <= VALUE_MAX:
            errors.append(f"item_{index}_out_of_range")
            continue
        numbers.append(value)

    if len(payload) != expected_count:
        errors.append(f"wrong_count:{len(payload)}")

    integer_items = sum(
        isinstance(value, int) and not isinstance(value, bool) for value in payload
    )
    return ParseResult(
        tuple(numbers),
        not errors,
        tuple(errors),
        observed_items=len(payload),
        integer_items=integer_items,
    )


def parse_identity_response(text: str, expected_count: int = EXPECTED_COUNT) -> ParseResult:
    """Parse the v1 flat JSON-array contract without silently repairing output."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return ParseResult((), False, (f"invalid_json:{exc.msg}",))
    if not isinstance(payload, list):
        return ParseResult((), False, ("top_level_not_array",))
    return _validate_numbers(payload, expected_count)


def parse_grid_response(text: str, rows: int = 9, columns: int = 35) -> ParseResult:
    """Parse a 9x35 grid, optionally wrapped as ``{"numbers": ...}``."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return ParseResult((), False, (f"invalid_json:{exc.msg}",))
    if isinstance(payload, dict) and set(payload) == {"numbers"}:
        payload = payload["numbers"]
    if not isinstance(payload, list):
        return ParseResult((), False, ("missing_grid_array",))

    errors: list[str] = []
    if len(payload) != rows:
        errors.append(f"wrong_row_count:{len(payload)}")
    flattened: list[object] = []
    for row_index, row in enumerate(payload):
        if not isinstance(row, list):
            errors.append(f"row_{row_index}_not_array")
            continue
        if len(row) != columns:
            errors.append(f"row_{row_index}_wrong_count:{len(row)}")
        flattened.extend(row)

    validated = _validate_numbers(flattened, rows * columns)
    return ParseResult(
        validated.numbers,
        not errors and validated.valid,
        tuple(errors) + validated.errors,
        observed_items=validated.observed_items,
        integer_items=validated.integer_items,
    )

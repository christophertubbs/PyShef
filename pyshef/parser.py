from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

import pandas as pd

_CONTROL_PREFIX = "D"
# Matches leading SHEF message format markers like ".A", ".B", ".BR", and ".E".
_FORMAT_RE = re.compile(r"^\.(A|B|E)[A-Z0-9]*\b")
# Matches parameter code tokens with optional trailing values ("PPH 1.25", "TAH 72").
_CODE_VALUE_RE = re.compile(r"^([A-Z][A-Z0-9]{1,7})(?:\s+(.+))?$")


@dataclass
class _Measurement:
    format: str
    station: str | None
    date_token: str | None
    timezone: str | None
    parameter: str
    value: str | None
    sequence: int | None = None


def _split_slash_tokens(text: str) -> list[str]:
    return [token.strip() for token in text.split("/") if token.strip()]


def _extract_code_value(token: str) -> tuple[str | None, str | None]:
    match = _CODE_VALUE_RE.match(token)
    if not match:
        return None, token
    code = match.group(1)
    raw_value = match.group(2)
    value = raw_value.strip() if raw_value is not None else None
    return code, value


def _parse_dot_a_or_e(line: str, fmt: str) -> list[_Measurement]:
    """Parse a single `.A` or `.E` line into measurements.

    `.A` messages produce one row per explicit parameter/value pair.
    `.E` messages also support trailing value-only tokens after a parameter
    token and emit a zero-based `sequence` index for each extracted value.
    """
    prefix, _, payload = line.partition(" ")
    parts = payload.strip().split()
    station = parts[0] if parts else None
    date_token = parts[1] if len(parts) > 1 else None
    timezone = None
    data_start = 2
    if len(parts) > 2 and "/" not in parts[2]:
        timezone = parts[2]
        data_start = 3
    data = " ".join(parts[data_start:])
    tokens = _split_slash_tokens(data)

    out: list[_Measurement] = []
    current_parameter: str | None = None
    sequence = 0
    for token in tokens:
        code, value = _extract_code_value(token)
        if code and code.startswith(_CONTROL_PREFIX):
            continue
        if code and value is None:
            current_parameter = code
            continue
        if code and value is not None:
            current_parameter = code
            out.append(
                _Measurement(
                    format=fmt,
                    station=station,
                    date_token=date_token,
                    timezone=timezone,
                    parameter=code,
                    value=value,
                    sequence=sequence if fmt == "E" else None,
                )
            )
            if fmt == "E":
                sequence += 1
            continue
        if current_parameter:
            out.append(
                _Measurement(
                    format=fmt,
                    station=station,
                    date_token=date_token,
                    timezone=timezone,
                    parameter=current_parameter,
                    value=value,
                    sequence=sequence if fmt == "E" else None,
                )
            )
            if fmt == "E":
                sequence += 1
    return out


def _parse_dot_b(lines: list[str], start: int) -> tuple[list[_Measurement], int]:
    """Parse a `.B` block from `start` until `.END`.

    Header parameter tokens are used for positional mapping in body lines.
    Body lines that include explicit `CODE value` tokens use those directly.
    Returns parsed measurements and the next unread line index.
    """
    header = lines[start]
    _, _, payload = header.partition(" ")
    main, _, tail = payload.partition("/")
    parts = main.strip().split()
    date_token = parts[1] if len(parts) > 1 else None
    timezone = parts[2] if len(parts) > 2 and "/" not in parts[2] else None
    header_tokens = _split_slash_tokens(tail)
    parameters = [token for token in header_tokens if not token.startswith(_CONTROL_PREFIX)]

    out: list[_Measurement] = []
    i = start + 1
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith(":"):
            i += 1
            continue
        if line.upper().startswith(".END"):
            return out, i + 1
        station, _, values_part = line.partition(" ")
        values = _split_slash_tokens(values_part)
        if not values:
            i += 1
            continue
        explicit_rows = 0
        for token in values:
            code, value = _extract_code_value(token)
            if code and value is not None and not code.startswith(_CONTROL_PREFIX):
                out.append(
                    _Measurement(
                        format="B",
                        station=station,
                        date_token=date_token,
                        timezone=timezone,
                        parameter=code,
                        value=value,
                    )
                )
                explicit_rows += 1
        if explicit_rows == 0 and parameters:
            for idx, value in enumerate(values):
                if idx >= len(parameters):
                    break
                out.append(
                    _Measurement(
                        format="B",
                        station=station,
                        date_token=date_token,
                        timezone=timezone,
                        parameter=parameters[idx],
                        value=value,
                    )
                )
        i += 1
    return out, i


def parse_shef_lines(lines: Iterable[str]) -> pd.DataFrame:
    """Parse SHEF text lines into a pandas DataFrame.

    Supports `.A`, `.B` (until `.END`), and `.E` records.
    Returns columns: `format`, `station`, `date_token`, `timezone`,
    `parameter`, `value`, and `sequence`.
    `value` is preserved as the raw token string from SHEF data.
    """
    rows: list[_Measurement] = []
    normalized = [line.strip() for line in lines if line.strip()]

    i = 0
    while i < len(normalized):
        line = normalized[i]
        if line.startswith(":"):
            i += 1
            continue
        format_match = _FORMAT_RE.match(line.upper())
        if not format_match:
            i += 1
            continue
        fmt = format_match.group(1)
        if fmt == "A":
            rows.extend(_parse_dot_a_or_e(line, "A"))
            i += 1
        elif fmt == "E":
            rows.extend(_parse_dot_a_or_e(line, "E"))
            i += 1
        else:
            b_rows, next_i = _parse_dot_b(normalized, i)
            rows.extend(b_rows)
            i = next_i

    frame = pd.DataFrame(
        {
            "format": [r.format for r in rows],
            "station": [r.station for r in rows],
            "date_token": [r.date_token for r in rows],
            "timezone": [r.timezone for r in rows],
            "parameter": [r.parameter for r in rows],
            "value": [r.value for r in rows],
            "sequence": [r.sequence for r in rows],
        }
    )
    return frame


def parse_shef(text: str) -> pd.DataFrame:
    """Parse a SHEF text blob into a pandas DataFrame.

    Example input includes `.A`, `.B`/`.END`, and `.E` records in one text
    string. Output schema matches `parse_shef_lines`.
    """
    return parse_shef_lines(text.splitlines())

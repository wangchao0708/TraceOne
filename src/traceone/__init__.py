"""TraceOne: one-response model-route attribution and degradation auditing."""

from .adapter import identify_text_adapted
from .degradation import (
    compare_paired_outcomes,
    compare_stratified_outcomes,
    mcnemar_detection_power,
    plan_mcnemar,
)
from .fingerprint import identify_text
from .support import identify_text_supported

__all__ = [
    "compare_paired_outcomes",
    "compare_stratified_outcomes",
    "identify_text",
    "identify_text_adapted",
    "identify_text_supported",
    "mcnemar_detection_power",
    "plan_mcnemar",
]
__version__ = "0.1.0"

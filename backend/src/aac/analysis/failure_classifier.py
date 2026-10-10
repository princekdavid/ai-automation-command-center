"""Rule-based failure classification. This module does not call an AI service."""

from dataclasses import dataclass
from enum import Enum


class FailureCategory(str, Enum):
    ASSERTION_FAILURE = "assertion_failure"
    LOCATOR_NOT_FOUND = "locator_not_found"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION = "authentication"
    TEST_SETUP = "test_setup"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class FailureAnalysis:
    test_id: str
    category: FailureCategory
    summary: str
    matched_rule: str | None = None


# Order matters: the most specific/high-signal patterns must be checked first.
_RULES: tuple[tuple[FailureCategory, tuple[str, ...], str], ...] = (
    (FailureCategory.TIMEOUT, (
        "timed out", "timeout", "time out", "deadline exceeded", "operation exceeded",
    ), "The test or an operation exceeded its time limit."),
    (FailureCategory.LOCATOR_NOT_FOUND, (
        "no such element", "element not found", "locator not found", "strict mode violation",
        "unable to locate", "could not find element", "waiting for locator",
    ), "The automation could not resolve the expected UI element or locator."),
    (FailureCategory.AUTHENTICATION, (
        "unauthorized", "forbidden", "http 401", "http 403", "invalid credentials",
        "authentication failed", "login failed",
    ), "The operation appears to have failed at an authentication or authorization boundary."),
    (FailureCategory.NETWORK_ERROR, (
        "connection refused", "connection reset", "name or service not known", "temporary failure in name resolution",
        "network is unreachable", "dns lookup failed", "ssl error", "tls handshake",
        "httpx.connecterror", "requests.exceptions.connectionerror",
    ), "The failure contains a network, DNS, or TLS connection signal."),
    (FailureCategory.ASSERTION_FAILURE, (
        "assertionerror", "assertion failed", "assert ",
        "does not equal", "not equal to", "mismatch",
    ), "The test's expected and actual values appear not to match."),
    (FailureCategory.TEST_SETUP, (
        "fixture setup", "setup failed", "teardown failed", "failed to import",
        "modulenotfounderror", "importerror", "fixture ' ", "fixture \"",
    ), "The failure appears to occur while importing or preparing the test."),
)


def classify_failure(test_id: str, outcome: str, message: str | None) -> FailureAnalysis:
    """Classify a normalized test result using transparent keyword rules."""
    normalized_outcome = outcome.strip().lower()
    if normalized_outcome not in {"failed", "error"}:
        return FailureAnalysis(
            test_id=test_id,
            category=FailureCategory.NOT_APPLICABLE,
            summary="Failure classification applies only to failed or errored tests.",
        )

    text = (message or "").strip().lower()
    if not text:
        return FailureAnalysis(
            test_id=test_id,
            category=FailureCategory.UNKNOWN,
            summary="The result contains no failure message to classify.",
        )

    for category, patterns, summary in _RULES:
        for pattern in patterns:
            if pattern in text:
                return FailureAnalysis(
                    test_id=test_id,
                    category=category,
                    summary=summary,
                    matched_rule=pattern,
                )

    return FailureAnalysis(
        test_id=test_id,
        category=FailureCategory.UNKNOWN,
        summary="No deterministic rule matched this failure message; review the raw message.",
    )

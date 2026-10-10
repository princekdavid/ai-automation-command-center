from aac.analysis.failure_classifier import FailureCategory, classify_failure


def test_timeout_rule_has_precedence() -> None:
    result = classify_failure("test_login", "failed", "AssertionError after request timed out")

    assert result.category is FailureCategory.TIMEOUT
    assert result.matched_rule == "timed out"


def test_locator_failure_is_classified() -> None:
    result = classify_failure("test_button", "failed", "Locator not found: #submit")

    assert result.category is FailureCategory.LOCATOR_NOT_FOUND
    assert result.matched_rule == "locator not found"


def test_assertion_failure_is_classified() -> None:
    result = classify_failure("test_total", "failed", "AssertionError: expected 4, actual 5")

    assert result.category is FailureCategory.ASSERTION_FAILURE


def test_empty_or_unknown_message_stays_unknown() -> None:
    empty = classify_failure("test_unknown", "error", None)
    unknown = classify_failure("test_unknown", "failed", "unexpected application behavior")

    assert empty.category is FailureCategory.UNKNOWN
    assert unknown.category is FailureCategory.UNKNOWN
    assert unknown.matched_rule is None


def test_passed_test_is_not_classified_as_failure() -> None:
    result = classify_failure("test_ok", "passed", "assertionerror in fixture log")

    assert result.category is FailureCategory.NOT_APPLICABLE

import pytest

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



@pytest.mark.parametrize(
    ("message", "expected_category"),
    [
        ("HTTP 401 unauthorized", FailureCategory.AUTHENTICATION),
        ("Connection refused by host", FailureCategory.NETWORK_ERROR),
        ("ModuleNotFoundError: No module named 'fixture_package'", FailureCategory.TEST_SETUP),
    ],
)
def test_authentication_network_and_setup_rules(message, expected_category) -> None:
    result = classify_failure("test_case", "error", message)

    assert result.category is expected_category
    assert result.matched_rule is not None


@pytest.mark.parametrize(
    ("message", "expected_category", "expected_rule"),
    [
        (
            "playwright._impl._errors.TimeoutError: page.wait_for_selector: Timeout 30000ms exceeded",
            FailureCategory.TIMEOUT,
            "timeout",
        ),
        (
            "strict mode violation: locator('button') resolved to 2 elements",
            FailureCategory.LOCATOR_NOT_FOUND,
            "strict mode violation",
        ),
        (
            "API request failed: HTTP 403 Forbidden",
            FailureCategory.AUTHENTICATION,
            "forbidden",
        ),
        (
            "requests.exceptions.ConnectionError: connection reset by peer",
            FailureCategory.NETWORK_ERROR,
            "connection reset",
        ),
        (
            "pytest: fixture 'db_session' setup failed",
            FailureCategory.TEST_SETUP,
            "fixture ' ",
        ),
        (
            "AssertionError: expected total 12, actual total 10; values do not equal",
            FailureCategory.ASSERTION_FAILURE,
            "assertionerror",
        ),
    ],
)
def test_representative_framework_failure_messages(message, expected_category, expected_rule):
    result = classify_failure("test_checkout", "FAILED", message)

    assert result.category is expected_category
    assert result.matched_rule == expected_rule


def test_failure_classification_is_case_insensitive_and_trims_outcome():
    result = classify_failure("test_auth", " Error ", "LOGIN FAILED: invalid credentials")

    assert result.category is FailureCategory.AUTHENTICATION
    assert result.matched_rule == "invalid credentials"


def test_unknown_failure_does_not_claim_a_root_cause():
    result = classify_failure(
        "test_regression", "failed",
        "The page rendered but the business workflow stopped unexpectedly",
    )

    assert result.category is FailureCategory.UNKNOWN
    assert result.matched_rule is None
    assert "No deterministic rule matched" in result.summary


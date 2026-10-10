# Deterministic Failure Analysis

## Purpose

Normalize common test-failure signals into transparent categories so the dashboard can group failures without an external model or paid AI service.

## Endpoint

`POST /api/v1/analysis/failures`

Request:

```json
{
  "results": [
    {
      "test_id": "pytest:abc123",
      "outcome": "failed",
      "message": "Locator not found: #submit"
    }
  ]
}
```

The response contains one analysis per input result: `test_id`, `category`, a short explanation, and the keyword rule that matched (when one did).

## Categories and rule order

1. `timeout` — timeout/deadline phrases
2. `locator_not_found` — missing element/locator and strict-mode phrases
3. `authentication` — authorization, credentials, and HTTP 401/403 phrases
4. `network_error` — connection, DNS, and TLS phrases
5. `assertion_failure` — assertion and expected/actual mismatch phrases
6. `test_setup` — import, fixture setup, and teardown phrases
7. `unknown` — failed/error result with no recognized signal
8. `not_applicable` — passed, skipped, xfailed, or xpassed result

Order is deliberate; for example, a timeout message that also includes an assertion phrase is classified as a timeout.

## Safety and limitations

- Classification is deterministic, local, and keyword-based; it does not call an AI model.
- The category is a heuristic, not a root-cause guarantee. Keep the original failure message visible for debugging.
- The matched keyword is returned for transparency.
- Unknown messages remain `unknown`; the classifier must not invent a root cause.
- Rules need representative fixtures and careful regression tests before being treated as stable.
- This endpoint classifies normalized inputs. It does not execute tests or mutate a repository.

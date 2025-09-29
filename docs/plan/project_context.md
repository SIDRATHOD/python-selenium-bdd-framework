### Project Context

Feature: AI-powered Self-Healing Locators for Selenium BDD Tests

Framework: Selenium + Python with BDD (Gherkin `.feature`, step definitions in `features/steps/`, page objects in `pages/`).

Problem: Locator fragility causes frequent test failures; manual fixes increase MTTR.

Goals:
- Reduce maintenance time by 60%.
- Achieve >80% healing accuracy.
- Avoid false positives when elements are truly missing.

Scope (from PRD):
- Error detection and artifact capture.
- AI analysis to generate stable locator candidates and wait strategy guidance.
- Safe, minimal code edits to replace only broken locators.
- Automated re-run with up to 3 attempts.
- Comprehensive audit trail, manual approval mode, and configuration controls.

Key Constraints:
- Only Selenium + Python BDD; no unrelated tools.
- Deterministic and secure processing; redaction of sensitive data.
- Whitelist edits to `pages/` and `features/steps/`.

Deliverables:
- Self-healing module, config (`framework_config.yaml`), `healing_report.json`, docs and example runs.




## Product Requirements Document (PRD)

### Feature Name
AI-powered Self-Healing Locators for Selenium BDD Tests

### Background
The existing automation framework uses Selenium WebDriver with Python organized in a BDD structure (Gherkin `.feature` files and Python step definitions). Failures frequently occur due to locator fragility caused by DOM changes, dynamic attributes, or timing issues. Today, engineers manually debug failures, identify broken locators, and update page objects and/or step definitions, which increases mean-time-to-repair (MTTR) and reduces test suite reliability.

### Objective and Success Criteria
- Reduce test maintenance time by 60% by eliminating most manual locator updates.
- Achieve >80% accuracy in automatically healing broken locators without human intervention.
- Avoid false positives: the system must not pass a test if the element is truly missing or business behavior has changed.

### Out of Scope
- Non-Selenium toolchains (e.g., Cypress, Playwright).
- Research content or academic treatments of AI/ML beyond pragmatic implementation details.
- Non-UI failures (API, data setup), except when needed to differentiate root causes.

### Users and Roles
- Test Automation Engineers: consume healing output, review audit trail, accept/reject AI changes.
- CI/CD System: executes test runs, triggers re-runs after healing.
- QA Leads: monitor healing metrics, govern configuration and guardrails.

### Functional Requirements
1) Error Detection
- The framework shall intercept and classify Selenium exceptions relevant to locator instability: `NoSuchElementException`, `TimeoutException`, and `StaleElementReferenceException`.
- The framework shall log failure context including:
  - Test metadata: feature file path, scenario name, step text, tags.
  - Locator metadata: source file path (page object or step), locator type (CSS/XPath/etc.), raw selector string, resolution strategy hierarchy if applicable.
  - Runtime context: URL, timestamp, browser/driver info, viewport size, retry count.
  - DOM artifacts: full page HTML snapshot, element subtree (if resolvable), and screenshot.
- The framework shall persist artifacts in a run-scoped folder and index them for retrieval by the AI module.

2) AI Error Analysis
- The system shall invoke an AI analysis workflow when a locator-related failure is detected.
- The AI shall determine the likely root cause classified into one of: invalid/changed locator, timing/synchronization issue, or stale element due to DOM re-render.
- The AI shall tokenize and analyze DOM and attributes to suggest one or more replacement locators with a stability score (0–1), prioritizing:
  1. `data-*` attributes (e.g., `data-test-id`),
  2. stable semantic attributes (e.g., `aria-label`, `role`, `name`, `type`),
  3. robust CSS selectors, and
  4. constrained XPath as last resort.
- The AI shall propose wait strategy changes if timing is the root cause (e.g., switch to explicit waits for visibility/clickability, increase timeout upper bound with jitter, or add retry-on-stale logic).
- The AI shall provide a confidence score and rationale for each recommendation, referencing DOM tokens and heuristic signals.

3) Code Auto-Fix
- The system shall automatically apply the AI recommendation to update only the broken locator while preserving scenario logic and business assertions.
- Supported targets for edits:
  - Page Object files in `pages/` that declare locators and element accessors.
  - Step definition files in `features/steps/` that embed locators or call page object methods.
- The AI fix shall:
  - Modify the minimal code surface (single locator/strategy),
  - Preserve function and scenario signatures,
  - Maintain coding style and lint rules,
  - Annotate the change with an inline comment indicating it was AI-healed, including timestamp and link to `healing_report.json` entry.
- The system shall not modify unrelated steps or features.

4) Re-run and Validation
- After applying a fix, the framework shall re-run the failing scenario only.
- If the scenario passes: mark outcome as "healed" and persist results.
- If the scenario fails again: the system shall retry with up to 2 additional healing attempts (max 3 total attempts), potentially trying alternate suggested locators or wait strategies in descending confidence order.
- If still failing after retries: classify as "manual intervention required", persist last artifacts, and do not attempt further automatic changes.

5) Audit and Governance
- All AI analyses, recommendations, applied edits, and run outcomes shall be logged to `reports/self_healing/healing_report.json` with entries including:
  - Test/scenario metadata, failure type and stack trace,
  - Original locator and proposed replacements with confidence/stability scores,
  - Code edit diff summary (file, line ranges, before/after hashes),
  - Re-run outcomes per attempt, and final status (healed/manual),
  - Links to DOM snapshot and screenshots.
- The framework shall support a manual approval mode: when enabled, fixes are proposed and recorded but not applied until accepted via a CLI flag or pre-commit step.
- A global configuration file `framework_config.yaml` shall expose:
  - `self_healing.enabled: true|false`,
  - `self_healing.mode: auto|manual`,
  - `self_healing.max_attempts: 3` (default),
  - `self_healing.selector_preferences: [data, semantic, css, xpath]`,
  - `self_healing.max_dom_snapshot_mb`, `self_healing.screenshot: true|false`,
  - provider-related keys for AI model and cost controls.

### Non-Functional Requirements
- Determinism: identical inputs should yield repeatable AI recommendations given the same model and configuration.
- Performance: healing analysis end-to-end should add ≤60 seconds median overhead per failing step.
- Security: redact secrets from DOM and logs; restrict file edits to whitelisted directories (`pages/`, `features/steps/`).
- Observability: structured logs with correlation IDs; emit metrics for attempts, heal rate, latency.

### Technical Approach
- Orchestration: Use LangGraph to implement a stateful graph with nodes for Execution, Detection, Analysis, Candidate Generation, Code Edit, Re-run, and Finalization. Maintain a per-scenario context object across nodes.
- Agentic AI: Implement a reasoning agent that consumes DOM tokens, failure metadata, and code context, producing ranked locator candidates and optional wait strategy adjustments.
- DOM and Artifacts: Save full-page HTML, targeted element subtree (if found), and screenshot. Tokenize DOM (attributes, paths, text) for model input while enforcing privacy filters.
- Code Editing: Programmatically rewrite only the affected locator using AST- or pattern-based edits to avoid collateral changes; validate imports and style.
- Retry Strategy: Implement exponential backoff for timing adjustments and alternate candidate locators per attempt.
- Configuration: Load `framework_config.yaml` at runtime; allow per-suite overrides via environment variables and CLI flags.

### Data Model and Storage
- `healing_report.json`: array of objects with keys: `id`, `timestamp`, `feature_path`, `scenario`, `step`, `failure_type`, `locator_before`, `candidates[]`, `chosen_fix`, `attempt`, `status`, `dom_snapshot_path`, `screenshot_path`, `diff`, `rationale`, `confidence`, `metrics`.
- Artifacts directory structure: `reports/self_healing/<run_id>/<scenario_id>/` containing `dom.html`, `screenshot.png`, `context.json`, and diffs.

### CI/CD Integration
- On failure in CI, the self-healing flow runs automatically if enabled.
- Post-run, publish `healing_report.json` as a CI artifact and surface a summary (healed count, manual needed) in the job logs.
- Optional Git automation: in manual mode, open a branch/PR with proposed locator edits and attach the report.

### Acceptance Criteria
- Given a changed DOM that breaks a locator, when the test runs with self-healing enabled, then the framework logs failure artifacts, proposes a new stable locator, applies the minimal edit, and the scenario passes within ≤3 attempts.
- Given a truly missing element, the system shall not fabricate a pass; after attempts are exhausted, it shall report "manual intervention required".
- `healing_report.json` entries contain complete metadata, links to artifacts, and code edit summaries for every healing attempt.
- `framework_config.yaml` toggles self-healing on/off and supports auto/manual modes.

### Risks and Mitigations
- Incorrect locator fix causing false pass: mitigate via stability scoring, attribute preference order, and post-fix validation that the element uniquely resolves and is interactable.
- Unintended edits to unrelated steps: mitigate via AST-based targeted edits and directory whitelisting.
- Overreliance on flaky attributes: mitigate via attribute preference and fallbacks; optionally annotate unstable selectors for human follow-up.

### Deliverables
- Self-healing module integrated into the framework with LangGraph-based workflow and agent.
- `framework_config.yaml` with self-healing settings and documentation.
- `reports/self_healing/healing_report.json` schema and generation.
- Documentation of the healing process, configuration, and governance, plus example healed runs with before/after locator snapshots.



# Improvement Roadmap: Elevating to 9/10 Engineering Standard

This roadmap is derived from the [Codebase Engineering Audit](.cursor/plans/codebase_engineering_audit_985f60ce.plan.md) and structures improvements by category, effort tier, and execution phase. The target is a **9/10** overall standard across Architecture, Design, and Code Readability & Maintainability.

**Prioritization axes:** long-term maintainability → risk reduction → scalability → developer experience.

**Implementation status:** Phase 1 (Quick Wins), Phase 2 (Dependency and API Clarity), Phase 3 (Structure and Testability), and Phase 4 (Polish and 9/10 Checklist) are **done**.

---

## Part 1: Category-Level Targets and Actions

### 1. Architecture

#### Current Weaknesses (Audit)

- Models depend on core (`Constants`, `serial_number_parser`) — inverted dependency.
- Config schema does not validate observability or `fail_on_ambiguous_matches`.
- Single worker thread, no cancellation or job queue (acceptable today, not documented).

#### 9/10 Standard

- **Dependency direction:** Domain (models) has zero imports from `core` or `operations`; core and UI depend on domain and operations only.
- **Config:** Every `AppConfig` field is validated and documented in one schema; invalid values are rejected or normalized with clear rules.
- **Concurrency:** Single-job behavior is explicit in docs and code; extension points (e.g. cancel, queue) are documented so future changes are low-risk.

#### Actionable Refactoring

| Tier | Action | Example / Detail |
|------|--------|------------------|
| **Quick win** **[Done]** | Extend `ConfigSchema.validate_config()` to include `metrics_enabled`, `telemetry_enabled`, `crash_reporting_enabled`, `fail_on_ambiguous_matches`. Validate as booleans; log and coerce invalid values to defaults. | In `config_schema.py`, add keys to `validate_config()` and call from `load_user_config` / `load_env_config`; ensure `AppConfig.from_dict` uses validated dict only. |
| **Quick win** **[Done]** | Document single-job concurrency in ARCHITECTURE.md: “Merge runs one job at a time; no cancel or queue. Future: add cancel token or job queue here.” | Add a short “Concurrency” subsection under Technical Details. |
| **Medium** **[Done]** | Introduce `pdf_merger/models/defaults.py` with `DEFAULT_SERIAL_NUMBERS_COLUMN` and `PERCENTAGE_MULTIPLIER`. `MergeJob.create()` and `MergeResult.get_success_rate()` use these; remove `from ..core.constants` from models. | `defaults.py`: `DEFAULT_SERIAL_NUMBERS_COLUMN = 'serial_numbers'`, `PERCENTAGE_MULTIPLIER = 100.0`. Core `Constants` re-exports from here or keeps its own for non-model callers. |
| **Medium** **[Done]** | Move serial-number parsing out of core for Row: add `pdf_merger/utils/serial_number_parser.py` (or `parsing/serial_numbers.py`) with `split_serial_numbers`, `deduplicate_serial_numbers`, `normalize_serial_number`. `Row.from_raw_data` and validators import from utils/parsing; core’s `serial_number_parser` becomes a thin wrapper or is deprecated. | Keep the same function signatures; only change import locations so `Row` and validators do not depend on `core`. |
| **Deep** **[Done]** | Optional: introduce a small `JobLoader` (e.g. in `core/job_loader.py`) that takes `(input_file, required_column)` and returns `MergeJob` (with rows loaded). Orchestrator and `process_file` both call it. This removes duplicate row-loading and centralizes file-read errors. | `load_job_from_file(path, required_column, on_progress=None) -> MergeJob`; raise or return empty job on read error; used by `run_merge_job` and `process_file`. |

---

### 2. Design

#### Current Weaknesses (Audit)

- Legacy and modern APIs both supported; dual entry points and result types increase cognitive load and divergence risk.
- `ConfigSchema` is a static-method class with no instance state.
- `MergeHandler.is_processing` is a public mutable flag used from UI and worker.
- PDF libs loaded via globals; testing and alternate backends are harder.

#### 9/10 Standard

- **API surface:** One primary path (`run_merge_job` / `process_job` / `MergeResult`); legacy entry points explicitly deprecated with timeline and single adapter (`as_processing_result`).
- **Config validation:** Plain functions or a single validated builder; no “namespace class” with only static methods.
- **Merge state:** Single source of truth for “is a merge running”; UI only reads state; transitions (idle → running → idle) are explicit and hard to misuse.
- **Testability:** PDF merge can be tested via an injectable abstraction (optional; default remains current lazy loading).

#### Actionable Refactoring

| Tier | Action | Example / Detail |
|------|--------|------------------|
| **Quick win** **[Done]** | Replace `ConfigSchema` with module-level functions. Add `validate_config(data) -> dict`, `validate_input_file(value)`, etc. in `config_schema.py`; call them from config_manager. Remove the class. | `def validate_config(data: Dict[str, Any]) -> Dict[str, Any]:` with same logic; config_manager imports `from .config_schema import validate_config`. |
| **Quick win** **[Done]** | Encapsulate merge state in `MergeHandler`: private `_state: Literal["idle", "running"]` and `_job_id: Optional[str]`. Public property `is_processing` only reads; `run_merge` sets state to running at start and back to idle in a single `finally` (and in completion/error callbacks if needed). | Ensure only one place writes “idle” (e.g. a single `_set_idle()` called from worker’s finally and from completion/error). |
| **Medium** **[Done]** | Formalize “preferred API” and deprecate legacy: (1) In `run_merge` and `process_file` docstrings, add “Deprecated. Use run_merge_job / process_job and as_processing_result if you need ProcessingResult. Will be removed in 2.0.” (2) In ARCHITECTURE.md Public API section, state “Primary: run_merge_job, process_job, MergeResult. Legacy: run_merge, process_file, ProcessingResult (deprecated).” (3) Add a short DEPRECATION.md or section in README with timeline. | No behavior change; only docs and deprecation notices. Optionally `warnings.warn(..., DeprecationWarning)` in `run_merge` / `process_file`. |
| **Medium** | Extract “apply result to UI” from `_on_merge_complete`: e.g. `_apply_merge_result_to_ui(self, result: MergeResult)` (updates results frame, log lines, counts) and `_reset_merge_ui_state()` (button, progress bar). `_on_merge_complete` becomes: set handler idle, stop progress, call `_apply_merge_result_to_ui`, `_reset_merge_ui_state`, `_update_ui_state`. | Enables unit tests of “given MergeResult, what log lines and frame values are set” without running the full app. |
| **Deep** | Introduce an optional PDF backend protocol: e.g. `Protocol merge(paths: List[Path], output: Path) -> bool`. Default implementation in `operations/pdf_merger.py` uses current lazy-loaded pypdf. Processor/row_pipeline accept an optional `pdf_backend` argument (default None = use default). Tests can inject a mock. | Keep existing API; add optional parameter to the layer that calls `merge_pdfs` (e.g. row_pipeline or a small service used by it). |

---

### 3. Code Readability & Maintainability

#### Current Weaknesses (Audit)

- Custom `FileNotFoundError` shadows the built-in.
- Duplicate row-loading in orchestrator and `process_file`.
- Long methods in `process_job` and `_on_merge_complete`; magic strings in UI and progress.

#### 9/10 Standard

- **Exceptions:** No shadowing of built-ins; custom exceptions are namespaced (e.g. `PDFMergerFileNotFoundError`).
- **DRY:** One implementation of “load file → MergeJob with rows”; used everywhere.
- **Readability:** Long methods split into named steps; UI and progress use named constants or enums; non-obvious behavior documented in docstrings.

#### Actionable Refactoring

| Tier | Action | Example / Detail |
|------|--------|------------------|
| **Quick win** **[Done]** | Rename `utils.exceptions.FileNotFoundError` to `PDFMergerFileNotFoundError`. Update all raises and except clauses (and tests). Re-export in `utils/__init__.py` and keep `PDFMergerError` as base. | `class PDFMergerFileNotFoundError(PDFMergerError):`; grep for `FileNotFoundError` in repo and update to new name. |
| **Quick win** **[Done]** | Add UI/progress constants: e.g. in `ui/constants.py` or `theme.py`: `WINDOW_SIZE_DEFAULT = "1020x800"`, `WINDOW_MIN_SIZE = (620, 500)`; progress keywords `PROGRESS_KEYWORD_SUCCESS = "Success"`, etc. Use these in `app.py` and in `_on_merge_progress` keyword list. | Reduces magic strings and makes tuning and i18n easier. |
| **Medium** **[Done]** | Extract “load rows from file into MergeJob” into one function: `load_job_from_file(input_file, source_folder, output_folder, required_column, job_id=None, on_progress=None) -> MergeJob`. Use in both `run_merge_job` and `process_file`; on read error return empty job or raise (and let orchestrator/process_file translate to empty result). | Implement in orchestrator or `core/job_loader.py`; both call sites pass through so file-read and progress behavior are identical. |
| **Medium** **[Done]** | Split `process_job`: extract `_record_job_failure` (already exists), and e.g. `_process_single_row_and_report(job, row, result, metrics, on_progress, fail_on_ambiguous)` that returns the `RowResult` and optionally calls `on_progress`. Loop in `process_job` becomes: for each row, call progress start, call `_process_single_row_and_report`, add result, call progress end. | Shorter `process_job` body; row-level logic testable via `_process_single_row_and_report` with mocks. |
| **Low** **[Done]** | Add one-line docstrings to internal helpers that encode non-obvious behavior: e.g. row_pipeline `_convert_excel_files_to_pdfs` (“Returns (pdf_paths, temp_pdf_files) for caller to cleanup.”), `_cleanup_temp_files`, and pipeline error mapping in merge_processor (“Maps pipeline error_message to RowStatus and RowResult fields.”). | Focus on “why” and “contract” (inputs/outputs) where not obvious from the name. |

---

## Part 2: Effort Tiers (Summary)

- **Quick wins (high impact, low effort)**  
  - Config schema extended for all AppConfig fields. **[Done]**  
  - Concurrency documented. **[Done]**  
  - ConfigSchema replaced by module-level validation functions. **[Done]**  
  - MergeHandler state encapsulated (single writer for idle/running). **[Done]**  
  - Rename `FileNotFoundError` → `PDFMergerFileNotFoundError`. **[Done]**  
  - UI/progress constants for window size and progress keywords. **[Done]**

- **Medium-complexity**  
  - Models defaults module; remove core dependency from models. **[Done]**  
  - Serial number parsing moved to utils/parsing; Row no longer depends on core. **[Done]**  
  - Deprecation notices and docs for legacy API. **[Done]**  
  - Extract “apply result to UI” and “reset merge UI” from `_on_merge_complete`. **[Done]**  
  - Single `load_job_from_file` and use in orchestrator and `process_file`. **[Done]**  
  - Split `process_job` with a clear “process one row and report” helper. **[Done]**

- **Deep structural**  
  - Optional `JobLoader` abstraction and single place for all job-from-file loading. **[Done]**  
  - Optional PDF backend protocol for testing and future backends.

---

## Part 3: Phased Execution Plan

### Phase 1: Quick Wins (Target: 1–2 weeks)

**Goal:** Remove immediate risks and clarify contracts with minimal structural change.

**Scope:**

1. **Architecture**  
   - Extend config schema to validate all AppConfig fields (including observability and `fail_on_ambiguous_matches`).  
   - Add a short “Concurrency” subsection in ARCHITECTURE.md (single job, no cancel/queue, future extension point).

2. **Design**  
   - Replace `ConfigSchema` class with module-level functions in `config_schema.py`; update config_manager imports.  
   - Encapsulate `MergeHandler` state: private `_state`/`_job_id`, public `is_processing` read-only; single place that sets idle (e.g. `_set_idle()` in worker’s finally and in callbacks).

3. **Readability & Maintainability**  
   - Rename `FileNotFoundError` → `PDFMergerFileNotFoundError`; update all usages and tests.  
   - Add UI/progress constants (window size, min size, progress keywords) and use them in app.py.

**Success criteria:**

- All existing tests pass.  
- No new deprecation warnings from these changes.  
- Config with invalid observability/boolean fields is validated (and coerced or rejected with log).  
- ARCHITECTURE.md contains a Concurrency subsection.  
- Grep for `FileNotFoundError` shows only built-in or explicit “built-in” comments; custom one is `PDFMergerFileNotFoundError`.

**Measurable outcomes:**

- Config schema coverage: 100% of AppConfig fields validated.  
- Zero exception shadowing of built-ins for the renamed exception.

---

### Phase 2: Dependency and API Clarity (Target: 2–3 weeks)

**Goal:** Correct dependency direction (domain independent of core) and single “load job” path; clarify preferred vs legacy API.

**Scope:**

1. **Architecture**  
   - Add `pdf_merger/models/defaults.py` with `DEFAULT_SERIAL_NUMBERS_COLUMN` and `PERCENTAGE_MULTIPLIER`.  
   - Update `MergeJob` and `MergeResult` to use model defaults; remove their imports from core.  
   - Move serial number parsing to `utils/serial_number_parser.py` (or `utils/parsing/serial_numbers.py`); update `Row` and validators to use it; core’s parser becomes wrapper or is removed.  
   - Introduce `load_job_from_file(...)` (orchestrator or `core/job_loader.py`) and use it in both `run_merge_job` and `process_file`.

2. **Design**  
   - Mark `run_merge` and `process_file` as deprecated in docstrings and ARCHITECTURE.md; add DEPRECATION.md (or README section) with timeline (e.g. remove in 2.0).  
   - Optionally add `warnings.warn(..., DeprecationWarning)` in legacy entry points.

3. **Readability & Maintainability**  
   - Rely on single `load_job_from_file` so row-loading and file-read error handling are in one place; remove duplicate loop from orchestrator and process_file.

**Success criteria:**

- `pdf_merger.models` has no imports from `pdf_merger.core` or `pdf_merger.operations`.  
- All tests pass; no regressions in merge behavior.  
- Deprecation section exists; at least docstring deprecation on legacy entry points.

**Measurable outcomes:**

- Dependency graph: models depend only on utils (and optionally config for defaults if you move any config there).  
- Single implementation of “file → MergeJob with rows” (no duplicated loop).

---

### Phase 3: Structure and Testability (Target: 2–3 weeks) **[Done]**

**Goal:** Shorter, testable methods; optional backend abstraction for PDF and future scalability.

**Scope:**

1. **Architecture**  
   - Optional: formalize `JobLoader` (or keep `load_job_from_file` as the single function) and document it in ARCHITECTURE.md.

2. **Design**  
   - Extract from `_on_merge_complete`: `_apply_merge_result_to_ui(result)` and `_reset_merge_ui_state()`.  
   - Split `process_job`: extract row-level logic into a helper (e.g. `_process_single_row_and_report`) so the main loop is a simple “for each row: progress → process row → add result → progress.”  
   - Optional: add PDF backend protocol and optional parameter in the layer that calls `merge_pdfs`; default implementation unchanged; tests can inject a mock.

3. **Readability & Maintainability**  
   - Add short docstrings to internal helpers (row_pipeline, pipeline→result mapping, cleanup).  
   - Ensure long methods (process_job, _on_merge_complete) are decomposed as above.

**Success criteria:**

- `process_job` and `_on_merge_complete` are under ~30 lines of control flow each; details in helpers.  
- At least one unit test that asserts “given MergeResult X, _apply_merge_result_to_ui produces expected log/frame state” (with app or handler mocks).  
- Internal helpers that encode non-obvious behavior have one-line docstrings.

**Measurable outcomes:**

- Cyclomatic complexity of `process_job` and `_on_merge_complete` reduced.  
- Test coverage of result-to-UI and single-row processing preserved or improved.

---

### Phase 4: Polish and 9/10 Checklist (Target: 1 week) **[Done]**

**Goal:** Close remaining gaps and document the 9/10 standard.

**Scope:**

1. **Architecture**  
   - Review ARCHITECTURE.md for concurrency, dependency rules, and config; add a “Quality bar” or “Target 9/10” subsection that states dependency direction, schema coverage, and concurrency contract.

2. **Design**  
   - Final pass: ensure MergeHandler state is the only source of truth for “merge in progress”; no stray `is_processing = False` outside the intended transition.  
   - If PDF backend was added, document it in ARCHITECTURE.md and in docstrings.

3. **Readability & Maintainability**  
   - Audit for remaining magic strings in UI and progress; move to constants if any are left.  
   - Optional: add a CONTRIBUTING.md or “Code standards” section that references this roadmap and the audit.

**Success criteria:**

- ARCHITECTURE.md includes a short “9/10 bar” or “Quality bar” subsection.  
- No remaining built-in exception shadowing; no duplicated row-loading; config fully validated.  
- All phases’ success criteria still hold.

**Measurable outcomes:**

- Checklist: (1) Models do not import core/operations, (2) Config schema validates all AppConfig fields, (3) Single load_job_from_file, (4) No FileNotFoundError shadowing, (5) Merge state encapsulated, (6) Legacy API deprecated with timeline, (7) Long methods split and key helpers documented.

---

## Part 4: Priority Order (Cross-Phase)

Ordered by: **maintainability → risk → scalability → DX.**

1. **Rename FileNotFoundError** **[Done]** (risk: confusion and wrong catches) — Phase 1.  
2. **Extend config schema** **[Done]** (maintainability, single source of truth) — Phase 1.  
3. **Encapsulate MergeHandler state** **[Done]** (risk: stuck “processing” state) — Phase 1.  
4. **Remove models → core dependency** **[Done]** (maintainability, clean layers) — Phase 2.  
5. **Single load_job_from_file** **[Done]** (maintainability, DRY) — Phase 2.  
6. **Replace ConfigSchema with functions** **[Done]** (design clarity) — Phase 1.  
7. **Deprecate legacy API with timeline** **[Done]** (cognitive load, divergence risk) — Phase 2.  
8. **Move serial parsing to utils** **[Done]** (architecture) — Phase 2.  
9. **Split long methods and extract UI result application** (readability, testability) — Phase 3.  
10. **Optional PDF backend** (testability, scalability) — Phase 3.  
11. **Document concurrency and 9/10 bar** **[Done]** (scalability, DX) — Phase 1 + 4.

---

## Part 5: Risk and Rollback

- **Phase 1:** Low risk. Config schema and MergeHandler changes are backward-compatible; exception rename is a breaking change for any code that catches `FileNotFoundError` expecting the custom one — grep and update call sites and tests.  
- **Phase 2:** Medium. Dependency and import moves can cause subtle import errors; run full test suite and a quick smoke test of the GUI after each move. Keep a single commit per “move” (e.g. defaults, parser, load_job_from_file) so you can revert by commit if needed.  
- **Phase 3:** Low. Extractions and optional protocol are additive; default behavior unchanged.  
- **Phase 4:** None. Documentation and checklist only.

**Rollback:** Each phase is designed so that reverting that phase’s commits restores the previous behavior without leaving the codebase in an inconsistent state (e.g. don’t remove legacy API in Phase 2, only deprecate).

---

## Summary

- **Phase 1 (Done):** Quick wins — config schema, concurrency docs, ConfigSchema→functions, MergeHandler state, exception rename, UI constants.  
- **Phase 2 (Done):** Architecture and API — model defaults, no core in models, single job loader, deprecate legacy.  
- **Phase 3 (Done):** Structure — split long methods, extract UI result application, optional PDF backend, docstrings.  
- **Phase 4 (Done):** Polish — 9/10 checklist in ARCHITECTURE.md, final pass on state and constants.

Completing all four phases with the success criteria above should bring the codebase to a **9/10** standard: clean dependency direction, full config validation, single source of truth for job loading and merge state, no exception shadowing, and clearer, testable structure with a defined path beyond legacy APIs.

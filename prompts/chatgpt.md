# AI Prompt History — Customer Orders Data Engineering Pipeline

## Project information

- Project: Customer Orders Data Engineering Pipeline
- Recruitment context: YottaFlex AI Data Engineering challenge
- AI tool: ChatGPT
- Conversation date: 2026-10-28
- Record format: Focused prompt and troubleshooting history

This record contains project-related user requests and relevant errors.
Routine successful terminal output dumps and assistant responses are omitted
as requested.

This is a reconstructed record, not a verbatim export of every message.
Review the original conversation and add any missing prompts before submission.
Prompts sent to other AI tools must be recorded separately.

## 1. Understand the challenge

### Prompt 1
"explain detail step by step after that we can start our project"

Purpose: Understand the recruitment email and submission guidelines before
starting implementation.

### Prompt 2
"Read carefully understand each point"

Purpose: Review the complete problem statement, including the workflow,
validation requirements, edge cases, acceptance criteria, evaluation weights,
and required deliverables.

### Prompt 3
"what we do next"

Purpose: Determine the first implementation step.

### Prompt 4
"Next"

Purpose: Continue the guided project workflow after environment setup.

## 2. Project setup and data preparation

### Prompt 5
"Next"

Purpose: Continue with dependency installation, project directory preparation,
and creation of reproducible sample customer and order CSV files.

### Prompt 6
"Next"

Purpose: Continue to CSV verification and implementation of data validation.

### Prompt 7
"Next"

Purpose: Continue after initial pipeline execution and inspect its outputs.

### Troubleshooting: Python launcher

Command entered:

    py --0p

Error:

    Unknown option: --0p

Purpose: Diagnose the incorrect Python launcher option.
The corrected command was `py -0p`.

### Troubleshooting: Wrong application launcher

Command attempted:

    C:\Program Files\nodejs\node.exe --experimental-network-inspection .\app.js

Error:

    Error: Cannot find module
    C:\Users\subbu\Documents\yottaflex-data-pipeline\app.js

Purpose: Diagnose why VS Code tried to launch a nonexistent Node.js entry point.
The project uses Python, and the Python script was run directly instead.

## 3. Validation, testing, and database publishing

### Prompt 8
"Next"

Purpose: Continue implementation after the validation module was created.

### Prompt 9
"Next"

Purpose: Add automated tests for validation, malformed records, duplicates,
null keys, empty datasets, and schema errors.

### Prompt 10
"Next"

Purpose: Add DuckDB publishing, database tables, and run-history metrics.

### Prompt 11
"Next"

Purpose: Test repeated publication and database transaction rollback.

### Troubleshooting: Failed rollback test

Primary error:

    _duckdb.ConversionException:
    Conversion Error: invalid date field format: "not-a-date"

Secondary error:

    _duckdb.TransactionException:
    TransactionContext Error: Current transaction is aborted (please ROLLBACK)

Purpose: Diagnose why an intentionally invalid date caused a rollback test
to fail during temporary DataFrame cleanup.

Resolution: Updated cleanup handling in `src/publish.py`, then reran the tests.

### Prompt 12
"Next"

Purpose: Add structured logging, run metrics, and JSON reconciliation reports.

## 4. Large datasets and performance

### Prompt 13
"Next"

Purpose: Create a reproducible synthetic data generator and benchmark a dataset
containing 20,000 customers and 100,000 orders.

### Prompt 14
"Next"

Purpose: Optimize duplicate-key detection after measuring the validation
bottleneck.

### Prompt 15
"Your next action: Replace the function, run all eight tests, and then run the
three-iteration benchmark."

Purpose: Validate that the optimization preserved correctness and measure
runtime and throughput again.

### Prompt 16
"Next"

Purpose: Add edge-case tests and prepare the documentation.

## 5. Documentation and prompt-history requirements

### Prompt 17
"yes the files exits
make the prompt history,but don't include all output pastes just query and error occur prompts.
what do you suggests"

Purpose: Create a focused AI prompt history that excludes routine successful
terminal output but preserves actual project requests and relevant errors.

### Prompt 18
"proceed with next steps"

Purpose: Complete the README, dependency specification, Git ignore rules,
and submission preparation.

## 6. Git and GitHub setup

### Prompt 19
"before doing that we need to connect our git repository right??"

Purpose: Confirm the need to connect the local Git repository to a GitHub remote.

### Prompt 20
"Done,what's next"

Purpose: Continue after renaming the repository to a neutral project name.

### Prompt 21
"start"

Purpose: Begin updating the repository description and finish submission preparation.

### Troubleshooting: URL entered as a command

Input entered directly into PowerShell:

    https://github.com/Subbu2542/yottaflex-data-pipeline.git

Error:

    The term 'https://github.com/Subbu2542/yottaflex-data-pipeline.git'
    is not recognized as the name of a cmdlet, function, script file,
    or operable program.

Purpose: Diagnose the PowerShell error. The URL must be supplied as an argument
to a Git command, such as `git remote add` or `git remote set-url`.

### Troubleshooting: Missing local Git repository

Command:

    git status --short

Error:

    fatal: not a git repository (or any of the parent directories): .git

Purpose: Diagnose the missing local Git repository and initialize Git.

### Troubleshooting: README replacement

Error:

    Old heading not found. No changes made; inspect README.md.

Purpose: Diagnose why an exact-text replacement did not find the old README
heading. The replacement was changed to locate the first Markdown heading.

### Prompt 22
"Done"

Purpose: Confirm the GitHub About description was updated and continue final review.

## 7. AI Tool Disclosure

ChatGPT was the only AI tool used for this project.

This document records project-related prompts and relevant
troubleshooting issues. Routine successful terminal outputs and
assistant responses are omitted.

Short workflow messages such as "Next", "start", and "Done" are
navigation-only messages rather than substantive technical requests.
They are not individually itemized in this focused record.

This is a reconstructed prompt history, not a verbatim transcript.
The original conversation should be reviewed for completeness before
submission. The record must not be represented as a verbatim export.

## 8. Final Completeness Review

Before submission:

1. Compare this record against the original ChatGPT conversation.
2. Add any missing substantive project or troubleshooting prompts.
3. Preserve exact wording where available.
4. Ensure the record accurately reflects the AI tool actually used.

The YottaFlex AI Candidate Project FAQ requires prompts submitted to
AI tools; AI responses are optional.

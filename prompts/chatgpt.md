# YottaFlex AI Candidate Project — AI Prompt History

## Scope

Project: Data Engineering Batch Pipeline
Date: 2026-10-28
AI tool: ChatGPT

This file records the candidate's project-related requests, implementation
follow-ups, and relevant troubleshooting errors. Routine successful terminal
outputs and assistant responses are intentionally omitted.

This is a focused record reconstructed from the documented conversation.
Review the original chat before submission and add any omitted prompts.
Prompts submitted to other AI tools must be recorded separately.

## 1. Project Understanding and Requirements

### Prompt 1 — Understand the recruitment challenge

"explain detail step by step after that we can start our project"

Purpose: Understand the project instructions and submission requirements
before implementation.

### Prompt 2 — Review the problem statement

"Read carefully understand each point"

Purpose: Carefully analyze the supplied screenshots and identify the
requirements, deliverables, edge cases, and evaluation criteria.

### Prompt 3 — Decide the next implementation step

"what we do next"

Purpose: Establish the next actions after reviewing the requirements.

### Prompt 4 — Continue the guided implementation

"next"

Purpose: Continue to the next project step after environment setup,
dataset preparation, pipeline implementation, testing, and reporting.
This short follow-up was used repeatedly during development.

## 2. Environment and Execution Troubleshooting

### Issue 1 — Incorrect Python launcher option

Command entered:

    py --0p

Error:

    Unknown option: --0p

Purpose: Diagnose the Python launcher command error.

Resolution: Used the correct command, `py -0p`, to list installed
Python interpreters.

### Issue 2 — Incorrect application launcher

Command attempted:

    C:\Program Files\nodejs\node.exe --experimental-network-inspection .\app.js

Error:

    Error: Cannot find module
    C:\Users\subbu\Documents\yottaflex-data-pipeline\app.js

Purpose: Diagnose why the project would not start when the editor
launched Node.js.

Resolution: The project uses Python, not Node.js. The validation
script was run directly with Python.

### Issue 3 — Checking the source file and running the pipeline

The source-file listing was checked after the launch error. The
subsequent Python command was:

    python src\validate.py

Purpose: Confirm that the Python source file existed and execute
the correct application entry point.

## 3. Data Validation and Database Implementation

### Prompt 5 — Continue after sample data creation

"Next"

Purpose: Proceed from sample CSV preparation to implementing
validation rules and the data-quality pipeline.

### Prompt 6 — Continue after the first pipeline run

"Next"

Purpose: Proceed from manual output inspection to automated
testing with Pytest.

### Prompt 7 — Continue after the initial validation tests

"Next"

Purpose: Add DuckDB publishing and database verification.

### Prompt 8 — Continue after database publishing

"Next"

Purpose: Test repeated publication, idempotency, and transaction
rollback behavior.

### Prompt 9 — Troubleshoot the failed rollback test

The following errors were shared:

    _duckdb.ConversionException:
    Conversion Error: invalid date field format: "not-a-date"

    _duckdb.TransactionException:
    TransactionContext Error: Current transaction is aborted (please ROLLBACK)

Purpose: Diagnose why an intentional invalid-date failure caused
the rollback test to fail.

Resolution: Updated the temporary DataFrame cleanup behavior in
`src/publish.py`. The rollback test subsequently passed.

### Prompt 10 — Continue after rollback tests

"Next"

Purpose: Add structured logging, reconciliation reports, and
pipeline run metrics.

## 4. Large Dataset and Performance Work

### Prompt 11 — Continue after reconciliation reporting

"Next"

Purpose: Generate reproducible large datasets and build a benchmark.

### Prompt 12 — Continue after the initial benchmark

"Next"

Purpose: Optimize duplicate-key detection after measuring the
validation bottleneck.

### Prompt 13 — Review benchmark optimization

"Your next action: Replace the function, run all eight tests,
and then run the three-iteration benchmark."

Purpose: Validate that the optimization preserved correctness
and measure runtime and throughput again.

### Prompt 14 — Continue to final project preparation

"proceed with next steps"

Purpose: Complete documentation, requirements, repository hygiene,
and the GitHub submission workflow.

## 5. Prompt History Format Preference

### Prompt 15 — Record only relevant prompts and errors

"yes the files exits
make the prompt history,but don't include all output pastes just query and error occur prompts.
what do you suggests"

Purpose: Create a concise prompt-history document focused on
requests and troubleshooting rather than routine successful
terminal output.

## 6. GitHub Repository Setup

### Prompt 16 — Confirm the correct publication workflow

"before doing that we need to connect our git repository right??"

Purpose: Confirm that the local Git project should be connected
to its GitHub remote before publishing.

### Issue 4 — GitHub URL entered as a command

The repository URL was pasted directly into PowerShell:

    https://github.com/Subbu2542/yottaflex-data-pipeline.git

Error:

    The term 'https://github.com/Subbu2542/yottaflex-data-pipeline.git'
    is not recognized as the name of a cmdlet, function, script file,
    or operable program.

Purpose: Diagnose the PowerShell error when attempting to connect
the local project to GitHub.

Resolution: Used the URL with `git remote add origin`.

### Issue 5 — Local Git repository not initialized

Command:

    git status --short

Error:

    fatal: not a git repository (or any of the parent directories): .git

Purpose: Diagnose the missing local Git repository during setup.

Resolution: Initialized Git in the project directory and configured
the `main` branch and `origin` remote.

## 7. Other AI Tools

This record covers the documented ChatGPT project interactions.
If Gemini, Claude, or another AI tool was used, add its actual project
prompts and relevant errors here under a separate heading.

Do not invent prompts, claim that an unused AI tool was used, or
represent a reconstructed summary as a verbatim export.

## 8. Candidate Review

Before submission, compare this record with the original AI conversation
and add any project prompts that are missing. Preserve the actual wording
where available. Assistant responses are optional under the candidate
project FAQ; prompts are required.

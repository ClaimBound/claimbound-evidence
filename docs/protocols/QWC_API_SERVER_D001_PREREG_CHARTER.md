# QWC_API_SERVER_D001 Pre-Registration Charter

Status: draft scaffold. This file is not a completed evidence record.

Created: 2026-05-26

## Claim Boundary

This track may check only one narrow software-development behavior for QWC_API_SERVER under a frozen local protocol. It must not claim production readiness, broad project correctness, certification or correctness outside this protocol.

## Source

- Source name: QWC_API_SERVER local development source boundary
- Source URL: local or private source note to be recorded by the operator
- Domain: software-development
- Audience: software developers and maintainers
- Execution mode: AUTOMATED_AI_ASSISTED or MANUAL_NO_AI

## Fields To Freeze Before Execution

- exact narrow software claim;
- repository, branch and commit hash;
- local environment summary;
- endpoint, command, fixture or golden-vector manifest;
- payload publication policy;
- pass, negative, blocked and insufficient-coverage decision rules;
- expected report paths and report hashes;
- forbidden after-result changes;
- stop conditions.

## Stop Conditions

Stop and record an honest blocked or insufficient status when the source boundary, fixtures, environment, command logs, hashes or publication boundary are not good enough for a fair run.

## Non-Replacement Rule

This protocol can complement tests and code review. It must not be cited as a replacement for the project's normal software test suite, CI, maintainer review or release engineering.

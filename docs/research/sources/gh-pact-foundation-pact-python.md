---
id: "gh-pact-foundation-pact-python"
type: "github"
url: "https://github.com/pact-foundation/pact-python"
raw_url: "https://github.com/pact-foundation/pact-python"
tags: ["api-testing", "ci-cd", "consumer-driven-contracts", "contract-testing", "integration-testing", "microservices", "mock-server", "pact", "pact-broker", "python", "repo"]
linked_files: []
relevance: "Useful when a project needs to decouple service integration testing from full environments—especially for microservices or APIs where teams want fast local tests, safe deployments, and automated detection of breaking contract changes between consumers and providers."
ingested_at: "2026-06-10 17:06 UTC"
---

# pact-foundation/pact-python — Python version of Pact. Enables consumer driven contract testing, providing a…

## Summary

Pact Python is the official Python client for Pact, a consumer-driven contract testing framework for APIs and microservices. It lets teams replace slow, brittle end-to-end integration tests with fast, local unit tests that verify HTTP/REST and event-driven interactions via a configurable mock server and flexible matching rules. The library integrates with the broader Pact ecosystem (Broker, PactFlow, 12+ language implementations) and is maintained by the Pact Foundation with SmartBear support.

## Key claims

- Pact is described as the de-facto API contract testing tool for replacing expensive end-to-end integration tests with fast, debuggable unit tests
- Consumer-driven contract testing lets consumers define expected interactions and providers verify they honor those contracts
- Supports HTTP/REST APIs and event-driven systems with a configurable mock server and matching rules to reduce test brittleness
- Integrates with Pact Broker and PactFlow for publishing, versioning, and verifying contracts in CI/CD pipelines
- Installable via pip as pact-python; targets all Python versions still supported by the PSF
- Documentation covers separate consumer and provider testing workflows, with API docs generated from code docstrings
- Collects anonymous telemetry (OS and package version only); disable with PACT_DO_NOT_TRACK=1
- Part of the pact-foundation ecosystem with community support via Slack, Stack Overflow, and GitHub Discussions

## Notes

_yours to annotate_

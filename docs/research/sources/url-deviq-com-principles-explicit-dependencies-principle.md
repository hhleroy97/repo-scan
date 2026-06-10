---
id: "url-deviq-com-principles-explicit-dependencies-principle"
type: "url"
url: "https://deviq.com/principles/explicit-dependencies-principle/"
raw_url: "https://deviq.com/principles/explicit-dependencies-principle/"
tags: ["article", "constructor-injection", "coupling", "dependency-injection", "dependency-inversion", "design-principles", "explicit-dependencies", "maintainability", "solid", "testability"]
linked_files: []
relevance: "For this project, favor constructor or parameter injection over hidden globals, static accessors, and in-method instantiation so modules declare what they need, remain easy to test with fakes, and can be swapped without searching the whole codebase for hidden collaborators."
ingested_at: "2026-06-10 18:49 UTC"
---

# Explicit Dependencies Principle

## Summary

This source explains the Explicit Dependencies Principle: classes and methods should declare every collaborator they need through constructor or method parameters, not hide them inside the implementation. It contrasts implicit dependencies (globals, static calls, direct instantiation) with explicit ones, using a C# PersonalizedResponse example refactored from a static Context to injected ILogger, IDateTime, and a Customer parameter. The principle matters because explicit dependencies improve testability, maintainability, and swap-ability of implementations.

## Key claims

- Methods and classes should explicitly require collaborating objects via constructor or method parameters.
- Implicit dependencies exist only inside a class's implementation and are absent from its public interface.
- Implicit dependencies increase maintenance cost, coupling, brittleness, and make side-effect analysis and testing harder.
- Explicit dependencies make requirements clear, support substitution in production and tests, and align with least surprise.
- Class-level dependencies belong in constructors; more local dependencies can be method parameters.
- The principle is closely related to Dependency Inversion and the Hollywood Principle (don't call us, we'll call you).

## Notes

_yours to annotate_

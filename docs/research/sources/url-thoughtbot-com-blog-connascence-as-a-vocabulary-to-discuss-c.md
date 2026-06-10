---
id: "url-thoughtbot-com-blog-connascence-as-a-vocabulary-to-discuss-c"
type: "url"
url: "https://thoughtbot.com/blog/connascence-as-a-vocabulary-to-discuss-coupling"
raw_url: "https://thoughtbot.com/blog/connascence-as-a-vocabulary-to-discuss-coupling"
tags: ["article", "code-quality", "connascence", "coupling", "dry", "enums", "magic-values", "rails", "refactoring", "software-design", "vocabulary"]
linked_files: []
relevance: "A codebase analysis or architecture-review tool can use connascence types and dimensions to classify coupling findings, prioritize refactors (stronger forms with low locality and high degree first), and give reviewers shared terms for explaining why a dependency is risky."
ingested_at: "2026-06-10 17:14 UTC"
---

# Connascence as a vocabulary to discuss Coupling

## Summary

This thoughtbot article introduces connascence as a precise vocabulary for discussing coupling beyond a simple coupled/not-coupled binary. Connascence occurs when a change in one software component requires a corresponding change in another, and it is characterized by strength, degree, and locality (with the heuristic Connascence = Strength × Degree / Locality). The piece illustrates three common forms—Connascence of Name, Position, and Meaning—with Rails examples and refactorings that move coupling toward weaker, more explicit forms.

## Key claims

- Connascence is defined as a relationship where a change in one piece of software requires a corresponding change in another.
- Coupling severity can be discussed using strength (how hard it is to discover or refactor), degree (how many components are involved), and locality (how physically close coupled components are).
- A practical heuristic for comparing connascence is Connascence = Strength × Degree / Locality, where higher locality is better.
- Connascence of Name (CoN) is the weakest form and is often unavoidable; it arises when components must agree on entity names.
- Connascence of Position (CoP) is stronger than CoN and arises when components must agree on the order or position of values, such as implicit enum ordering in Rails.
- Connascence of Meaning (CoM) is stronger still and arises when components must agree on the meaning of particular values, such as magic strings or numbers scattered through code.
- Refactoring should aim to move from stronger connascence forms to weaker ones—for example, replacing array-based enums with explicit hash mappings (CoP → CoN) or replacing magic values with named constants and predicate methods (CoM → CoN).
- Connascence’s main benefit is giving teams a shared, concrete vocabulary for coupling and DRY discussions, making code reviews and design conversations more goal-oriented and less nebulous.

## Notes

_yours to annotate_

# Pseudonym Policy for Confidential-Subject Claims

Some evidence is about a subject whose internals are confidential: a private method,
a closed model, an unpublished dataset construction. The owner can still register a
bounded claim about it without disclosing names, formulas or source code. This policy
defines how.

## What gets a pseudonym

Only the **subject** of the claim: the method, model, rule or pipeline being measured.
Everything that a reviewer needs to judge the claim stays public:

| Stays public | Replaced by a pseudonym or a hash |
| --- | --- |
| Protocol charter, decision rule and metric | Human-readable name of the private subject |
| Public data sources and their source-audit hashes | Private source code (committed only as a hash) |
| `proof_surface_hash` of the frozen protocol | Internal parameter values (committed only as a hash) |
| Result status, claim boundary, known limitations | Private run logs (committed only as a hash) |

## Pseudonym format

`SUBJ-<first 8 hex characters of SHA-256(secret salt + private name)>`

- The salt and the name-to-pseudonym mapping are kept by the owner **outside** this
  repository. They are never committed.
- One private subject keeps one pseudonym for its whole life, so that every card about it
  can be found and compared.
- A changed subject (new version of a private method) gets a new pseudonym; the card
  states which earlier pseudonym it supersedes.

## What a reviewer can and cannot verify

A card about a pseudonymous subject can prove:

- the claim was registered before the result (protocol hash and timestamps);
- the public data used are the data that were audited (source-audit hashes);
- a rerun with the same sealed artifact on the same data reproduces the result
  (`reproduction_attempt`, ideally by an independent operator who receives the sealed
  artifact but not its source).

It cannot prove that the private method is correct, general or better than anything
outside the frozen protocol. The `claim_boundary` of every such card must say so
explicitly, for example: "This card does not verify the internal correctness of the
pseudonymous subject; it verifies only the registered result on the audited data."

## Rules

1. A pseudonym never replaces a public data source, a protocol or a metric.
2. A negative or blocked result about a pseudonymous subject is published exactly like a
   positive one.
3. Revealing the mapping later is allowed; the pseudonym stays in the old cards and the
   reveal is recorded as a new card that references them.
4. Cards about pseudonymous subjects cannot reach a verification level above what the
   sealed-artifact rerun supports; source-level review is out of scope unless the owner
   discloses the source.

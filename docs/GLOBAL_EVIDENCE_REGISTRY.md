# Global Evidence Registry Direction

ClaimBound can grow from a single repository into a small global registry of
pre-registered public evidence records.

The goal is not to replace research repositories, benchmark suites or DOI
archives. The goal is to provide a thin, verifiable layer that links a narrow
claim to a protocol, source audit, result status, hashes and reproduction level.

## Public Access Model

The registry should be publicly readable and free to inspect.

The initial registry lives in
[docs/registry/evidence_index.json](registry/evidence_index.json). It lists
validated evidence cards, share URLs and aggregate statistics by status, domain
and source.

Future hosted versions may provide a database-backed search layer, but the
public contract stays the same:

- card metadata is public;
- aggregate statistics are public;
- raw payloads are not stored in the public registry;
- every result links back to a repository path that another operator can
  inspect.

## Registry Unit

The registry unit should be an evidence card, not a large raw dataset.

Required fields:

```text
evidence_id:
registry_sequence:
protocol_id:
protocol_version:
result_status:
claim_boundary:
source_name:
source_url:
access_date:
source_rights_note:
raw_payload_committed: false
manifest_hash:
report_hash:
repository_url:
git_commit:
operator:
last_verified_date:
verification_count:
verification_level:
reproduction_level:
created_at:
```

Optional fields:

```text
doi:
review_thread:
replication_attempts:
supersedes:
superseded_by:
```

## Trust Model

The registry should make three things easy to check:

1. The protocol existed before the reported run.
2. The public record has not silently changed.
3. Another operator can rerun the protocol and compare the status.

Trust should come from:

- source lineage;
- frozen gates;
- plain-language claim boundaries;
- public code;
- report and manifest hashes;
- independent reproduction attempts;
- visible negative and blocked outcomes.

## Storage Layers

A practical storage model is layered:

| Layer | Purpose | Suggested default |
| --- | --- | --- |
| Git repository | Code, protocols, evidence summaries | Required |
| Release archive | Stable packaged evidence records | Recommended |
| DOI repository | Long-term citation | Optional |

Raw payloads should remain outside the public repository unless the source
rights clearly allow redistribution.

## Blockchain Moratorium

Blockchain is not part of the ClaimBound roadmap. No review date is assigned for
adding it.

This moratorium includes:

- on-chain storage;
- chain-based timestamp anchoring;
- tokens;
- wallets;
- decentralized governance;
- chain-specific identity or reputation systems.

Reason:

- the current project needs trust through source lineage, frozen protocols,
  hashes, claim boundaries and reproduction;
- blockchain would add operational and communication complexity;
- a timestamp does not prove that a result is correct;
- raw payload storage and rights boundaries must stay simple.

Project rule:

```text
Do not add blockchain features, token features, wallet flows, on-chain storage
or chain timestamp requirements to the public ClaimBound roadmap.
```

## Development Phases

### Phase 1: Repository Evidence Cards

- Add an evidence-card template.
- Validate required fields in CI.
- Link cards from the README.
- Publish positive, negative and blocked examples.

### Phase 2: Small Public Registry

- Add a machine-readable registry index.
- Add stable evidence IDs.
- Add contiguous registry sequence numbers and verification metadata.
- Add query examples by source, status, domain and reproduction level.
- Add a contribution path for independent reproduction records.

### Phase 3: External Anchors

- Archive selected releases in a DOI repository.
- Keep archives secondary to the open protocol and rerun path.

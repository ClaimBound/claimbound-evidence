# Scripts Index

Scripts are maintainer and operator tooling that runs from a repository clone. The
installed `protocolith` command calls some of them (`demo`, `rerun`, `verify`); everything
else is run directly, for example `uv run python scripts/<name>.py --help`.

Nothing here is required to read or validate a card. For that, use
`protocolith validate-card FILE` or `protocolith validate-all`.

| Group | Scripts | Purpose |
| --- | --- | --- |
| Validators | `protocolith_validate_evidence_card.py`, `protocolith_validate_registry.py`, `protocolith_validate_family_ledger.py`, `protocolith_validate_family_frontier.py`, `protocolith_validate_family_tree.py` | Script entry points for the checks behind `protocolith validate-*`. |
| Card rendering | `protocolith_render_evidence_card_svg.py` | Render a card JSON to its SVG. |
| Scaffolding | `protocolith_scaffold_track.py` | Draft files for a new track; drafts are not evidence. |
| Source audits and track runners | `protocolith_run_eea_source_audit.py`, `protocolith_run_eea_manual_track.py`, `protocolith_run_eu_public_source_audit.py`, `protocolith_run_grok_prompts_source_audit.py`, `protocolith_run_public_doc_source_audit.py`, `protocolith_build_eu_evidence_cards.py` | Public-source audit runners behind the `demo` command and the EU cards. |
| Pre-registered data runners | `protocolith_run_nasa_power_prereg.py`, `fetch_nasa_power.py`, `protocolith_run_noaa_coops_prereg.py`, `fetch_noaa_coops_d131_payloads.py` | Frozen NASA POWER and NOAA CO-OPS gates (`rerun nasa-d103`, `rerun noaa-d131`). |
| Factories and atlases | `protocolith_run_esa_factory.py`, `protocolith_run_nasa_factory.py`, `esa_factory_data.py`, `nasa_factory_data.py`, `build_esa_factory_atlas.py`, `build_nasa_factory_atlas.py`, `build_esa_factory_showcase.py`, `build_nasa_issue_matrices.py`, `protocolith_run_esa_issue_131.py`, `protocolith_run_esa_issue_132.py`, `esa_issue_13*_*.py` | ESA and NASA source-boundary card factories and the pages built from them. |
| Public claim campaign | `build_public_claim_catalog.py`, `build_domain_primary_claim_manifests.py`, `build_first_700_primary_claim_manifests.py`, `build_public_claim_atlas_v2.py`, `build_verified_claim_atlas.py`, `build_wikidata_public_claims.py`, `register_*.py`, `run_domain_primary_pack.py`, `update_cb7k_primary_progress.py`, `verify_primary_public_claim_group.py`, `audit_cb7k_campaign.py`, `public_claim_atlas/` | Claim catalogs, per-domain manifests, atlases and registry updates. |
| Claim batches (historical) | `protocolith_run_claim_batch.py`, `protocolith_review_claim_batch_166_v3.py` … `protocolith_review_claim_batch_184.py`, `protocolith_run_claim_batch_166_v2.py`, `fetch_frozen_claim_sources.py`, `retry_frozen_claim_sources.py`, `readjudicate_claim_batch.py`, `analyze_claim_batch_root_causes.py`, `protocolith_gate_locator.py` | Per-batch review scripts kept for reproducibility of the published batch cards. Frozen sources are never replaced after seeing a result; see [maintainer boundary](../MAINTAINER_BOUNDARY.md). Do not edit these to change published outcomes. |
| Tool-evidence runs | `protocolith_run_headroom_*.py`, `protocolith_run_leqembi_campaign.py` | Runners for the software-tool and medical-source-boundary tracks. |
| Documentation | `gen_cli_reference.py`, `build_docs_site.py` | Regenerate `docs/CLI.md` (`--check` in CI) and assemble the MkDocs source tree. |
| GitHub settings | `github/ruleset_protect_main.json` | Branch ruleset definition for `main`. |

If a script is not listed here, run it with `--help` and add a row when you introduce it.

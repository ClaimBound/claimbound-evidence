"""Shared paths and copy constants for the public claim atlas."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "artifacts/cb7k_wikidata_public_claims.json"
PRIMARY_MANIFESTS = sorted(ROOT.glob("artifacts/cb7k_dom*_primary_claims.json"))
CARDS = ROOT / "docs/evidence_cards"
REPO = "https://github.com/ClaimBound/claimbound-evidence"
PRIMARY_SCHEMA = "CB7K-PRIMARY-PUBLIC-CLAIMS-v1"
PRIMARY_SCOPE = (
    "exact quoted statement in a named official primary PDF "
    "(SHA-256 + section locator); dual-extractor publication gate"
)
WIKIDATA_VERIFY = (
    "python3 scripts/build_wikidata_public_claims.py verify-sources "
    "artifacts/cb7k_wikidata_public_claims.json --cache .cache/claimbound-wikidata "
    "--claim-id {claim_id}"
)
PRIMARY_VERIFY = (
    "python3 scripts/verify_primary_public_claim_group.py "
    "artifacts/cb7k_domNNN_tNN_primary_claims.json --source-file <local-raw-pdf>"
)

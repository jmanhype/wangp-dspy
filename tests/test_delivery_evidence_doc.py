"""Guard the documented delivery-evidence contract against silent drift.

``pvg story verify-delivery`` is a compiled binary: its checks and its note
ordering are not editable from this repository. What *is* editable is whether the
documented procedure still matches what that binary accepts, so this test pins the
document to the verified vocabulary and proves that the worked example is itself a
well-formed delivered contract.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/delivery-evidence.md"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"

# The nine checks the installed pvg reports, as verified while closing out WD-t741.
CHECK_NAMES = (
    "label:delivered",
    "nd_contract:last_block",
    "nd_contract:eof",
    "notes:implementation_evidence",
    "notes:ci_test_results",
    "notes:commands_run",
    "notes:summary",
    "notes:commit_sha",
    "proof:ac_items",
)

# The exact literals the verifier matches; each must be documented verbatim.
REQUIRED_LITERALS = (
    "## Implementation Evidence",
    "### CI/Test Results",
    "### AC Verification",
    "Commands run:",
    "Summary:",
    "SHA: ",
    "| AC | Result | Evidence |",
    "status: delivered",
)

# Claims the document must make about the verifier's real matching behaviour,
# verified against the shipped binary. Each is (text, because) so a failure says
# which fact drifted.
REQUIRED_FACTS = (
    ("### Test Results", "the alternate CI heading the verifier also accepts"),
    ("commands run:", "the lowercase commands-run spelling the verifier accepts"),
    ("case-insensitive", "the SHA check accepts upper and lower hex"),
    ("[x] AC", "the checklist form that satisfies proof:ac_items"),
    ("does **not** match a table header",
     "the table header alone does not satisfy proof:ac_items"),
    ("(?m)(^\\[x\\] AC|^### AC Verification$)",
     "the observed pattern for proof:ac_items"),
)


def _fenced_blocks(text: str) -> list[str]:
    """Contents of every triple-backtick fenced block, in document order."""
    parts = text.split("```")
    # Odd indices are the contents between fence markers.
    return parts[1::2]


def test_contract_documents_every_check_and_literal() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    missing_checks = [name for name in CHECK_NAMES if name not in text]
    assert not missing_checks, f"delivery-evidence.md omits checks: {missing_checks}"
    missing_literals = [item for item in REQUIRED_LITERALS if item not in text]
    assert not missing_literals, (
        f"delivery-evidence.md omits required literals: {missing_literals}")
    missing_facts = [
        because for needle, because in REQUIRED_FACTS if needle not in text]
    assert not missing_facts, (
        "delivery-evidence.md no longer states: " + "; ".join(missing_facts))
    # The post-acceptance caveat is part of the contract too: acceptance drops the
    # delivered label, so a re-run legitimately reports 8 of 9.
    assert "Passed: 8" in text, "post-acceptance caveat is not documented"
    assert "delivered' label" in text, "the dropped-label cause is not documented"


def test_documented_example_is_a_valid_delivered_contract() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    examples = [block for block in _fenced_blocks(text) if "## nd_contract" in block]
    assert examples, "delivery-evidence.md has no worked example with a contract block"

    example = examples[-1]
    last = example.rindex("## nd_contract")
    tail = example[last:]
    assert "status: delivered" in tail, (
        "the worked example's last contract block is not delivered")
    proof_items = [line for line in tail.splitlines() if line.strip().startswith("- [x] ")]
    assert proof_items, "the worked example carries no checked proof items"
    assert "### proof" in tail, "the worked example has no proof section"


def test_contributing_and_readme_link_the_contract() -> None:
    contributing = CONTRIBUTING.read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/delivery-evidence.md" in contributing, (
        "CONTRIBUTING.md does not point at the delivery-evidence contract")
    assert "docs/delivery-evidence.md" in readme, (
        "README documentation index does not link the delivery-evidence contract")

"""Check caller-authenticated receipts, never execute commands or authenticate their issuer."""
from pathlib import Path

from .memory.models import canonical, digest, validate
from .memory.operational_io import read_json
from .workspace import MemoryInputError


def verify_receipts(witnesses, tests, required, selected, code_set, document, policy_hash, report):
    observed = {}
    for witness in witnesses:
        receipt = read_json(Path(witness["path"]))
        validate("execution-receipt", receipt)
        # This witness must be constructed by trusted CI after checking producer/run/artifact
        # identity. Copying a digest from a PR is NOT authentication of a receipt.
        if digest(canonical(receipt)) != witness["digest"]:
            report.add("EVI001", "evidence", "receipt bytes do not match the CI-authenticated digest")
            continue
        name = receipt["test"]
        spec = tests.get(name)
        if (name in observed or not spec or receipt["producer"] != witness["producer"]
                or receipt["run"] != witness["run"]
                or witness["producer"] != spec["producer"]):
            report.add("EVI001", "evidence", "duplicate test, unknown test or unauthenticated producer/run")
            continue
        observed[name] = receipt
        if (receipt["code_set"] != code_set or receipt["document"] != document
                or receipt["policy_hash"] != policy_hash or receipt["command"] != spec["command"]):
            report.add("EVI002", name, "receipt does not attest this exact code set, mandate, policy and command")
        if receipt["result"] != "passed" or receipt["exit_code"] != 0:
            report.add("EVI003", name, "test did not pass")
    for name in sorted(required - observed.keys()):
        report.add("EVI003", name, "mandatory test has no authenticated execution receipt")
    if any(name not in tests for name in selected):
        raise MemoryInputError("a selected fast-cycle test is not declared in the trusted policy")
    return dict(mandatory=sorted(required), selected=sorted(selected),
                received=sorted(observed), execution="not-performed",
                trust="issuer-and-artifact-authentication-is-the-calling-CI-boundary")

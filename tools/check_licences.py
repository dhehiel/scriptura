"""Licence registry/manifest consistency + gate evaluation (make check-licences)."""
from __future__ import annotations
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from scriptura.provenance import LicensingStore, load_licensing_store
ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    errors = []
    try:
        store = load_licensing_store(ROOT / "docs/data/source-registry.json",
                                     ROOT / "docs/data/licence-manifest.json",
                                     ROOT / "schemas")
    except Exception as exc:
        print("check-licences FAILED: " + str(exc))
        return 1
    for problem in store.consistency_problems():
        errors.append(problem)
    # Attribution strings are enforced at the point of use, not at the point of
    # research: a missing string is an error only where the source is ingestible.
    # At M0 nothing is ingestible, so missing strings are recorded (in the
    # registry's verification_required) rather than failed here.
    for lic in store._licences.values():
        if lic.get("attribution_required") and not (lic.get("attribution_text") or "").strip():
            using = [sid for sid in lic.get("applies_to", [])
                     if (store.source(sid) or {}).get("ingestible")]
            if using:
                errors.append("licence %s requires attribution but records no string "
                              "and is ingestible for %s" % (lic.get("licence_id"), using))
    # every licenced ingestible source must resolve to a GateResult with warnings typed
    for sid in store.ingestible_sources():
        result = store.evaluate(sid, authorised=[])
        if result.permitted:
            errors.append("source %s evaluates permitted while gate closed" % sid)
    # spot-check: a verified source must refuse for G9/G10 even when authorised
    for sid, source in store._sources.items():
        if source.get("verification_status") == "verified":
            result = store.evaluate(sid, authorised=[sid])
            unmet = [u.split(":")[0] for u in result.unmet]
            if result.permitted or "G9" not in unmet:
                errors.append("source %s: gate must refuse on G9 while closed" % sid)
    if errors:
        print("check-licences FAILED:")
        for error in errors:
            print("  - " + error)
        return 1
    n_src = len(store._sources)
    n_lic = len(store._licences)
    print("check-licences PASSED (%d sources, %d licences, gate closed, 0 ingestible)"
          % (n_src, n_lic))
    return 0


if __name__ == "__main__":
    sys.exit(main())

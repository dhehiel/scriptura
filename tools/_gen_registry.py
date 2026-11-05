#!/usr/bin/env python3
"""Generate docs/data/source-registry.json and docs/data/licence-manifest.json.

Every 'verified' entry below records evidence actually retrieved from a primary source
on 2026-11-05. Nothing is asserted from recollection. Entries whose licence could not
be established are recorded honestly as 'unverified' or 'absent' and are NOT ingestible.
"""
import json, pathlib

ROOT = pathlib.Path("/workspace")
RETRIEVED = "2026-11-05"

S = []  # source registry entries
L = []  # licence records


def src(**kw):
    S.append(kw)


def lic(**kw):
    L.append(kw)


# ---------------------------------------------------------------- VERIFIED ----

src(
    source_id="src-sblgnt",
    name="SBL Greek New Testament (SBLGNT)",
    edition="SBLGNT",
    category="scripture_text",
    languages=["grc"],
    rights_holder="Faithlife / Logos Bible Software, per the licence page footer. "
                  "Joint attribution to the Society of Biblical Literature is commonly stated "
                  "but was NOT verified from the licence page itself.",
    availability="unknown",
    licence="CC BY 4.0",
    licence_url="https://www.sblgnt.com/license/",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="SBL Greek New Testament - End User License Agreement Creative Commons "
                   "Attribution 4.0 International Public License",
    verification_status="verified",
    licence_cleared=True,
    ingestible=False,
    derivatives_permitted=True,
    commercial_use_permitted=True,
    share_alike=False,
    attribution_required=True,
    attribution_text=None,
    licensing_model="single",
    canonical_url="https://www.sblgnt.com/",
    citation=None,
    notes="Licence page retrieved 2026-11-05 and found to contain the full text of the "
          "Creative Commons Attribution 4.0 International Public License. The page footer "
          "reads 'Copyright Faithlife / Logos Bible Software'. Download availability was NOT "
          "verified from this page and is recorded as unknown. CC BY 4.0 requires attribution; "
          "the exact attribution wording the rights holder expects was not stated on the page "
          "and must be confirmed before redistribution.",
    verification_required=[
        "Confirm the download location and access conditions.",
        "Confirm the exact attribution wording expected by the rights holder.",
        "Confirm whether copyright is held jointly with the Society of Biblical Literature.",
    ],
    target_milestone="M1",
)
lic(
    licence_id="lic-cc-by-4-0-sblgnt",
    applies_to=["src-sblgnt"],
    licence="CC BY 4.0",
    rights_holder="Faithlife / Logos Bible Software (per licence page footer)",
    licence_url="https://www.sblgnt.com/license/",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="Creative Commons Attribution 4.0 International Public License",
    verification_status="verified",
    derivatives_permitted=True,
    commercial_use_permitted=True,
    share_alike=False,
    share_alike_consequence=None,
    non_commercial_quarantine=False,
    attribution_required=True,
    attribution_text=None,
    public_domain_basis=None,
    licensing_model="single",
    layer_split=None,
    notes="CC BY 4.0 is permissive: reproduction, sharing and adaptation are permitted for any "
          "purpose including commercial, subject to attribution. The licence text also notes the "
          "licensor may offer the material under separate terms or stop distributing it, without "
          "terminating the licence already granted. Exact attribution wording must be confirmed "
          "with the rights holder before redistribution.",
    verification_required=["Confirm the exact attribution wording expected by the rights holder."],
)

src(
    source_id="src-oshb",
    name="Open Scriptures Hebrew Bible (morphhb)",
    edition="morphhb, master branch",
    category="morphology",
    languages=["heb"],
    rights_holder="Open Scriptures",
    availability="open_download",
    licence="CC BY 4.0",
    licence_url="https://raw.githubusercontent.com/openscriptures/morphhb/master/LICENSE.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="Creative Commons Attribution 4.0 International (CC BY 4.0) ... You must "
                   "attribute the work as follows: \"Original work of the Open Scriptures Hebrew "
                   "Bible available at https://github.com/openscriptures/morphhb\"",
    verification_status="verified",
    licence_cleared=True,
    ingestible=False,
    derivatives_permitted=True,
    commercial_use_permitted=True,
    share_alike=False,
    attribution_required=True,
    attribution_text="Original work of the Open Scriptures Hebrew Bible available at "
                     "https://github.com/openscriptures/morphhb",
    licensing_model="single",
    canonical_url="https://github.com/openscriptures/morphhb",
    citation=None,
    notes="LICENSE.md retrieved 2026-11-05. The licence file states the work 'is based on The "
          "Westminster Leningrad Codex, which is in the public domain' and applies CC BY 4.0 with "
          "a specified attribution string. IMPORTANT: the public-domain status of the Westminster "
          "Leningrad Codex is an assertion made by Open Scriptures, not independently verified by "
          "Scriptura; see src-wlc. The attribution string must be reproduced verbatim.",
    verification_required=[
        "Independently verify the licence status of the Westminster Leningrad Codex itself "
        "(see src-wlc) rather than relying on Open Scriptures' assertion.",
    ],
    target_milestone="M1",
)
lic(
    licence_id="lic-cc-by-4-0-oshb",
    applies_to=["src-oshb"],
    licence="CC BY 4.0",
    rights_holder="Open Scriptures",
    licence_url="https://raw.githubusercontent.com/openscriptures/morphhb/master/LICENSE.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="You must attribute the work as follows: \"Original work of the Open Scriptures "
                   "Hebrew Bible available at https://github.com/openscriptures/morphhb\"",
    verification_status="verified",
    derivatives_permitted=True,
    commercial_use_permitted=True,
    share_alike=False,
    share_alike_consequence=None,
    non_commercial_quarantine=False,
    attribution_required=True,
    attribution_text="Original work of the Open Scriptures Hebrew Bible available at "
                     "https://github.com/openscriptures/morphhb",
    public_domain_basis=None,
    licensing_model="single",
    layer_split=None,
    notes="Permissive with a mandatory verbatim attribution string. The licence file also notes "
          "that compliance is not required for elements already in the public domain, and that the "
          "licence may not grant all permissions necessary for an intended use.",
    verification_required=[],
)

src(
    source_id="src-bsb",
    name="Berean Standard Bible (BSB)",
    edition="Berean Standard Bible",
    category="translation",
    languages=["eng"],
    rights_holder="Bible Hub / Berean Bible Translation Committee (dedicated to the public domain)",
    availability="open_download",
    licence="Public domain (dedication dated 2023-04-30)",
    licence_url="https://berean.bible/terms.htm",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="The Berean Bible and Majority Bible texts are officially dedicated to the "
                   "public domain as of April 30, 2023. All uses are freely permitted. "
                   "Attribution Notice (appreciated but not required).",
    verification_status="verified",
    licence_cleared=True,
    ingestible=False,
    derivatives_permitted=True,
    commercial_use_permitted=True,
    share_alike=False,
    attribution_required=False,
    attribution_text="The Holy Bible, Berean Standard Bible, BSB is produced in cooperation with "
                     "Bible Hub, Discovery Bible, OpenBible.com, and the Berean Bible Translation "
                     "Committee. This text of God's Word has been dedicated to the public domain.",
    licensing_model="single",
    canonical_url="https://berean.bible/",
    citation=None,
    notes="Terms page retrieved 2026-11-05. IMPORTANT CORRECTION TO A COMMON ASSUMPTION: the Berean "
          "texts were previously distributed under a Creative Commons licence and are frequently "
          "still described that way. As of 2023-04-30 they are dedicated to the public domain and "
          "all uses are freely permitted; attribution is appreciated but not required. The page "
          "states that derivatives varying from the official text are respectfully requested not to "
          "use the Berean name. That naming request is a request, not a licence condition, but "
          "Scriptura will honour it.",
    verification_required=[
        "Confirm the exact release/version identifier of the text actually retrieved at ingestion "
        "time, since the dedication covers the texts as published.",
    ],
    target_milestone="M1",
)
lic(
    licence_id="lic-public-domain-berean",
    applies_to=["src-bsb"],
    licence="Public domain (dedication dated 2023-04-30)",
    rights_holder="Bible Hub / Berean Bible Translation Committee",
    licence_url="https://berean.bible/terms.htm",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="officially dedicated to the public domain as of April 30, 2023. All uses are "
                   "freely permitted.",
    verification_status="verified",
    derivatives_permitted=True,
    commercial_use_permitted=True,
    share_alike=False,
    share_alike_consequence=None,
    non_commercial_quarantine=False,
    attribution_required=False,
    attribution_text="The Holy Bible, Berean Standard Bible, BSB is produced in cooperation with "
                     "Bible Hub, Discovery Bible, OpenBible.com, and the Berean Bible Translation "
                     "Committee. This text of God's Word has been dedicated to the public domain.",
    public_domain_basis="Explicit dedication by the rights holder, dated 2023-04-30, stated on the "
                        "rights holder's own terms page. This is a dedication, not an expiry of "
                        "term. No jurisdictional caveat was stated by the rights holder.",
    licensing_model="single",
    layer_split=None,
    notes="An explicit public-domain dedication by the rights holder is the strongest available "
          "basis and does not depend on term-expiry analysis. Attribution is not required but the "
          "string is recorded so that Scriptura can attribute voluntarily. The request not to use "
          "the Berean name for texts that vary from the official text is honoured as a matter of "
          "good practice.",
    verification_required=[],
)

src(
    source_id="src-etcbc-bhsa",
    name="ETCBC BHSA (Biblia Hebraica Stuttgartensia Amstelodamensis, Text-Fabric)",
    edition="etcbc/bhsa, Text-Fabric dataset",
    category="morphology",
    languages=["heb", "arc"],
    rights_holder="Eep Talstra Centre for Bible and Computer, VU University Amsterdam",
    availability="open_download",
    licence="CC BY-NC 4.0",
    licence_url="https://github.com/ETCBC/bhsa/blob/master/README.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="This work is licensed under a Attribution-NonCommercial 4.0 International "
                   "(CC BY-NC 4.0) ... do not use the data for commercial applications without "
                   "consent; for any commercial use, please contact the German Bible Society.",
    verification_status="verified",
    licence_cleared=True,
    ingestible=False,
    derivatives_permitted=True,
    commercial_use_permitted=False,
    share_alike=False,
    attribution_required=True,
    attribution_text="Cite the persistent identifier 10.17026/dans-z6y-skyh",
    licensing_model="single",
    canonical_url="https://github.com/ETCBC/bhsa",
    citation="10.17026/dans-z6y-skyh",
    notes="README retrieved 2026-11-05. NON-COMMERCIAL: the data and Scriptura derivatives of it "
          "must be quarantined from any commercial distribution channel. The README states that "
          "commercial use requires contacting the German Bible Society, which indicates that "
          "underlying rights in the BHS text are held separately from the ETCBC annotation; this is "
          "a layered-rights situation even though the annotation licence is stated as single. "
          "Attribution is by persistent DOI. The extended family (dss, extrabiblical, peshitta, "
          "syrnt) was not individually licence-checked and must be verified separately.",
    verification_required=[
        "Verify the licence of each extended-family dataset separately (dss, extrabiblical, "
        "peshitta, syrnt). The bhsa licence does not establish rights for them.",
        "Confirm with the German Bible Society what commercial consent would require, if commercial "
        "use is ever contemplated.",
    ],
    target_milestone="M2",
)
lic(
    licence_id="lic-cc-by-nc-4-0-etcbc",
    applies_to=["src-etcbc-bhsa"],
    licence="CC BY-NC 4.0",
    rights_holder="Eep Talstra Centre for Bible and Computer, VU University Amsterdam",
    licence_url="https://github.com/ETCBC/bhsa/blob/master/README.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="do not use the data for commercial applications without consent; for any "
                   "commercial use, please contact the German Bible Society",
    verification_status="verified",
    derivatives_permitted=True,
    commercial_use_permitted=False,
    share_alike=False,
    share_alike_consequence=None,
    non_commercial_quarantine=True,
    attribution_required=True,
    attribution_text="Cite the persistent identifier 10.17026/dans-z6y-skyh",
    public_domain_basis=None,
    licensing_model="single",
    layer_split="The ETCBC annotation is licensed CC BY-NC 4.0 by the ETCBC. The README's direction "
                "to contact the German Bible Society for commercial use indicates separate "
                "underlying rights in the BHS text. Both must be respected.",
    notes="QUARANTINE REQUIRED. This dataset and any Scriptura derivative of it must be marked "
          "commercial_use_permitted=false and excluded from any commercial distribution channel. "
          "Mixing this material into a permissively-licensed Scriptura data product is prohibited "
          "by .clinerules/050-data-licensing.md section 6.",
    verification_required=[],
)

src(
    source_id="src-morphgnt-sblgnt",
    name="MorphGNT: SBLGNT Edition",
    edition="Version 6.12",
    category="morphology",
    languages=["grc"],
    rights_holder="MorphGNT project (editor J. K. Tauber); underlying text per the SBLGNT licence",
    availability="open_download",
    licence="Layered: annotation CC-BY-SA (version not stated); underlying SBLGNT text per SBLGNT terms",
    licence_url="https://github.com/morphgnt/sblgnt/blob/master/README.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="The SBLGNT text itself is subject to the SBLGNT EULA and the morphological "
                   "parsing and lemmatization is made available under a CC-BY-SA License.",
    verification_status="disputed",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=True,
    commercial_use_permitted=None,
    share_alike=True,
    attribution_required=True,
    attribution_text="Tauber, J. K., ed. (2017) MorphGNT: SBLGNT Edition. Version 6.12 [Data set]. "
                     "https://github.com/morphgnt/sblgnt DOI: 10.5281/zenodo.376200",
    licensing_model="layered",
    canonical_url="https://github.com/morphgnt/sblgnt",
    citation="Tauber, J. K., ed. (2017) MorphGNT: SBLGNT Edition. Version 6.12 [Data set]. "
             "https://github.com/morphgnt/sblgnt DOI: 10.5281/zenodo.376200",
    notes="README retrieved 2026-11-05. This is the canonical example of LAYERED licensing: the "
          "annotation and the underlying text carry different licences, and both must be resolved. "
          "The README states 'CC-BY-SA' WITHOUT a version number, and refers to the 'SBLGNT EULA' "
          "rather than naming CC BY 4.0; the SBLGNT licence page itself was verified to contain the "
          "CC BY 4.0 text (see src-sblgnt), but the discrepancy in how the two sources describe the "
          "same licence must be resolved before ingestion. Marked NOT ingestible pending that "
          "resolution. Share-alike: any Scriptura derivative of the annotation inherits CC BY-SA.",
    verification_required=[
        "Resolve which CC BY-SA version applies to the annotation (the README does not state one).",
        "Reconcile the README's reference to a 'SBLGNT EULA' with the CC BY 4.0 text published at "
        "the SBLGNT licence page.",
        "Confirm commercial-use status once the share-alike version is known.",
    ],
    target_milestone="M2",
)
lic(
    licence_id="lic-layered-morphgnt",
    applies_to=["src-morphgnt-sblgnt"],
    licence="Layered: annotation CC-BY-SA (version not stated); underlying SBLGNT text per SBLGNT terms",
    rights_holder="MorphGNT project; underlying text per the SBLGNT rights holder",
    licence_url="https://github.com/morphgnt/sblgnt/blob/master/README.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="The SBLGNT text itself is subject to the SBLGNT EULA and the morphological "
                   "parsing and lemmatization is made available under a CC-BY-SA License.",
    verification_status="disputed",
    derivatives_permitted=True,
    commercial_use_permitted=None,
    share_alike=True,
    share_alike_consequence="If CC BY-SA applies to the annotation, Scriptura derivatives of the "
                            "annotation inherit that licence and are NOT relicensed under Apache "
                            "2.0. The inherited licence must be recorded on every derived record.",
    non_commercial_quarantine=None,
    attribution_required=True,
    attribution_text="Tauber, J. K., ed. (2017) MorphGNT: SBLGNT Edition. Version 6.12 [Data set]. "
                     "https://github.com/morphgnt/sblgnt DOI: 10.5281/zenodo.376200",
    public_domain_basis=None,
    licensing_model="layered",
    layer_split="Annotation (morphological parsing and lemmatization): CC-BY-SA, version unstated. "
                "Underlying text: SBLGNT terms, described as an 'EULA' in the README and as CC BY "
                "4.0 on the SBLGNT licence page.",
    notes="Recorded as 'disputed', not 'verified', because the share-alike version is unstated and "
          "two sources describe the underlying text licence differently. Under "
          ".clinerules/050-data-licensing.md section 5, 'disputed' blocks ingestion. This entry "
          "exists to record the discrepancy so it is resolved rather than guessed.",
    verification_required=[
        "Establish the CC BY-SA version for the annotation.",
        "Reconcile the two descriptions of the underlying text licence.",
    ],
)

src(
    source_id="src-stepbible-data",
    name="STEPBible-Data",
    edition="STEPBible-Data repository, master branch",
    category="reference_data",
    languages=["heb", "grc", "eng"],
    rights_holder="STEP Bible (Charitable Incorporated Organisation, UK #1193950); data created "
                  "initially by Tyndale House Cambridge",
    availability="open_download",
    licence="CC BY 4.0",
    licence_url="https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/README.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="# STEPBible Data Repository  **CC BY 4.0** ... And you should: * **Credit it** "
                   "to \"STEP Bible\" linked to www.STEPBible.org",
    verification_status="verified",
    licence_cleared=True,
    ingestible=False,
    derivatives_permitted=True,
    commercial_use_permitted=True,
    share_alike=False,
    attribution_required=True,
    attribution_text='Credit to "STEP Bible" linked to www.STEPBible.org',
    licensing_model="single",
    canonical_url="https://github.com/STEPBible/STEPBible-Data",
    citation=None,
    notes="README retrieved 2026-11-05. The repository as a whole is stated to be CC BY 4.0, with "
          "credit to 'STEP Bible'. CAVEAT REQUIRING SEPARATE VERIFICATION: the repository includes "
          "TTESV (Translators Tags for ESV), which are tags applied to the translated text of the "
          "ESV. The ESV text itself is a separately copyrighted modern translation whose terms were "
          "NOT verified by Scriptura. The CC BY 4.0 statement covers STEPBible's own data; it does "
          "not and cannot establish rights in a third party's Bible translation. TTESV and any "
          "dataset embedding a modern copyrighted translation must be verified separately and are "
          "NOT covered by this entry.",
    verification_required=[
        "Verify the licence of the ESV text separately before ingesting TTESV or anything embedding "
        "ESV text.",
        "Verify each individual dataset in the repository (TAHOT, TAGNT, ProperNames, and others) "
        "where its content derives from a third-party source rather than from Tyndale House work.",
    ],
    target_milestone="M2",
)
lic(
    licence_id="lic-cc-by-4-0-stepbible",
    applies_to=["src-stepbible-data"],
    licence="CC BY 4.0",
    rights_holder="STEP Bible (CIO UK #1193950); data created initially by Tyndale House Cambridge",
    licence_url="https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/README.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote='Credit it to "STEP Bible" linked to www.STEPBible.org',
    verification_status="verified",
    derivatives_permitted=True,
    commercial_use_permitted=True,
    share_alike=False,
    share_alike_consequence=None,
    non_commercial_quarantine=False,
    attribution_required=True,
    attribution_text='Credit to "STEP Bible" linked to www.STEPBible.org',
    public_domain_basis=None,
    licensing_model="single",
    layer_split=None,
    notes="Permissive with attribution. The README also asks that changes be recorded and made "
          "available to subsequent users, and that mirrors link back to the repository. Those are "
          "requests accompanying the licence; Scriptura will honour them. The licence does not "
          "extend to third-party Bible translations embedded in some datasets.",
    verification_required=[],
)


# ------------------------------------- PER-ITEM LICENSING REGIMES (VERIFIED) ----
# For these sources the LICENSING MODEL is verified from a primary source, but no
# individual item is verified. An aggregator-level licence establishes nothing about
# any individual text, so no item from these sources is ingestible on this evidence.

src(
    source_id="src-sefaria-export",
    name="Sefaria-Export",
    edition="Sefaria-Export repository, master branch",
    category="aggregator",
    languages=["heb", "arc", "eng"],
    rights_holder="Per text. There is no single rights holder for the collection.",
    availability="open_download",
    licence=None,
    licence_url="https://raw.githubusercontent.com/Sefaria/Sefaria-Export/master/LICENSE.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="Each text is licensed separately, so there is no overall license for this "
                   "repository. You can find the license for each text in their JSON versions "
                   "under the `license` field. This is generally either \"Public Domain\", \"CC0\", "
                   "\"CC-BY\", \"CC-BY-SA\" or \"CC-BY-NC\".",
    verification_status="unverified",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=None,
    commercial_use_permitted=None,
    share_alike=None,
    attribution_required=None,
    attribution_text=None,
    licensing_model="per_item",
    canonical_url="https://github.com/Sefaria/Sefaria-Export",
    citation=None,
    notes="LICENSE.md retrieved 2026-11-05. This source is the canonical demonstration of why "
          "licensing must be dataset-specific and often ITEM-specific: the rights holder states "
          "explicitly that there is NO overall licence for the collection. The per-item licensing "
          "MODEL is verified from a primary source; no individual text is verified. Each text's "
          "`license` field must be read individually before that text may be ingested. Note that "
          "the stated range includes CC-BY-NC, so some items would require non-commercial "
          "quarantine. NOT ingestible as a collection under any circumstances.",
    verification_required=[
        "Read the `license` field of each individual text intended for ingestion.",
        "Record a separate registry entry and licence record for each item actually used.",
        "Apply non-commercial quarantine to any item licensed CC-BY-NC.",
    ],
    target_milestone=None,
)
lic(
    licence_id="lic-per-item-sefaria",
    applies_to=["src-sefaria-export"],
    licence=None,
    rights_holder="Per text",
    licence_url="https://raw.githubusercontent.com/Sefaria/Sefaria-Export/master/LICENSE.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="Each text is licensed separately, so there is no overall license for this "
                   "repository.",
    verification_status="unverified",
    derivatives_permitted=None,
    commercial_use_permitted=None,
    share_alike=None,
    share_alike_consequence=None,
    non_commercial_quarantine=None,
    attribution_required=None,
    attribution_text=None,
    public_domain_basis=None,
    licensing_model="per_item",
    layer_split=None,
    notes="This licence record deliberately records NO licence, because the rights holder states "
          "there is none for the collection. It exists to prevent anyone from treating the "
          "repository as licensed. Per-item resolution is mandatory.",
    verification_required=["Read the `license` field of each individual text before ingestion."],
)

src(
    source_id="src-ebible-org",
    name="eBible.org translation corpus",
    edition="eBible.org Bible List",
    category="aggregator",
    languages=["mult"],
    rights_holder="Per translation. eBible.org records the copyright owner for each translation.",
    availability="open_download",
    licence=None,
    licence_url="https://ebible.org/find/index.php",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="Listings with a white background are freely redistributable, at possibly with a "
                   "noncommercial restriction. Listings with a gray background may not be "
                   "redistributed without permission of the copyright owner.",
    verification_status="unverified",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=None,
    commercial_use_permitted=None,
    share_alike=None,
    attribution_required=None,
    attribution_text=None,
    licensing_model="per_item",
    canonical_url="https://ebible.org/",
    citation=None,
    notes="Bible List page retrieved 2026-11-05. Redistributability is determined PER TRANSLATION "
          "and is visually encoded in the listing, with some freely redistributable translations "
          "still carrying a non-commercial restriction. The listing page is not a licence for any "
          "translation; each translation's own copyright page must be read. Background colour in a "
          "web listing is not a durable machine-readable licence record, so per-translation "
          "verification is mandatory. NOT ingestible as a collection.",
    verification_required=[
        "Read the copyright page of each individual translation intended for ingestion.",
        "Record whether the translation carries a non-commercial restriction and quarantine if so.",
    ],
    target_milestone=None,
)
lic(
    licence_id="lic-per-item-ebible",
    applies_to=["src-ebible-org"],
    licence=None,
    rights_holder="Per translation",
    licence_url="https://ebible.org/find/index.php",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="Listings with a gray background may not be redistributed without permission of "
                   "the copyright owner.",
    verification_status="unverified",
    derivatives_permitted=None,
    commercial_use_permitted=None,
    share_alike=None,
    share_alike_consequence=None,
    non_commercial_quarantine=None,
    attribution_required=None,
    attribution_text=None,
    public_domain_basis=None,
    licensing_model="per_item",
    layer_split=None,
    notes="Records no licence, because none applies to the collection. Note that 'freely "
          "redistributable' here may still carry a non-commercial restriction, so freely "
          "redistributable does not imply permissive.",
    verification_required=["Read each translation's own copyright page before ingestion."],
)

src(
    source_id="src-perseus-hopper",
    name="Perseus Digital Library (Hopper)",
    edition="Perseus 4.0 / Hopper",
    category="aggregator",
    languages=["grc", "lat", "eng"],
    rights_holder="Tufts University holds the overall copyright to the Perseus Digital Library; "
                  "individual materials have varying copyright status",
    availability="open_download",
    licence=None,
    licence_url="https://www.perseus.tufts.edu/hopper/help/copyright",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="Tufts University holds the overall copyright to the Perseus Digital Library; "
                   "the materials therein ... are provided for the personal use of students, "
                   "scholars, and the public. Any commercial use or publication without "
                   "authorization is strictly prohibited. Materials within the Perseus DL have "
                   "varying copyright status.",
    verification_status="restricted",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=None,
    commercial_use_permitted=False,
    share_alike=None,
    attribution_required=None,
    attribution_text=None,
    licensing_model="per_item",
    canonical_url="https://www.perseus.tufts.edu/hopper",
    citation="Perseus Digital Library. Ed. Gregory R. Crane. Tufts University. "
             "http://www.perseus.tufts.edu",
    notes="Copyright page retrieved 2026-11-05. IMPORTANT FINDING, CONTRARY TO A COMMON ASSUMPTION: "
          "the Perseus Hopper is NOT a blanket open-licence collection. Tufts holds the overall "
          "copyright, materials are provided for personal use, commercial use or publication "
          "without authorisation is strictly prohibited, and materials have varying copyright "
          "status. Some texts are used by agreement with publishers who hold their copyrights. The "
          "page states that links are always preferable to copying, and that some materials are "
          "governed by special copyrights prohibiting reproduction outside the Perseus environment. "
          "Recorded as 'restricted': not ingestible. NOTE: this concerns the Hopper site. The Open "
          "Greek and Latin GitHub data is a separate matter and is recorded separately at "
          "src-ogl-first1kgreek.",
    verification_required=[
        "Contact the Perseus project about any specific component before use, as the copyright "
        "page itself directs.",
        "Do not treat the Hopper as a source of freely redistributable text.",
    ],
    target_milestone=None,
)
lic(
    licence_id="lic-restricted-perseus",
    applies_to=["src-perseus-hopper"],
    licence=None,
    rights_holder="Tufts University (overall); varying per material",
    licence_url="https://www.perseus.tufts.edu/hopper/help/copyright",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="Any commercial use or publication without authorization is strictly prohibited.",
    verification_status="restricted",
    derivatives_permitted=None,
    commercial_use_permitted=False,
    share_alike=None,
    share_alike_consequence=None,
    non_commercial_quarantine=True,
    attribution_required=None,
    attribution_text=None,
    public_domain_basis=None,
    licensing_model="per_item",
    layer_split=None,
    notes="'restricted' means the licence was confirmed and prohibits the intended use. Scriptura's "
          "intended use is redistribution of ingested text, which this source prohibits without "
          "authorisation. Not ingestible. A future ADR could propose a link-only integration that "
          "references Perseus URLs without copying text, which the copyright page explicitly "
          "welcomes.",
    verification_required=["Contact the Perseus project about any specific component before use."],
)


# ---------------- CANDIDATE SOURCES: LICENCE NOT ESTABLISHED (NOT INGESTIBLE) ----
# Each entry below records honestly what was attempted and what was found. None of these
# confers any rights. 'unverified' = a source exists and evidence was sought but rights were
# not established from a primary source. 'absent' = no licence information was located at M0.

src(
    source_id="src-tregelles-gnt",
    name="Tregelles' Greek New Testament (Tyndale House digitisation)",
    edition="Crosswire SWORD module 'TNT'",
    category="scripture_text",
    languages=["grc"],
    rights_holder="Not recorded in the module record consulted. Tyndale House is the digitiser.",
    availability="open_download",
    licence="CC BY-NC-SA 4.0 (as recorded by Crosswire; NOT confirmed with the rights holder)",
    licence_url="https://www.crosswire.org/sword/copyright/ModInfoCopyright.jsp?modName=TNT",
    retrieved_at=RETRIEVED,
    evidence_kind="secondary",
    evidence_quote="Module Name: TNT. Book Name: Tregelles' Greek New Testament. Distribution "
                   "License: Creative Commons: BY-NC-SA 4.0. Text Source: "
                   "http://www.tyndalehouse.com/tregelles/. Copyright Date / Holder / Contact: "
                   "[see note below] (not populated).",
    verification_status="unverified",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=True,
    commercial_use_permitted=False,
    share_alike=True,
    attribution_required=True,
    attribution_text=None,
    licensing_model="single",
    canonical_url="http://www.tyndalehouse.com/tregelles/",
    citation=None,
    notes="Crosswire module record retrieved 2026-11-05. Crosswire is a DISTRIBUTOR, not the rights "
          "holder, so this is SECONDARY evidence. Under .clinerules/050-data-licensing.md section 4 "
          "a licence determination requires a primary source, so this entry is recorded as "
          "unverified even though a specific licence is stated. The module record leaves Copyright "
          "Date and Copyright Holder unpopulated. If CC BY-NC-SA 4.0 is confirmed, the dataset "
          "would require BOTH non-commercial quarantine AND share-alike inheritance. NOT "
          "ingestible until Tyndale House confirms the licence directly.",
    verification_required=[
        "Confirm the licence with Tyndale House (the digitiser) rather than relying on the "
        "Crosswire module record.",
        "Establish the copyright holder and date.",
    ],
    target_milestone=None,
)

src(
    source_id="src-ogl-first1kgreek",
    name="Open Greek and Latin — First1KGreek",
    edition="First1KGreek repository, master branch",
    category="ancient_text",
    languages=["grc"],
    rights_holder="Open Greek and Latin / Perseus Digital Library (per secondary attribution)",
    availability="open_download",
    licence=None,
    licence_url="https://raw.githubusercontent.com/OpenGreekAndLatin/First1KGreek/master/README.md",
    retrieved_at=RETRIEVED,
    evidence_kind="primary",
    evidence_quote="# First1KGreek — XML files for the works in the First Thousand Years of Greek "
                   "Project. (The README states NO licence. A request for /LICENSE at the "
                   "repository root returned HTTP 404.)",
    verification_status="unverified",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=None,
    commercial_use_permitted=None,
    share_alike=None,
    attribution_required=None,
    attribution_text=None,
    licensing_model="unknown",
    canonical_url="https://github.com/OpenGreekAndLatin/First1KGreek",
    citation="DOI 10.5281/zenodo.596723",
    notes="README retrieved 2026-11-05: it states no licence, and no LICENSE file was found at the "
          "repository root (HTTP 404). A third-party catalogue attributes specific texts from this "
          "repository to 'CC BY-SA 4.0: Perseus Digital Library / Open Greek and Latin "
          "(First1KGreek)', but that is SECONDARY evidence and does not establish rights. Absence "
          "of a licence statement is NOT a public-domain statement; under copyright law the default "
          "is all rights reserved. Recorded as unverified and NOT ingestible. This is a case where "
          "the honest answer is that the licence is unknown, not that the material is free.",
    verification_required=[
        "Contact Open Greek and Latin to establish the licence for the specific works intended for "
        "use.",
        "Check for a licence file in subdirectories or in the project wiki.",
        "Do not rely on third-party catalogue attributions.",
    ],
    target_milestone=None,
)

src(
    source_id="src-beta-masaheft",
    name="Beta masaheft (Ethiopic manuscript and text corpus, Universitat Hamburg)",
    edition="BetaMasaheft/Works repository",
    category="ancient_text",
    languages=["gez"],
    rights_holder="Beta masaheft project, Universitat Hamburg (per secondary attribution)",
    availability="open_download",
    licence=None,
    licence_url="https://github.com/BetaMasaheft/Works",
    retrieved_at=None,
    evidence_kind="none",
    evidence_quote=None,
    verification_status="unverified",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=None,
    commercial_use_permitted=None,
    share_alike=None,
    attribution_required=None,
    attribution_text=None,
    licensing_model="unknown",
    canonical_url="https://github.com/BetaMasaheft/Works",
    citation=None,
    notes="NOT consulted directly at M0. A third-party catalogue attributes specific Geez texts "
          "(1 Enoch, Jubilees, from the Ethiopian Orthodox Tewahedo Church printed Bible) to "
          "'CC BY-SA 4.0 (Beta masaheft, Universitat Hamburg)' and notes that a SEPARATE scholarly "
          "edition in the same file is non-commercial only. That is SECONDARY evidence, and the "
          "note about mixed licensing within a single file is precisely the layered-licensing "
          "hazard this registry exists to surface. Recorded as unverified; the repository itself "
          "must be consulted before any use.",
    verification_required=[
        "Consult the repository's own licence statement.",
        "Determine the licence of each individual work file, since a single file may contain "
        "material under different licences.",
    ],
    target_milestone=None,
)

src(
    source_id="src-wlc",
    name="Westminster Leningrad Codex (WLC)",
    edition="Westminster Leningrad Codex",
    category="scripture_text",
    languages=["heb"],
    rights_holder="Not established",
    availability="unknown",
    licence=None,
    licence_url=None,
    retrieved_at=None,
    evidence_kind="none",
    evidence_quote=None,
    verification_status="unverified",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=None,
    commercial_use_permitted=None,
    share_alike=None,
    attribution_required=None,
    attribution_text=None,
    licensing_model="unknown",
    canonical_url=None,
    citation=None,
    notes="NOT consulted directly at M0. The Open Scriptures Hebrew Bible LICENSE.md asserts that "
          "the Westminster Leningrad Codex 'is in the public domain'. That is a SECONDARY assertion "
          "made by a downstream project, not a statement by the WLC's own publisher. The underlying "
          "Hebrew text of the Leningrad Codex is medieval and its text is not in copyright, but the "
          "digital ENCODING of a critical edition may carry its own rights, which is exactly the "
          "distinction .clinerules/050-data-licensing.md section 6 requires Scriptura to resolve. "
          "Recorded as unverified.",
    verification_required=[
        "Establish who published the digital WLC encoding and on what terms.",
        "Distinguish the rights in the medieval text from any rights in the digital encoding.",
    ],
    target_milestone=None,
)

src(
    source_id="src-kjv",
    name="King James Version / Authorised Version",
    edition="1769 Blayney standardised text",
    category="translation",
    languages=["eng"],
    rights_holder="Not established. Copyright status is jurisdiction-dependent.",
    availability="unknown",
    licence=None,
    licence_url=None,
    retrieved_at=None,
    evidence_kind="none",
    evidence_quote=None,
    verification_status="unverified",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=None,
    commercial_use_permitted=None,
    share_alike=None,
    attribution_required=None,
    attribution_text=None,
    licensing_model="unknown",
    canonical_url=None,
    citation=None,
    notes="NOT verified at M0. The KJV is widely described as public domain in most jurisdictions "
          "while being subject to a distinct status in the United Kingdom, but Scriptura did NOT "
          "read a primary source establishing either proposition and therefore asserts neither. "
          "Recording a jurisdiction-dependent status from general knowledge would be exactly the "
          "fabrication .clinerules/010-source-integrity.md prohibits. Marked unverified pending "
          "primary-source confirmation.",
    verification_required=[
        "Establish the copyright status in each jurisdiction of intended distribution from a "
        "primary source.",
        "Establish who holds any printing or distribution rights, and on what terms.",
        "Establish which specific text (1611, 1769 Blayney, or a later standardisation) would be "
        "ingested, since the editions differ.",
    ],
    target_milestone=None,
)

src(
    source_id="src-rahlfs-lxx",
    name="Septuaginta (Rahlfs-Hanhart edition)",
    edition="Rahlfs-Hanhart",
    category="scripture_text",
    languages=["grc"],
    rights_holder="Not established. Widely understood to be controlled by a German Bible Society "
                  "entity, but not verified.",
    availability="unknown",
    licence=None,
    licence_url="https://www.die-bibel.de/en/rights",
    retrieved_at=None,
    evidence_kind="none",
    evidence_quote=None,
    verification_status="absent",
    licence_cleared=False,
    ingestible=False,
    derivatives_permitted=None,
    commercial_use_permitted=None,
    share_alike=None,
    attribution_required=None,
    attribution_text=None,
    licensing_model="unknown",
    canonical_url=None,
    citation=None,
    notes="The rights page at die-bibel.de returned HTTP 403 when consulted on 2026-11-05, so no "
          "licence information was located. The failed fetch is recorded as a result, per "
          ".clinerules/010-source-integrity.md section 2 rule 4. No licence is asserted. Note that "
          "the ETCBC README separately directs commercial enquiries about its Hebrew data to the "
          "German Bible Society, which suggests that body controls rights in scholarly editions, "
          "but that is an inference and is NOT recorded as a licence determination.",
    verification_required=[
        "Retrieve the rights page by a means that succeeds, or contact the rights holder directly.",
        "Establish whether any redistribution is permitted at all.",
    ],
    target_milestone=None,
)


# ---- Remaining candidates. No licence information was located at M0. None asserted. ----


def candidate(source_id, name, edition, category, languages, notes, required,
              availability="unknown", canonical_url=None, rights_holder=None,
              licence_url=None):
    src(
        source_id=source_id, name=name, edition=edition, category=category,
        languages=languages, rights_holder=rights_holder, availability=availability,
        licence=None, licence_url=licence_url, retrieved_at=None, evidence_kind="none",
        evidence_quote=None, verification_status="absent", licence_cleared=False,
        ingestible=False,
        derivatives_permitted=None, commercial_use_permitted=None, share_alike=None,
        attribution_required=None, attribution_text=None, licensing_model="unknown",
        canonical_url=canonical_url, citation=None, notes=notes,
        verification_required=required, target_milestone=None,
    )


candidate(
    "src-thgnt", "Tyndale House Greek New Testament (THGNT)", "THGNT (2017)",
    "scripture_text", ["grc"],
    "A Crosswire module lookup for 'THGNT' returned HTTP 500 on 2026-11-05, so no licence "
    "information was located. Note that THGNT is DISTINCT from Tregelles' Greek New Testament "
    "(src-tregelles-gnt); both are Tyndale House projects and the two must not be conflated. The "
    "failed fetch is recorded as a result. No licence is asserted.",
    ["Establish the licence from Tyndale House or the publisher directly.",
     "Confirm whether any redistribution is permitted."],
)

candidate(
    "src-na28", "Novum Testamentum Graece, 28th revised edition (NA28) / UBS5",
    "NA28 / UBS5", "scripture_text", ["grc"],
    "Not researched at M0. Widely understood to be an all-rights-reserved scholarly edition whose "
    "text is not freely redistributable, but Scriptura did NOT verify this from a primary source "
    "and therefore asserts no licence status either way. Note that STEPBible's TAGNT dataset "
    "describes itself as including the words of NA27/28 among other editions, which is a separate "
    "matter governed by STEPBible's own CC BY 4.0 licence and does NOT establish rights in NA28 "
    "itself.",
    ["Establish the licence from the rights holder directly.",
     "Determine whether any part may be redistributed, and on what terms."],
)

candidate(
    "src-bhs", "Biblia Hebraica Stuttgartensia (BHS)", "BHS", "scripture_text", ["heb", "arc"],
    "Not researched at M0. The ETCBC README directs commercial enquiries about its Hebrew data to "
    "the German Bible Society, which suggests separate underlying rights in the BHS text, but that "
    "is an inference and is NOT recorded as a licence determination. The rights page at "
    "die-bibel.de returned HTTP 403 on 2026-11-05.",
    ["Establish the licence from the rights holder directly.",
     "Distinguish rights in the critical edition from rights in the underlying manuscript text."],
    licence_url="https://www.die-bibel.de/en/rights",
)

candidate(
    "src-whiston-josephus", "Josephus, Works (Whiston translation, 1737)",
    "Whiston translation", "ancient_text", ["eng"],
    "A Crosswire module lookup for 'Whiston' returned HTTP 500 on 2026-11-05, so no licence "
    "information was located. A 1737 translation is very likely out of copyright term in most "
    "jurisdictions, but Scriptura did NOT verify this and does not assert it. Modern EDITORIAL "
    "material in a contemporary printing of an old translation may carry its own rights.",
    ["Establish the status of the specific digital edition intended for use, not merely of the "
     "1737 translation.",
     "Distinguish the underlying translation from any modern editorial apparatus."],
)

candidate(
    "src-thayers", "Thayer's Greek-English Lexicon of the New Testament (1889)",
    "Thayer's Lexicon", "lexicon", ["grc", "eng"],
    "A Crosswire module lookup for 'Thayers' returned HTTP 500 on 2026-11-05, so no licence "
    "information was located. No status is asserted.",
    ["Establish the status of the specific digital edition intended for use.",
     "Distinguish the 1889 lexicon from any modern digital encoding or editorial additions."],
)

candidate(
    "src-strongs", "Strong's Exhaustive Concordance (1890)", "Strong's Concordance",
    "reference_data", ["eng", "heb", "grc"],
    "Not researched at M0. No status is asserted. Note that disambiguated or extended Strong's "
    "numbering schemes produced by later projects are separate works with their own rights, and "
    "must be verified separately.",
    ["Establish the status of the specific digital edition intended for use.",
     "Verify separately any extended or disambiguated Strong's scheme produced by a later project."],
)

candidate(
    "src-bdb", "Brown-Driver-Briggs Hebrew and English Lexicon (1906)", "BDB",
    "lexicon", ["heb", "eng"],
    "Not researched at M0. No status is asserted.",
    ["Establish the status of the specific digital edition intended for use.",
     "Distinguish the 1906 lexicon from any modern digital encoding."],
)

candidate(
    "src-davidson-talmud", "William Davidson Talmud (Steinsaltz Noe edition), as published by Sefaria",
    "Davidson Talmud", "ancient_text", ["heb", "arc", "eng"],
    "A request for sefaria.org/license returned HTTP 404 and the terms page returned only "
    "navigation content on 2026-11-05, so no licence information was located. Note that Sefaria's "
    "export repository states each text is licensed separately (see src-sefaria-export), so the "
    "licence for this specific text must be read from its own record.",
    ["Read the `license` field of this specific text in the Sefaria export data.",
     "Confirm whether the English translation carries a licence distinct from the Hebrew/Aramaic."],
    licence_url="https://github.com/Sefaria/Sefaria-Export",
)

candidate(
    "src-web", "World English Bible (WEB)", "WEB", "translation", ["eng"],
    "Not researched at M0. Frequently described as public domain, but Scriptura did NOT verify this "
    "from a primary source and does not assert it.",
    ["Establish the status from the publisher's own statement.",
     "Confirm which revision of the WEB would be ingested."],
)

candidate(
    "src-clementine-vulgate", "Clementine Vulgate (1598)", "Clementine edition",
    "translation", ["lat"],
    "Not researched directly at M0. A third-party catalogue lists a Clementine Vulgate text as "
    "public domain, but that is SECONDARY evidence and the specific copyright page was not read. "
    "The 1598 text is very likely out of copyright term, but no status is asserted. Note that the "
    "Nova Vulgata is a distinct modern edition and must be verified separately.",
    ["Establish the status of the specific digital edition intended for use.",
     "Verify the Nova Vulgata separately; it is a distinct modern edition."],
)

candidate(
    "src-nag-hammadi", "Nag Hammadi Library (Robinson translation)",
    "Robinson translation", "ancient_text", ["eng"],
    "Not researched at M0. A late-20th-century scholarly translation is very likely still in "
    "copyright term, but Scriptura did NOT verify this and asserts no status. The underlying Coptic "
    "texts are ancient and are a separate matter from the modern translation.",
    ["Establish the licence of the specific translation from its publisher.",
     "Verify separately any Coptic text edition intended for use."],
)

candidate(
    "src-brenton-lxx", "Septuagint, English translation (Brenton, 1851)",
    "Brenton translation", "translation", ["eng"],
    "Not researched at M0. No status is asserted. Note that the underlying GREEK critical editions "
    "(for example Rahlfs-Hanhart) are a separate matter with separate rights; an English "
    "translation's status says nothing about a Greek edition's status.",
    ["Establish the status of the specific digital edition intended for use.",
     "Verify any Greek edition separately."],
)

# ------------------------------------------------------------------- OUTPUT ----

registry = {
    "registry_version": "1.0.0",
    "milestone": "M0",
    "generated_at": RETRIEVED,
    "schema": "schemas/data/source-registry-entry.schema.json",
    "policy": (
        "Licensing is dataset-specific. There is no blanket licence for biblical data. An entry "
        "whose verification_status is not 'verified' confers NO rights and may NOT be ingested. "
        "A 'verified' status additionally requires an open milestone gate and per-dataset human "
        "authorisation before ingestion. Aggregator-level licences never establish rights for an "
        "individual item. See .clinerules/050-data-licensing.md and ADR-0010."
    ),
    "ingestion_gate_open": False,
    "ingestion_gate_note": (
        "CLOSED at M0. Opening requires a completed architecture review by a human reviewer, "
        "recorded with identity and date. See docs/milestones/M0-acceptance-criteria.md."
    ),
    "datasets_ingested": 0,
    "verification_status_vocabulary": {
        "verified": "Licence confirmed against a primary source, with URL and retrieval date recorded.",
        "unverified": "Candidate source under evaluation. Rights NOT established. Not ingestible.",
        "disputed": "Sources conflict or the terms are contested. Not ingestible.",
        "restricted": "Licence confirmed but prohibits the intended use. Not ingestible.",
        "absent": "No licence information located. Not ingestible.",
        "not_required": "Scriptura-authored material; Apache 2.0 applies.",
    },
    "sources": S,
}

manifest = {
    "manifest_version": "1.0.0",
    "milestone": "M0",
    "generated_at": RETRIEVED,
    "schema": "schemas/data/licence-record.schema.json",
    "policy": (
        "This manifest is the authoritative machine-readable licence record for Scriptura. It "
        "drives the ingestion licence gate implemented in src/scriptura/provenance/licensing.py. "
        "It records Scriptura's OWN code and documentation licence separately from third-party "
        "corpus data licences; conflating the two tiers is a compliance error."
    ),
    "project_licence": {
        "tier": "Scriptura's own code, specifications, schemas and documentation",
        "licence": "Apache-2.0",
        "licence_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "notice_file": "NOTICE",
        "notes": (
            "Covers only material authored by the Scriptura project. It does NOT and cannot cover "
            "ingested third-party corpus data, which is governed per dataset by its own rights "
            "holder."
        ),
    },
    "corpus_data_present": False,
    "corpus_data_note": (
        "NO third-party corpus data is present in this repository at M0. Nothing has been "
        "downloaded, vendored, committed or derived. Machine-checked by tools/check_repo.py and "
        "tests/test_repo_hygiene.py."
    ),
    "licences": L,
    "datasets": [],
    "datasets_note": (
        "EMPTY BY DESIGN. No dataset has been authorised or ingested. A dataset entry appears here "
        "only when the licence gate permits, the milestone gate is open, and a human has authorised "
        "ingestion of that specific dataset. Schema: schemas/data/dataset-manifest.schema.json."
    ),
}

out = ROOT / "docs" / "data"
out.mkdir(parents=True, exist_ok=True)
(out / "source-registry.json").write_text(
    json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
(out / "licence-manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

by_status = {}
for s in S:
    by_status[s["verification_status"]] = by_status.get(s["verification_status"], 0) + 1
print("WROTE source-registry.json and licence-manifest.json")
print(f"sources={len(S)} licences={len(L)} datasets={len(manifest['datasets'])}")
print("by verification_status:", json.dumps(by_status, sort_keys=True))
print("ingestible:", [s["source_id"] for s in S if s["ingestible"]])

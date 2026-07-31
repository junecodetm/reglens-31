# Entity-Resolution Design and Limitations

## Scope

The OFAC ownership-graph module is outside the repository's implemented scope. The repository does not ingest or distribute OpenSanctions, OFAC Sanctions List Service, or GLEIF data. This document records the retained design and its evidentiary limits; it does not describe a deployed capability. The scope decision is recorded in [CHECKLIST.md](CHECKLIST.md).

OpenSanctions is CC-BY-NC 4.0 with attribution if the module is ever enabled. Its license terms would apply independently of the repository's Apache-2.0 code license.

## Resolution model

OFAC's SDN Advanced XML data model does not publish a Legal Entity Identifier (LEI), and no official OFAC-to-LEI crosswalk exists. OpenSanctions treats GLEIF LEI data as a separate external enrichment dataset, `ext_gleif`, because OFAC does not publish LEIs. Individuals cannot hold LEIs. Joining OFAC designations to GLEIF relationship data is therefore an entity-resolution task rather than a key-based join.

The retained design uses OpenSanctions FollowTheMoney records enriched with `leiCode` through `ext_gleif` and its yente 5.0 `logic-v2` matcher. Records without an OpenSanctions link require candidate matching with `nomenklatura`, `splink`, or `rapidfuzz` over normalized names, country, and registration numbers, followed by human adjudication.

## Coverage and legal limitations

- LEI coverage of OFAC entities is sparse. Individuals cannot receive LEIs, and shell and holding companies frequently lack them. The OpenSanctions "Sanctioned Securities" collection processed on 2026-05-19 contains approximately 11,002 companies among approximately 510,885 entities; the U.S. OFAC SDN source contains approximately 37,379 entities, including many individuals and vessels. These figures are coverage proxies, not an authoritative count of OFAC entities with LEIs. Available matches are biased toward publicly listed and securities-issuing entities.
- GLEIF Level 2 coverage is limited to relationships in which the parent has an LEI and the child has not filed a reporting exception.
- GLEIF Level 2 identifies the direct or ultimate accounting consolidating parent. Accounting consolidation is a proxy for, and not equivalent to, the ownership interest addressed by OFAC's 50 Percent Rule. GLEIF and the Regulatory Oversight Committee define Level 2 through accounting consolidation rather than the classical concept of ownership.
- OFAC FAQ 398 states: "No. OFAC's 50 Percent Rule speaks only to ownership and not to control. An entity that is controlled (but not owned 50 percent or more) by one or more blocked persons is not considered automatically blocked pursuant to OFAC's 50 Percent Rule." Accounting consolidation can therefore omit ownership relationships, including ownership by natural persons without LEIs, and can include control without 50-percent ownership.
- OFAC FAQ 399 requires aggregation of ownership interests held by persons blocked under different OFAC programs. The retained design can illustrate that rule but cannot adjudicate it.

## Fixed instructional case

The retained design uses a documented Oleg Deripaska case as a reproducible instructional fixture: **Oleg Deripaska (SDN) → EN+ Group / RUSAL / Basic Element / B-Finance Ltd.** Treasury's 2018-04-06 designation, press release SM0338, named the entities as owned or controlled by Deripaska, stated that the regulated community remained responsible for compliance with OFAC's 50 Percent Rule, and cautioned that the list was not exhaustive. Under the January 2019 delisting terms, Deripaska reduced his EN+ ownership interest from 70 percent to 44.95 percent; his voting rights were limited to 35 percent, and he remained an SDN.

Within the retained design, the fixed fixture provides an offline explanation of the rule, and live matches remain additional candidates requiring human review. OpenOwnership Register, OpenCorporates, ICIJ Offshore Leaks, and European and United Kingdom company registers may provide supplementary context, but none offers a more suitable zero-cost, joinable primary source for this design. OpenCorporates bulk and API access is not fully available at zero cost.

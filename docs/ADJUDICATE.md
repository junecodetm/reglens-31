# Adjudication Worklist

Progress: **0/168 adjudicated.** Labels below are
machine-proposed (see `proposed_by`) and are NOT ground truth until you rule on them.

## How to adjudicate an item

1. Read the provision text against `docs/ANNOTATION_GUIDELINES.md`.
2. In `reglens/eval/gold/gold.jsonl`, find the line with the item's `provision_id`.
3. **Accept:** set `"adjudicated": true`. **Edit:** correct the label fields,
   then set `"adjudicated": true`. **Reject the provision entirely:** delete the line
   (and note why in your commit message).
4. Commit; the eval label and this file's counts update from the JSONL
   (`just eval` regenerates metrics; `uv run python -m reglens.eval.adjudicate`
   regenerates this worklist).

## Evening 1 (items 1-20)

### 1. `3c8441d058413908` — ⬜ pending

- **Document:** 2026-09090 (chars 0-358)
- **Provision:** <html> <head> <title>Federal Register, Volume 91 Issue 88 (Thursday, May 7, 2026)</title> </head> <body><pre> [Federal Register Volume 91, Number 88 (Thursday, May 7, 2026)] [Rules and Regulations] [Pages 24716-24719] From the Federal Register Online via the Government Publishing Office [<a href="http://www.gpo.gov">www.gpo.gov</a>] [FR Doc No: 2026-09090]
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** HTML masthead and citation boilerplate; no operative language

### 2. `6612961039830dac` — ⬜ pending

- **Document:** 2026-09090 (chars 775-1037)
- **Provision:** SUMMARY: The Department of the Treasury's Office of Foreign Assets Control (OFAC) is publishing four general licenses (GLs) issued pursuant to the Venezuela Sanctions Regulations: GLs 47, 48, 49, and 50, which were previously made available on OFAC's website.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** SUMMARY describing what OFAC is publishing; not operative text

### 3. `5873796889e7b291` — ⬜ pending

- **Document:** 2026-09090 (chars 1164-1356)
- **Provision:** FOR FURTHER INFORMATION CONTACT: OFAC: Assistant Director for Regulatory Affairs, 202-622-4855; or <a href="https://ofac.treasury.gov/contact-ofac">https://ofac.treasury.gov/contact-ofac</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Contact-information notice; imposes no duty

### 4. `fa7f293e5188e46e` — ⬜ pending

- **Document:** 2026-09090 (chars 1415-1574)
- **Provision:** This document and additional information concerning OFAC are available on OFAC's website: <a href="https://ofac.treasury.gov/">https://ofac.treasury.gov/</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Availability notice pointing to OFAC website; no duty

### 5. `948d16770e346fc0` — ⬜ pending

- **Document:** 2026-09090 (chars 7930-8650)
- **Provision:** (b) This general license does not authorize: (1) Payment terms that are not commercially reasonable, involve debt swaps or payments in gold, or are denominated in digital currency, digital coin, or digital tokens issued by, for, or on behalf of the Government of Venezuela, including the petro; (2) Any transaction involving a person located in or organized under the laws of the Russian Federation, …
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Carve-out limiting scope of an authorization; underlying prohibition lives elsewhere

### 6. `1a6ec9e822c784e4` — ⬜ pending

- **Document:** 2026-09090 (chars 10490-10590)
- **Provision:** Authorizing Negotiations of and Entry Into Contingent Contracts for Certain Investment in Venezuela
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** General license heading only; no operative language

### 7. `d34894d5411a3828` — ⬜ pending

- **Document:** 2026-09090 (chars 13193-14353)
- **Provision:** (a) Except as provided in paragraph (b) of this general license, all transactions prohibited by the Venezuela Sanctions Regulations, 31 CFR part 591 (the VSR), including those involving the Government of Venezuela, Petr[oacute]leos de Venezuela, S.A. (PdVSA), or any entity in which PdVSA owns, directly or indirectly, a 50 percent or greater interest (collectively, ``PdVSA Entities''), that are rel…
- **Proposed:** is_obligation=True, type=requirement, party=persons engaging in transactions authorized by this general license
- **Rationale (claude-fable-5):** Provisos bind: contracts must specify U.S. law; payments made into designated funds

### 8. `b4679f75de27934d` — ⬜ pending

- **Document:** 2026-09092 (chars 1151-1343)
- **Provision:** FOR FURTHER INFORMATION CONTACT: OFAC: Assistant Director for Regulatory Affairs, 202-622-4855; or <a href="https://ofac.treasury.gov/contact-ofac">https://ofac.treasury.gov/contact-ofac</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Contact-information notice; imposes no duty

### 9. `0ceedee27c929329` — ⬜ pending

- **Document:** 2026-09092 (chars 1402-1561)
- **Provision:** This document and additional information concerning OFAC are available on OFAC's website: <a href="https://ofac.treasury.gov/">https://ofac.treasury.gov/</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Availability notice pointing to OFAC website; no duty

### 10. `db9f943b4ba4aa40` — ⬜ pending

- **Document:** 2026-09092 (chars 3480-3722)
- **Provision:** Note 1 to Paragraph (a). For purposes of this general license, the term ``established U.S. entity'' means any entity organized under the laws of the United States or any jurisdiction within the United States on or before January 29, 2025.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Definition of "established U.S. entity"; definitions are not obligations

### 11. `275a385aced3b3d1` — ⬜ pending

- **Document:** 2026-09092 (chars 8161-8403)
- **Provision:** Note 1 to Paragraph (a). For purposes of this general license, the term ``established U.S. entity'' means any entity organized under the laws of the United States or any jurisdiction within the United States on or before January 29, 2025.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Definition of "established U.S. entity"; definitions are not obligations

### 12. `630d0fd30c5832d0` — ⬜ pending

- **Document:** 2026-09092 (chars 13357-13864)
- **Provision:** Note 2 to Paragraph (a). Transactions authorized by paragraph (a) include arranging shipping and logistics services, including chartering vessels, obtaining marine insurance and protection and indemnity (P&I) coverage, and arranging port and terminal services, including with port authorities or terminal operators that are part of the Government of Venezuela. Paragraph (a) also authorizes commercia…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Explanatory note enumerating what paragraph (a) authorizes; permission, not duty

### 13. `312d70664d6c3e30` — ⬜ pending

- **Document:** 2026-09092 (chars 13871-14051)
- **Provision:** Note 3 to Paragraph (a). For purposes of this general license, the term ``petrochemical products'' includes fertilizer products and fertilizer precursor chemicals, including the
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Definition of "petrochemical products"; definitions are not obligations

### 14. `978858e540e3ffbf` — ⬜ pending

- **Document:** 2026-09092 (chars 20703-20832)
- **Provision:** </pre><script data-cfasync="false" src="/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js"></script></body> </html>
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** HTML closing markup and script tag; no regulatory text

### 15. `d2d47650781a5bee` — ⬜ pending

- **Document:** 2026-09094 (chars 772-1011)
- **Provision:** SUMMARY: The Department of the Treasury's Office of Foreign Assets Control (OFAC) is publishing two general licenses (GLs) issued in the Iranian sanctions program: GLs S and T. These GLs were previously made available on OFAC's website.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** SUMMARY describing what OFAC is publishing; not operative text

### 16. `da1f616c96914b05` — ⬜ pending

- **Document:** 2026-09094 (chars 1121-1313)
- **Provision:** FOR FURTHER INFORMATION CONTACT: OFAC: Assistant Director for Regulatory Affairs, 202-622-4855; or <a href="https://ofac.treasury.gov/contact-ofac">https://ofac.treasury.gov/contact-ofac</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Contact-information notice; imposes no duty

### 17. `e533c9b4c5b3843e` — ⬜ pending

- **Document:** 2026-09094 (chars 1372-1531)
- **Provision:** This document and additional information concerning OFAC are available on OFAC's website: <a href="https://ofac.treasury.gov/">https://ofac.treasury.gov/</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Availability notice pointing to OFAC website; no duty

### 18. `b21c377775009af2` — ⬜ pending

- **Document:** 2026-09094 (chars 2434-3099)
- **Provision:** (a) Except as provided in paragraph (b) of this general license, all transactions prohibited by Executive Order (E.O.) 13902 that are ordinarily incident and necessary to one or more of the following activities involving the blocked vessels or blocked persons listed in the Annex to this general license, and any entity in which the listed blocked persons own, directly or indirectly, individually or…
- **Proposed:** is_obligation=True, type=requirement, party=persons making payments to a blocked person under this general license
- **Rationale (claude-fable-5):** Explicit proviso: payment to blocked person "must be made" into blocked interest-bearing account

### 19. `1f156326be0e5cea` — ⬜ pending

- **Document:** 2026-09094 (chars 3121-4138)
- **Provision:** (1) The safe docking and anchoring in any port, excluding ports located in Iran or the Russian Federation or Venezuela, or under the control of the Government of Iran or the Government of the Russian Federation or the Government of Venezuela, of the blocked vessels listed in the Annex to this general license (the ``Blocked Vessels''); (2) The preservation of the health or safety of the crew of any…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** List of authorized activities; provisos state eligibility facts, not duties to act

### 20. `c38255219cd8f9a2` — ⬜ pending

- **Document:** 2026-09094 (chars 5285-5402)
- **Provision:** List of Blocked Persons and Blocked Vessels Described in Paragraph (a) of General License S as of December 18, 2025:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Annex list heading; no operative language

## Evening 2 (items 21-40)

### 21. `4a56313231e28efd` — ⬜ pending

- **Document:** 2026-09094 (chars 12141-12268)
- **Provision:** Bradley T. Smith, Director, Office of Foreign Assets Control. [FR Doc. 2026-09094 Filed 5-6-26; 8:45 am] BILLING CODE 4810-AL-P
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Signature block and filing/billing codes; no duty

### 22. `3005c66ff96b5702` — ⬜ pending

- **Document:** 2026-10036 (chars 1743-2117)
- **Provision:** FOR FURTHER INFORMATION CONTACT: Karen McSweeney, Special Counsel, Graham Bannon, Counsel, and Priscilla Benner, Counsel, Chief Counsel's Office, 202-649-5490; Office of the Comptroller of the Currency, 400 7th Street SW, Washington, DC 20219. If you are deaf, hard of hearing, or have a speech disability, please dial 7-1-1 to access telecommunications relay services.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Contact information; "please dial 7-1-1" is an invitation, not a duty

### 23. `722fea2a2a923de6` — ⬜ pending

- **Document:** 2026-10036 (chars 11886-13011)
- **Provision:** The terms and conditions of escrow accounts, including whether and to what extent banks pay interest or other compensation, are ultimately a business judgment made by each bank in accordance with safe and sound banking principles. This discretion ensures that banks have the flexibility to make business decisions about how to effectively and efficiently set the terms and conditions of their escrow …
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Preamble discussion of bank business judgment and OCC rationale; no operative duty

### 24. `e956429e86f3fd99` — ⬜ pending

- **Document:** 2026-10036 (chars 16312-17193)
- **Provision:** The Federal Reserve Act and HOLA both evince clear congressional intent to provide banks with broad, discretionary real estate lending powers, which include the flexibility to make business decisions about how to effectively and efficiently set the terms and conditions of escrow accounts. Each of these statutes also provides the OCC broad discretionary grants of rulemaking authority. Additionally,…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Preamble discussion of statutory authority and bank discretion; no operative duty

### 25. `16d2fbc96aab27d1` — ⬜ pending

- **Document:** 2026-10036 (chars 24664-25757)
- **Provision:** [the plaintiff] maintains that the language and legislative history of section 371 indicate the Comptroller is permitted only to impose ``conditions and limitations'' on the lending powers of national banks, not to issue rules that would expand those powers. The short answer to this argument, as the Comptroller notes, is that permitting national banks to offer [adjustable-rate mortgages] is not a …
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Block quotation from judicial opinion and legislative history; no operative duty

### 26. `1c6169f2d7e45f62` — ⬜ pending

- **Document:** 2026-10036 (chars 58247-58689)
- **Provision:** One commenter recommended that the final rule establish boundaries that protect homeowners' escrow funds and prevent abusive or unpredictable practices. The OCC remains committed to ensuring that homeowners' escrow funds are protected against abusive practices. The OCC has determined that sufficient statutory, regulatory, and supervisory protections and practices already exist addressing this conc…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Response to comment describing OCC's determination; no operative duty

### 27. `6416e27fa1643c1d` — ⬜ pending

- **Document:** 2026-10036 (chars 68379-68776)
- **Provision:** For purposes of the Congressional Review Act, OMB makes a determination as to whether a final rule constitutes a ``major'' rule.\66\ If a rule is deemed a ``major rule'' by the OMB, the Congressional Review Act generally provides that the rule may not take effect until at least 60 days following its publication.\67\ ---------------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Describes Congressional Review Act requirements located elsewhere; description, not operative text

### 28. `29674bbb081b8f71` — ⬜ pending

- **Document:** 2026-10036 (chars 70794-70975)
- **Provision:** 0 2. Amend Sec. 34.2 by: 0 a. Redesignating paragraphs (b) and (c) as paragraphs (c) and (d), respectively; and 0 b. Adding a new paragraph (b). The addition reads as follows:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instruction to codifier; does not quote operative regulatory text

### 29. `1ec45c86ff1e04e8` — ⬜ pending

- **Document:** 2026-10037 (chars 25304-25758)
- **Provision:** \23\ For purposes of this preemption determination, the term ``State'' includes Guam and the U.S. Virgin Islands. \24\ The OCC notes, however, that the same preemption standard and analysis would apply to other State interest-on-escrow laws that have substantively equivalent terms even if they are not specifically incorporated into this final preemption determination. -----------------------------…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Footnotes defining "State" and noting preemption analysis scope; no duty

### 30. `1a42d12a1fe6f61f` — ⬜ pending

- **Document:** 2026-10037 (chars 25764-26976)
- **Provision:** Additional State laws. Commenters also recommended that the OCC expand the scope of its proposed preemption determination to address State laws that impose other kinds of requirements on escrow accounts or require the payment of interest on funds held by national banks in other similar circumstances. The OCC declines to expand the scope of this preemption determination beyond State interest-on-esc…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Comment response and preemption conclusion; declaratory, imposes no duty

### 31. `c4997a84677e7d32` — ⬜ pending

- **Document:** 2026-10037 (chars 34964-35791)
- **Provision:** The Supreme Court has also recognized that when a State law does not prevent or significantly interfere with the national bank's exercise of its powers, it is not preempted.\40\ For example, in Anderson National Bank v. Luckett, the Supreme Court contrasted the California dormant account law addressed in San Jose with a more conventional dormant account law in Kentucky. The Supreme Court found tha…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Discussion of Supreme Court preemption case law; no operative duty

### 32. `b0c12cf7ffcca246` — ⬜ pending

- **Document:** 2026-10037 (chars 35797-36319)
- **Provision:** \40\ Barnett, 517 U.S. at 33-34. \41\ 321 U.S. at 251-52. \42\ Id. at 248. \43\ See 12 CFR 7.4007(c)(5), 7.4008(e)(5), and 34.4(b)(6). The differing outcomes in San Jose and Anderson, which both addressed State dormant account laws, demonstrate that even generally applicable State infrastructure laws may be preempted if they prevent or significantly interfere with a national bank's exercise of its…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Citation footnotes with explanatory commentary; no operative duty

### 33. `4c0ec26378d9e709` — ⬜ pending

- **Document:** 2026-10037 (chars 37379-37705)
- **Provision:** \44\ 164 U.S. at 357-61. \45\ 76 U.S. at 262-63. The Court also stated that the State law ``in no manner hinder[ed]'' the national bank and imposed ``no greater interference with the functions of the bank than any other legal proceeding.'' Id. ---------------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Citation footnotes quoting case language; no operative duty

### 34. `ee844ae190ad895b` — ⬜ pending

- **Document:** 2026-10037 (chars 42669-43807)
- **Provision:** \52\ 12 U.S.C. 25b(c). Dodd-Frank also requires the OCC to (1) publish a list of preemption determinations then in effect at least quarterly; and (2) conduct periodic reviews of each determination that Federal law preempts a State consumer financial law. See 12 U.S.C. 25b(d), (g). The OCC will comply with these requirements at the appropriate time. In addition, 12 U.S.C. 43 imposes procedural requ…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Footnote describing Dodd-Frank and 12 U.S.C. 43 duties located elsewhere; description only

### 35. `6bc8c32eb02d2596` — ⬜ pending

- **Document:** 2026-10037 (chars 43863-44352)
- **Provision:** National banks are ``necessarily subject to the paramount authority of the United States.'' \56\ At the center of this system is a Federal framework for regulation and supervision that authorizes national banks to engage in the business of banking and ensures that they operate in a safe and sound manner, comply with applicable law, provide fair access to financial services, and treat customers fai…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Descriptive statement about the federal banking framework; no operative duty

### 36. `40b1e6a9d2bdf84a` — ⬜ pending

- **Document:** 2026-10116 (chars 1061-1214)
- **Provision:** DATES: Effective date: These regulations are effective on May 20, 2026. Applicability date: For dates of applicability, see Sec. 1.6050K- 1(h).
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** DATES effective/applicability notice; excluded by guidelines

### 37. `75beb432fae4b46c` — ⬜ pending

- **Document:** 2026-10116 (chars 11678-11910)
- **Provision:** The Treasury Department and IRS did not receive any comments pertaining to the proposed regulations, and no public hearing was requested or held. Accordingly, these final regulations adopt the proposed regulations without change.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Procedural statement that no comments were received; no duty

### 38. `0716ed89bdb51ebe` — ⬜ pending

- **Document:** 2026-10116 (chars 11969-12384)
- **Provision:** These final regulations are not subject to review under section 6(b) of Executive Order 12866 pursuant to the Memorandum of Agreement (July 4, 2025) between the Treasury Department and the Office of Management and Budget (OMB) regarding review of tax regulations. Therefore, a regulatory impact assessment is not required. The Executive Order 14192 designation for this rule is expected to be deregul…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Executive Order 12866 review statement; explicitly says assessment not required

### 39. `1c263627769abb4d` — ⬜ pending

- **Document:** 2026-10116 (chars 13048-14061)
- **Provision:** It is hereby certified that the final regulations will not have a significant economic impact on a substantial number of small entities pursuant to the Regulatory Flexibility Act (5 U.S.C. chapter 6). These final regulations affect partnerships for which there is a section 751(a) exchange (as defined in Sec. 1.6050K-1(a)(4)(i)). These final regulations will likely affect a substantial number of sm…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Regulatory Flexibility Act certification; describes partnership duties located in other sections

### 40. `1ede7792bc86f074` — ⬜ pending

- **Document:** 2026-10116 (chars 14101-14691)
- **Provision:** Section 202 of the Unfunded Mandate Reform Act of 1995 (UMRA) requires that agencies assess anticipated costs and benefits and take certain other actions before issuing a final rule that includes any Federal mandate that may result in expenditures in any one year by a State, local, or Tribal government, in the aggregate, or by the private sector, of $100 million (updated annually for inflation). T…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Describes UMRA section 202 requirements located elsewhere; disclaims applicability here

## Evening 3 (items 41-60)

### 41. `ef97036326d8ad04` — ⬜ pending

- **Document:** 2026-10116 (chars 14735-15319)
- **Provision:** Executive Order 13132 (Federalism) prohibits an agency from publishing any rule that has federalism implications if the rule either imposes substantial, direct compliance costs on State and local governments, and is not required by statute, or preempts State law, unless the agency meets the consultation and funding requirements of section 6 of the Executive order. These final regulations do not ha…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Describes Executive Order 13132 prohibition located elsewhere; disclaims federalism implications

### 42. `af960d46e869957c` — ⬜ pending

- **Document:** 2026-10116 (chars 16558-16929)
- **Provision:** 0 Par. 2. Section 1.6050K-1 is amended by: 0 1. Adding a heading for paragraph (c); 0 2. Revising the paragraph heading and introductory text of paragraph (c)(1); 0 3. Revising paragraph (c)(1)(i); 0 4. Removing paragraph (c)(2) and redesignating paragraph (c)(3) as new paragraph (c)(2); and 0 5. Revising paragraph (h). The addition and revisions read as follows:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instruction listing edits; does not quote operative regulatory text

### 43. `4f6a47041757e2fd` — ⬜ pending

- **Document:** 2026-11140 (chars 35146-35618)
- **Provision:** CFR 54.9816-3, 29 CFR 2590.716-3, and 45 CFR 149.30 as proposed. The Departments did not receive any comments on the proposed amendment to remove the language under 26 CFR 54.9816-8T(c)(3)(ii), 29 CFR 2590.716- 8(c)(3)(ii), and 45 CFR 149.510(c)(3)(ii) stating that a bundled payment arrangement is subject to the rules for batched disputes, and are finalizing this amendment as proposed.\27\ -------…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Preamble narrative on comments and finalizing an amendment; no operative duty

### 44. `b1b446eaeec295aa` — ⬜ pending

- **Document:** 2026-11140 (chars 42571-43601)
- **Provision:** \29\ 88 FR 75744, 75759 (November 3, 2023). The ASC X12N 835 Version 5010 (835 transaction), adopted at 45 CFR 162.1602, is the current HIPAA standard that plans and issuers must use to electronically transmit explanations of benefits (EOBs) or remittance advice information to providers and facilities. \30\ An ERA explains how a plan or issuer has adjusted claim charges based on factors like contr…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Footnote describing the HIPAA standard duty adopted at 45 CFR 162.1602 elsewhere

### 45. `c3d47ac273bff125` — ⬜ pending

- **Document:** 2026-11140 (chars 181848-183130)
- **Provision:** 8(b)(1)(iii)(A)(5), and 45 CFR 149.510(b)(1)(iii)(A)(5) that, if the open negotiation notice indicates that the QPA was not communicated by the plan or issuer with the initial payment or notice of denial of payment or other remittance advice, the responding party (if a plan or issuer) must indicate the QPA it believes to be correct, and provide documentation to support the statement (for example, …
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Preamble recounting proposed text and commenter recommendations, not operative regulation

### 46. `04cb2f418d391d7f` — ⬜ pending

- **Document:** 2026-11140 (chars 302117-302487)
- **Provision:** \86\ See 29 CFR 2590.716-8(e)(5), and 45 CFR 149.510(e)(5); see also <a href="https://www.cms.gov/nosurprises/help-resolve-payment-disputes/submit-feedback-on-certified-organizations">https://www.cms.gov/nosurprises/help-resolve-payment-disputes/submit-feedback-on-certified-organizations</a>. ---------------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Footnote citation and URL only

### 47. `45c41d736fdd7d05` — ⬜ pending

- **Document:** 2026-11140 (chars 355268-355471)
- **Provision:** \95\ See <a href="https://www.cms.gov/files/document/nsa-helpdesk.pdf">https://www.cms.gov/files/document/nsa-helpdesk.pdf</a>. ---------------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Footnote containing only a URL reference

### 48. `d70f2ce8e34fdd84` — ⬜ pending

- **Document:** 2026-11140 (chars 611586-611955)
- **Provision:** \174\ The authorities applicable to HHS' debt collection activities generally includes, but are not limited to, 31 U.S.C. 3711, et seq.; 45 CFR 156.1215; 42 CFR part 401, subpart F; 31 CFR part 901; 45 CFR part 30; and applicable common law (collectively, ``Federal Debt Collection Law''). ---------------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Footnote listing authority citations for debt collection

### 49. `a557ad309ec017e4` — ⬜ pending

- **Document:** 2026-11140 (chars 923570-924044)
- **Provision:** \247\ These estimates are calculated as follows: 11.5 hours per respondent for initial registration x $77.78 combined average hourly rate = $894.50 cost per respondent. $894.50 x 1,585 respondents = $1,417,783 total one-time cost. 0.75 hours per respondent for annual updates x $74.67 combined average hourly rate = $56 cost per respondent. $56 x 1,585 respondents = $88,760 total annual cost. ------…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Footnote showing burden cost arithmetic

### 50. `c4182e58d9944782` — ⬜ pending

- **Document:** 2026-11592 (chars 0-359)
- **Provision:** <html> <head> <title>Federal Register, Volume 91 Issue 111 (Wednesday, June 10, 2026)</title> </head> <body><pre> [Federal Register Volume 91, Number 111 (Wednesday, June 10, 2026)] [Rules and Regulations] [Page 35142] From the Federal Register Online via the Government Publishing Office [<a href="http://www.gpo.gov">www.gpo.gov</a>] [FR Doc No: 2026-11592]
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** HTML header and Federal Register citation boilerplate

### 51. `22d6033e8b845228` — ⬜ pending

- **Document:** 2026-11592 (chars 1009-1112)
- **Provision:** DATES: GL 2 was issued on April 23, 2026. See SUPPLEMENTARY INFORMATION for additional relevant dates.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** DATES notice stating issuance date

### 52. `c5b75ede3a8968ed` — ⬜ pending

- **Document:** 2026-11592 (chars 1114-1306)
- **Provision:** FOR FURTHER INFORMATION CONTACT: OFAC: Assistant Director for Regulatory Affairs, 202-622-4855; or <a href="https://ofac.treasury.gov/contact-ofac">https://ofac.treasury.gov/contact-ofac</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Contact information heading

### 53. `4d01508dfee31674` — ⬜ pending

- **Document:** 2026-11592 (chars 1365-1524)
- **Provision:** This document and additional information concerning OFAC are available on OFAC's website: <a href="https://ofac.treasury.gov/">https://ofac.treasury.gov/</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Notice of document availability on OFAC website

### 54. `399bd9a394fb843e` — ⬜ pending

- **Document:** 2026-11592 (chars 1979-2109)
- **Provision:** Authorizing Certain Transactions Involving Anco Water Supply Co. Ltd. Related to the Treatment and Distribution of Drinking Water
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** General license title heading only

### 55. `099cbb75914245cc` — ⬜ pending

- **Document:** 2026-11592 (chars 2115-2836)
- **Provision:** (a) Except as provided in paragraph (b) of this general license, all transactions prohibited by the Cyber-Related Sanctions Regulations, 31 CFR part 578 (CRSR), involving Anco Water Supply Co. Ltd. or any entity in which Anco Water Supply Co. Ltd. owns, directly or indirectly, a 50 percent or greater interest, and that are ordinarily incident and necessary to the treatment or distribution of drink…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** General license authorizes transactions; paragraph (b) limits scope, imposes no duty

### 56. `ff791496c54a047a` — ⬜ pending

- **Document:** 2026-11592 (chars 2930-3057)
- **Provision:** Bradley T. Smith, Director, Office of Foreign Assets Control. [FR Doc. 2026-11592 Filed 6-9-26; 8:45 am] BILLING CODE 4810-AL-P
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Signature and filing block

### 57. `33f493dcc02dcdfe` — ⬜ pending

- **Document:** 2026-11601 (chars 362-505)
- **Provision:** ======================================================================= -----------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Typographic separator rule, no text

### 58. `31f0db32ea2458a2` — ⬜ pending

- **Document:** 2026-11601 (chars 859-1127)
- **Provision:** SUMMARY: The Department of the Treasury's Office of Foreign Assets Control (OFAC) is publishing a general license (GL) issued pursuant to the International Criminal Court-Related Sanctions Regulations: GL 11. This GL was previously made available on OFAC's website.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** SUMMARY describing publication of a general license

### 59. `5c44f2630bd1499a` — ⬜ pending

- **Document:** 2026-11601 (chars 1129-1236)
- **Provision:** DATES: GL 11 was issued on December 18, 2025. See SUPPLEMENTARY INFORMATION for additional relevant dates.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** DATES notice stating issuance date

### 60. `f2927059bb93b85c` — ⬜ pending

- **Document:** 2026-11601 (chars 1489-1646)
- **Provision:** This document and additional information concerning OFAC are available on OFAC's website: <a href="https://ofac.treasury.gov">https://ofac.treasury.gov</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Notice of document availability on OFAC website

## Evening 4 (items 61-80)

### 61. `6633cc3ee6925c25` — ⬜ pending

- **Document:** 2026-11601 (chars 1664-2055)
- **Provision:** On December 18, 2025, OFAC issued GL 11 to authorize certain transactions otherwise prohibited by the International Criminal Court- Related Sanctions Regulations, 31 CFR part 528. This GL expired on January 17, 2026. This GL was made available on OFAC's website (<a href="https://ofac.treasury.gov">https://ofac.treasury.gov</a>) when it was issued. The text of this GL is provided below.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Background narrative describing issuance and expiration of GL 11

### 62. `213978ce3a3238b8` — ⬜ pending

- **Document:** 2026-11601 (chars 2295-3363)
- **Provision:** (a) Except as provided in paragraph (b) of this general license, all transactions prohibited by the International Criminal Court-Related Sanctions Regulations (ICCSR), 31 CFR part 528, that are ordinarily incident and necessary to the wind down of any transaction involving one or more of the following blocked persons are authorized through 12:01 a.m. eastern standard time, January 17, 2026, provid…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Authorization with a passive proviso; no operative duty on a named party

### 63. `abaf23c90af038d8` — ⬜ pending

- **Document:** 2026-11601 (chars 3433-3586)
- **Provision:** Dated: December 18, 2025. Bradley T. Smith, Director, Office of Foreign Assets Control. [FR Doc. 2026-11601 Filed 6-9-26; 8:45 am] BILLING CODE 4810-AL-P
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Dated signature and filing block

### 64. `bece2d35e9a51adb` — ⬜ pending

- **Document:** 2026-11614 (chars 0-366)
- **Provision:** <html> <head> <title>Federal Register, Volume 91 Issue 111 (Wednesday, June 10, 2026)</title> </head> <body><pre> [Federal Register Volume 91, Number 111 (Wednesday, June 10, 2026)] [Rules and Regulations] [Pages 35141-35142] From the Federal Register Online via the Government Publishing Office [<a href="http://www.gpo.gov">www.gpo.gov</a>] [FR Doc No: 2026-11614]
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** HTML header and Federal Register citation boilerplate

### 65. `1f0bc6a976ca51d1` — ⬜ pending

- **Document:** 2026-11614 (chars 1374-1533)
- **Provision:** This document and additional information concerning OFAC are available on OFAC's website: <a href="https://ofac.treasury.gov/">https://ofac.treasury.gov/</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Notice of document availability on OFAC website

### 66. `dc61e08b0164dfd4` — ⬜ pending

- **Document:** 2026-11614 (chars 1551-2862)
- **Provision:** On March 20, 2026, OFAC issued GL U to authorize certain transactions otherwise prohibited by the Iranian Transactions and Sanctions Regulations, 31 CFR part 560; Russian Harmful Foreign Activities Sanctions Regulations, 31 CFR part 587; Ukraine-/Russia- Related Sanctions Regulations, 31 CFR part 589; Weapons of Mass Destruction Proliferators Sanctions Regulations, 31 CFR part 544; Iranian Financi…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Background narrative listing prior general licenses and expirations

### 67. `da3a4e31d324d254` — ⬜ pending

- **Document:** 2026-11614 (chars 3589-3734)
- **Provision:** Executive Order 13949 of September 21, 2020 (``Blocking Property of Certain Persons With Respect to the Conventional Arms Activities of Iran'')
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Executive Order title heading only

### 68. `e1f4fec8dc7ae845` — ⬜ pending

- **Document:** 2026-11614 (chars 5631-6195)
- **Provision:** (b) This general license does not authorize: (1) Any transaction involving a person located in or organized under the laws of the Democratic People's Republic of Korea, the Republic of Cuba, the Covered Regions of Ukraine, as defined by E.O. 14065, the Crimea Region of Ukraine, as defined by E.O. 13685, or any entity that is owned or controlled by or in a joint venture with such persons; or (2) An…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Carve-out limiting the authorization's scope, not an affirmative prohibition

### 69. `5d4137a7b04e3255` — ⬜ pending

- **Document:** 2026-11614 (chars 6454-6555)
- **Provision:** Authorizing the Wind Down of Transactions Involving Hengli Petrochemical (Dalian) Refinery Co., Ltd.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** General license title heading only

### 70. `4b4d39164a30df19` — ⬜ pending

- **Document:** 2026-11614 (chars 7329-7473)
- **Provision:** blocked pursuant to E.O. 13902 other than the blocked persons described in paragraph (a) of this general license, unless separately authorized.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Fragment of a scope limitation on the authorization

### 71. `b2e29ba4fd2f436d` — ⬜ pending

- **Document:** 2026-11615 (chars 0-366)
- **Provision:** <html> <head> <title>Federal Register, Volume 91 Issue 111 (Wednesday, June 10, 2026)</title> </head> <body><pre> [Federal Register Volume 91, Number 111 (Wednesday, June 10, 2026)] [Rules and Regulations] [Pages 35142-35143] From the Federal Register Online via the Government Publishing Office [<a href="http://www.gpo.gov">www.gpo.gov</a>] [FR Doc No: 2026-11615]
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** HTML header and Federal Register citation boilerplate

### 72. `78552d588a66b09e` — ⬜ pending

- **Document:** 2026-11615 (chars 774-1033)
- **Provision:** SUMMARY: The Department of the Treasury's Office of Foreign Assets Control (OFAC) is publishing two general licenses (GLs) issued pursuant to the Venezuela Sanctions Regulations: GLs 5U and 5V, each of which was previously made available on OFAC's website.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** SUMMARY describing publication of two general licenses

### 73. `53079050be48cb83` — ⬜ pending

- **Document:** 2026-11615 (chars 1571-2098)
- **Provision:** On February 2, 2026, OFAC issued GL 5U to authorize certain transactions otherwise prohibited by the Venezuela Sanctions Regulations (VSR), 31 CFR part 591. GL 5U replaced and superseded GL 5T. On March 19, 2026, OFAC issued GL 5V, also to authorize certain transactions otherwise prohibited by the VSR. GL 5V replaced and superseded GL 5U. These GLs were made available on OFAC's website (<a href="h…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Background narrative on issuance and supersession of GLs 5U and 5V

### 74. `70df3c94ee41349a` — ⬜ pending

- **Document:** 2026-11615 (chars 2208-2341)
- **Provision:** Authorizing Certain Transactions Related to the Petr[oacute]leos de Venezuela, S.A. 2020 8.5 Percent Bond on or After March 20, 2026
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** General license title heading only

### 75. `1b2cdaeb28893e15` — ⬜ pending

- **Document:** 2026-11615 (chars 2347-3151)
- **Provision:** (a) Except as provided in paragraph (b) of this general license, on or after March 20, 2026, all transactions related to, the provision of financing for, and other dealings in the Petr[oacute]leos de Venezuela, S.A. 2020 8.5 Percent Bond that would be prohibited by subsection l(a)(iii) of Executive Order (E.O.) 13835 of May 21, 2018, as amended by E.O. 13857 of January 25, 2019, and incorporated i…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Authorization plus scope limit and supersession clause; no duty imposed

### 76. `35490048240c01f5` — ⬜ pending

- **Document:** 2026-11615 (chars 3371-3501)
- **Provision:** Authorizing Certain Transactions Related to the Petr[oacute]leos de Venezuela, S.A. 2020 8.5 Percent Bond on or After May 5, 2026
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** General license title heading only

### 77. `f63ccc31f78de52d` — ⬜ pending

- **Document:** 2026-11615 (chars 3507-4305)
- **Provision:** (a) Except as provided in paragraph (b) of this general license, on or after May 5, 2026, all transactions related to, the provision of financing for, and other dealings in the Petr[oacute]leos de Venezuela, S.A. 2020 8.5 Percent Bond that would be prohibited by subsection l(a)(iii) of Executive Order (E.O.) 13835 of May 21, 2018, as amended by E.O. 13857 of January 25, 2019, and incorporated into…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Authorization plus scope limit and supersession clause; no duty imposed

### 78. `a36dea852d0137ac` — ⬜ pending

- **Document:** 2026-11616 (chars 1032-1137)
- **Provision:** DATES: GL 49A was issued on March 13, 2026. See SUPPLEMENTARY INFORMATION for additional relevant dates.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** DATES notice stating issuance date

### 79. `843ac0f418212c30` — ⬜ pending

- **Document:** 2026-11616 (chars 1567-1979)
- **Provision:** On March 13, 2026, OFAC issued GLs 48A and 49A to authorize certain transactions otherwise prohibited by the Venezuela Sanctions Regulations, 31 CFR part 591. GLs 48A and 49A replaced and superseded GLs 48 and 49, respectively. These GLs were made available on OFAC's website (<a href="https://ofac.treasury.gov">https://ofac.treasury.gov</a>) when they were issued. The text of these GLs is provided…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Background narrative on issuance of GLs 48A and 49A

### 80. `2c58816b462403ff` — ⬜ pending

- **Document:** 2026-11616 (chars 4481-4716)
- **Provision:** Note 3 to Paragraph (a). For purposes of this general license, the term ``petrochemical products'' includes fertilizer products and fertilizer precursor chemicals, including the chemicals listed in the Annex of this general license.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Definitional note explaining the term petrochemical products

## Evening 5 (items 81-100)

### 81. `44e23c611d8f0083` — ⬜ pending

- **Document:** 2026-11616 (chars 13244-13479)
- **Provision:** Note 3 to Paragraph (a). For purposes of this general license, the term ``petrochemical products'' includes fertilizer products and fertilizer precursor chemicals, including the chemicals listed in the Annex of this general license.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Definitional note explaining the term petrochemical products

### 82. `0f9f603f0a7fd303` — ⬜ pending

- **Document:** 2026-11616 (chars 14114-14338)
- **Provision:** Note to General License No. 49A. Nothing in this general license relieves any person from compliance with the requirements of other Federal agencies, including the Department of Commerce's Bureau of Industry and Security.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Savings clause pointing to other agencies' requirements located elsewhere

### 83. `7397f6d9b177dd0c` — ⬜ pending

- **Document:** 2026-11616 (chars 18276-18403)
- **Provision:** Bradley T. Smith, Director, Office of Foreign Assets Control. [FR Doc. 2026-11616 Filed 6-9-26; 8:45 am] BILLING CODE 4810-AL-P
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Signature and filing block

### 84. `8cd9a30f2a9c7d5f` — ⬜ pending

- **Document:** 2026-11616 (chars 18406-18535)
- **Provision:** </pre><script data-cfasync="false" src="/cdn-cgi/scripts/5c5dd728/cloudflare-static/email-decode.min.js"></script></body> </html>
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Closing HTML markup and script tag

### 85. `de2488899132b787` — ⬜ pending

- **Document:** 2026-11761 (chars 0-357)
- **Provision:** <html> <head> <title>Federal Register, Volume 91 Issue 112 (Thursday, June 11, 2026)</title> </head> <body><pre> [Federal Register Volume 91, Number 112 (Thursday, June 11, 2026)] [Rules and Regulations] [Page 35400] From the Federal Register Online via the Government Publishing Office [<a href="http://www.gpo.gov">www.gpo.gov</a>] [FR Doc No: 2026-11761]
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** HTML/Federal Register masthead boilerplate; no operative language

### 86. `48e955e423dca67d` — ⬜ pending

- **Document:** 2026-11761 (chars 585-703)
- **Provision:** Publication of the List of Medical Devices Requiring Specific Authorization for the North Korea Sanctions Regulations
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Document title only; imposes no duty

### 87. `bf414f3ecbeea71e` — ⬜ pending

- **Document:** 2026-11761 (chars 930-1432)
- **Provision:** SUMMARY: The Department of the Treasury's Office of Foreign Assets Control (OFAC) is publishing a list of medical devices that may not be exported or reexported to North Korea pursuant to the general license authorizing the exportation or reexportation to North Korea of certain agricultural commodities, medicine, medical devices, and replacement parts and components. The exportation or re-exportat…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** SUMMARY preamble describing restrictions codified at 31 CFR 510.521; description, not operative text

### 88. `79b790143c842a89` — ⬜ pending

- **Document:** 2026-11761 (chars 1720-1877)
- **Provision:** This document and additional information concerning OFAC is available on OFAC's website (<a href="https://ofac.treasury.gov">https://ofac.treasury.gov</a>).
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Informational availability notice; no duty imposed

### 89. `657af8c9b1139b29` — ⬜ pending

- **Document:** 2026-11761 (chars 2999-3128)
- **Provision:** The list below comprises the List of Medical Devices Requiring Specific Authorization as identified in 31 CFR 510.521(b)(3)(ii).
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Descriptive framing of the list that follows; no operative language

### 90. `6886ac33f7e79fd0` — ⬜ pending

- **Document:** 2026-11761 (chars 3170-3405)
- **Provision:** <bullet> Oxygen Generators <bullet> Pumps with flow rates of more than 1 liter/minute <bullet> Diagnostic Medical Imaging Equipment: [cir] Gamma imaging equipment [cir] Tactile Imaging equipment [cir] Thermography equipment
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Bare enumeration of device categories; no operative language

### 91. `2678aef4d8bbada3` — ⬜ pending

- **Document:** 2026-11761 (chars 5452-5580)
- **Provision:** Bradley T. Smith, Director, Office of Foreign Assets Control. [FR Doc. 2026-11761 Filed 6-10-26; 8:45 am] BILLING CODE 4810-AL-P
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Signature and filing block

### 92. `25b2ab04c38cfdcd` — ⬜ pending

- **Document:** 2026-12787 (chars 26341-27316)
- **Provision:** Accordingly, in connection with an Agency-specific rulemaking, an Agency could determine to use an identifier that is not in the joint standards, including an Agency-specific identifier, rather than, or in addition to or in combination with, an identifier established by the final joint rule. This could occur if, for example, the Agency exercised its authority to tailor the joint standards in its A…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Preamble discussion of agency discretion ('could', 'may'); no bound duty

### 93. `a429b5a4b1d7eef6` — ⬜ pending

- **Document:** 2026-12787 (chars 39114-39309)
- **Provision:** <bullet> The alphabetic currency code as defined by ISO 4217 Currency Codes \35\ for the identification of currencies. ---------------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Definitional bullet identifying a currency-code standard

### 94. `21791cc06c7e65d8` — ⬜ pending

- **Document:** 2026-12787 (chars 39315-39521)
- **Provision:** \35\ Available at <a href="https://www.iso.org/iso-4217-currency-codes.html">https://www.iso.org/iso-4217-currency-codes.html</a>. ---------------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Footnote citation with URL

### 95. `9268dab9a786ecd0` — ⬜ pending

- **Document:** 2026-12787 (chars 75216-76264)
- **Provision:** Several commenters recommended other legal entity identifiers or identifier standards. These include ISO 8000-116, the ISO standard for formatting Authoritative Legal Entity Identifiers (ALEI) as International Business Registration Numbers (IBRN). ALEI refers to an entity identifier used in an authoritative source, such as a jurisdiction business registry, where an entity is already registered. So…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Summary of commenter recommendations; no operative language

### 96. `47b571ef65f6ada6` — ⬜ pending

- **Document:** 2026-12787 (chars 85325-85568)
- **Provision:** CUSIP numbers). The Agencies stated that, while these identifiers are widely used, they are proprietary and not available under an open license in the United States. ---------------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Preamble recital of agency statements about proprietary identifiers

### 97. `c253da5278dddba0` — ⬜ pending

- **Document:** 2026-12787 (chars 146131-146760)
- **Provision:** OCC The Paperwork Reduction Act of 1995 \89\ (PRA) states that no agency may conduct or sponsor, nor is the respondent required to respond to, an information collection unless it displays a currently valid Office of Management and Budget (OMB) control number. The OCC has reviewed this final joint rule and determined that it does not create any information collection or revise any existing collecti…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Preamble recital of the PRA plus a no-collection determination; describes duty located elsewhere

### 98. `e36f527c54db4755` — ⬜ pending

- **Document:** 2026-12787 (chars 187649-187819)
- **Provision:** For the reasons set forth in the common preamble, the National Credit Union Administration amends chapter VII of title 12 of the Code of Federal Regulations as follows:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instruction to the CFR; quotes no operative regulatory duty

### 99. `e975717ff459a738` — ⬜ pending

- **Document:** 2026-13830 (chars 365-508)
- **Provision:** ======================================================================= -----------------------------------------------------------------------
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Typographic separator rule; no text

### 100. `6406054ce839e965` — ⬜ pending

- **Document:** 2026-13830 (chars 922-1556)
- **Provision:** SUMMARY: This document contains final regulations providing guidance on the application of the transfer for valuable consideration rules and associated information reporting requirements for reportable policy sales of interests in life insurance contracts to exchanges of life insurance contracts qualifying for nonrecognition of gain or loss and certain acquisitions of interests in life insurance c…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** SUMMARY describing scope and affected parties of final regulations

## Evening 6 (items 101-120)

### 101. `01ac94b090ad08e4` — ⬜ pending

- **Document:** 2026-13830 (chars 41916-42499)
- **Provision:** Executive Order 13132 (Federalism) prohibits an agency from publishing any rule that has federalism implications if the rule either imposes substantial, direct compliance costs on State and local governments, and is not required by statute, or preempts State law, unless the agency meets the consultation and funding requirements of section 6 of the Executive order. These final regulations do not ha…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Recites Executive Order 13132 and certifies no federalism implications; describes duty located elsewhere

### 102. `4353a128e8a3dbcf` — ⬜ pending

- **Document:** 2026-13830 (chars 42759-43002)
- **Provision:** The principal author of these regulations is Allan H. Sakaue, Office of Associate Chief Counsel (Financial Institutions and Products), IRS. However, other personnel from the Treasury Department and the IRS participated in their development.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Drafting-information credit paragraph

### 103. `8a93adfebf259541` — ⬜ pending

- **Document:** 2026-13830 (chars 44521-44632)
- **Provision:** Sec. 1.101-1 Exclusion from gross income of proceeds of life insurance contracts payable by reason of death.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Section heading only

### 104. `48044029bcbce5f0` — ⬜ pending

- **Document:** 2026-13830 (chars 57318-57687)
- **Provision:** 0 Par. 6. Section 1.6050Y-3 is amended by: 0 1. In paragraph (f) introductory text, removing the language ``paragraph (f)(1), (2), or (3) of this section applies'' at the end of the paragraph and adding in its place ``paragraph (f)(1) or (2) of this section applies''; 0 2. Removing paragraph (f)(3); and 0 3. Adding paragraph (h). The addition reads as follows:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instructions removing and adding paragraph language; no operative duty quoted

### 105. `e32927aadbf06db0` — ⬜ pending

- **Document:** 2026-13830 (chars 60131-60242)
- **Provision:** 0 Par. 7. Section 1.6050Y-4 is amended by adding a sentence at the end of paragraph (e)(3) to read as follows:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instruction adding a sentence; no operative duty quoted

### 106. `133bd4ca1062e223` — ⬜ pending

- **Document:** 2026-13851 (chars 730-1513)
- **Provision:** SUMMARY: This document contains final regulations that identify certain charitable remainder annuity trust (CRAT) transactions and substantially similar transactions as listed transactions, a type of reportable transaction. Material advisors and certain participants in these listed transactions are required to file disclosures with the IRS and will be subject to penalties for failure to disclose. …
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** SUMMARY describing disclosure duties imposed by regulations elsewhere

### 107. `b924119044092f59` — ⬜ pending

- **Document:** 2026-13851 (chars 1665-1864)
- **Provision:** FOR FURTHER INFORMATION CONTACT: Concerning the final regulations, Charles D. Wien of the Office of Associate Chief Counsel (Passthroughs, Trusts & Estates) (202) 317-5279 (not a toll-free number).
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Contact information block

### 108. `854d970421c70ec4` — ⬜ pending

- **Document:** 2026-13851 (chars 4170-4550)
- **Provision:** On March 25, 2024, the Department of Treasury (Treasury Department) and the IRS published a notice of proposed rulemaking (REG-108761-22) in the Federal Register (89 FR 20569) proposing regulations at new Sec. 1.6011-15 (proposed Sec. 1.6011-15) that would identify certain CRAT transactions and substantially similar transactions as ``listed transactions'' for purposes of
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Rulemaking history recital of the proposed regulations

### 109. `9cfac90438398e39` — ⬜ pending

- **Document:** 2026-13851 (chars 4568-5027)
- **Provision:** Sec. 1.6011-4 and sections 6111 and 6112 of the Code (proposed regulations). The Treasury Department and the IRS received one comment in response to the proposed regulations that are the subject of this final rulemaking. The comment is available for public inspection at <a href="https://www.regulations.gov">https://www.regulations.gov</a> or upon request. No public hearing was held on the proposed…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Procedural recital of comments received and no public hearing

### 110. `59fca6facdbf83ff` — ⬜ pending

- **Document:** 2026-13851 (chars 15676-15935)
- **Provision:** The principal author of these final regulations is Charles D. Wien, Office of Associate Chief Counsel (Passthroughs, Trusts, & Estates). However, other personnel from the IRS and the Treasury Department participated in the development of these regulations.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Drafting-information credit paragraph

### 111. `c5368300930dd05d` — ⬜ pending

- **Document:** 2026-13851 (chars 16342-16529)
- **Provision:** Authority: 26 U.S.C. 7805 * * * * * * * * Section 1.6011-15 also issued under 26 U.S.C. 6001 and 26 U.S.C. 6011. * * * * * Par. 2. Section 1.6011-15 is added to read as follows:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Authority citation plus amendatory instruction; no operative duty

### 112. `406447cce514e1dc` — ⬜ pending

- **Document:** 2026-13851 (chars 19363-19509)
- **Provision:** transaction described in paragraph (b) of this section as listed transactions for purposes of Sec. 1.6011-4(b)(2) is effective on July 9, 2026.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Effective-date clause fragment; states timing, imposes no duty

### 113. `97b3743723d7c696` — ⬜ pending

- **Document:** 2026-13925 (chars 870-1625)
- **Provision:** SUMMARY: This document contains final regulations that amend the Federal estate tax regulations applicable to estates of decedents passing property to or for the benefit of a noncitizen spouse in a domestic trust that satisfies all of the requirements under applicable Federal tax law and regulations to be a qualified domestic trust and for which the executor of the decedent's estate has made a qua…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** SUMMARY describing scope and affected estates; no operative language

### 114. `5dba962569160b17` — ⬜ pending

- **Document:** 2026-13925 (chars 16701-17495)
- **Provision:** Pursuant to the Regulatory Flexibility Act (5 U.S.C. chapter 6), it is hereby certified that the final regulations will not have a significant economic impact on a substantial number of small entities. This rule primarily affects individuals (or their estates) and trusts, which are not small entities for purposes of the Regulatory Flexibility Act. Although it is anticipated that there may be an in…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Regulatory Flexibility Act certification; no duty imposed

### 115. `e2ff915f58ddec1e` — ⬜ pending

- **Document:** 2026-13925 (chars 17522-17729)
- **Provision:** Pursuant to section 7805(f) of the Code, this regulation has been submitted to the Chief Counsel for the Office of Advocacy of the Small Business Administration for comment on its impact on small business.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Statement that submission to SBA Advocacy already occurred; no prospective duty

### 116. `bd7cd2953800bf82` — ⬜ pending

- **Document:** 2026-13925 (chars 20089-20555)
- **Provision:** Sec. 20.2056A-2 Requirements for qualified domestic trust. * * * * * (d) * * * (6) Special rules. (e) Applicability date. * * * * * Sec. 20.2056A-4 Procedures for conforming marital trusts and nontrust marital transfers to the requirements of a qualified domestic trust. * * * * * (e) Applicability date. * * * * * Sec. 20.2056A-11 Filing requirements and payment of the section 2056A estate tax. * *…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Table-of-contents style section headings

### 117. `f6dc73de53795583` — ⬜ pending

- **Document:** 2026-13925 (chars 28736-29959)
- **Provision:** when submitting the required documentation, see IRS Publication 4235, Collection Advisory Offices Contact Information, or as otherwise provided in IRS forms or instructions or on <a href="https://www.irs.gov">https://www.irs.gov</a>. (C) * * * (1) * * * Any notice of failure to renew or closure of a U.S. branch of a foreign bank required to be sent to the Internal Revenue Service must be sent to t…
- **Proposed:** is_obligation=True, type=reporting, party=U.S. branch of a foreign bank
- **Rationale (claude-fable-5):** Operative regulatory text: required notice 'must be sent' to the Estate Tax Advisory Group

### 118. `d10c060ef3f7ed15` — ⬜ pending

- **Document:** 2026-13925 (chars 36194-36327)
- **Provision:** To: Estate Tax Group, Assistant Commissioner (International) 950 L'Enfant Plaza CP:IN:D:C:EX:HQ:1114 Washington, DC 20024] Dear Sirs:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Address and salutation block of a model letter form

### 119. `d3fd0b2f6031f746` — ⬜ pending

- **Document:** 2026-13925 (chars 51109-51419)
- **Provision:** (a) * * * See also Sec. 20.2056A-5(c)(1) regarding the requirements for filing a Form 706-QDT in the case of a distribution to the surviving spouse on account of hardship, and Sec. 20.2056A-2(d)(3) regarding the requirements for filing Form 706-QDT in the case of the required annual statement. * * * * *
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Cross-reference pointing to filing requirements stated in other sections

### 120. `7755eb9474354bdd` — ⬜ pending

- **Document:** 2026-15008 (chars 0-353)
- **Provision:** <html> <head> <title>Federal Register, Volume 91 Issue 141 (Friday, July 24, 2026)</title> </head> <body><pre> [Federal Register Volume 91, Number 141 (Friday, July 24, 2026)] [Rules and Regulations] [Page 46724] From the Federal Register Online via the Government Publishing Office [<a href="http://www.gpo.gov">www.gpo.gov</a>] [FR Doc No: 2026-15008]
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** HTML/Federal Register masthead boilerplate

## Evening 7 (items 121-140)

### 121. `bce8ed0640416b07` — ⬜ pending

- **Document:** 2026-15008 (chars 598-721)
- **Provision:** Revising Qualified Domestic Trust Regulations Under Section 2056A To Update Outdated References and Procedures; Correction
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Document title only

### 122. `ed2525f4bcb8df23` — ⬜ pending

- **Document:** 2026-15008 (chars 891-1461)
- **Provision:** SUMMARY: This document contains corrections to Treasury Decision 10050 published in the Federal Register on Friday, July 10, 2026. Treasury Decision 10050 contains final regulations that amend the Federal estate tax regulations applicable to estates of decedents passing property to or for the benefit of a noncitizen spouse in a domestic trust that satisfies all of the requirements under applicable…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** SUMMARY describing corrections to a prior Treasury Decision

### 123. `d2b1a4019235a1b4` — ⬜ pending

- **Document:** 2026-15008 (chars 1463-1672)
- **Provision:** DATES: Effective date: These corrections are effective on July 24, 2026. Applicability dates: For dates of applicability, see Sec. Sec. 20.2056A-2(e), 20.2056A-4(e), 20.2056A-11(e), and 20.2056A-13.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** DATES section stating effective and applicability dates

### 124. `18130ad7017f1030` — ⬜ pending

- **Document:** 2026-15008 (chars 1809-1963)
- **Provision:** The final regulations (TD 10050) subject to these corrections are issued under sections 2056A(a)(2), 2056A(e), and 7805(a) of the Internal Revenue Code.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Statutory authority citation for the corrected regulations

### 125. `dc16ecf81c7adc1b` — ⬜ pending

- **Document:** 2026-15008 (chars 2412-3027)
- **Provision:** 0 Par. 2. Section 20.2056A-2 is amended: 0 a. In paragraph (d)(1)(i)(B)(2), in the form, by removing the language ``as defined in section 2056A'' and adding the language ``as defined in section 2056A(a)'' in its place. 0 b. In paragraph (d)(1)(i)(C)(2), in the form: 0 i. By removing the zip code ``20224'' and adding the zip code ``20024'' in its place. 0 ii. By removing the word ``Applicants'' and…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instructions correcting form language and zip code

### 126. `af642220fdeccdb2` — ⬜ pending

- **Document:** 2026-15008 (chars 3029-3229)
- **Provision:** Oluwafunmilayo Taylor, Section Chief, Publications and Regulations Section, Associate Chief Counsel, (Procedure and Administration). [FR Doc. 2026-15008 Filed 7-23-26; 8:45 am] BILLING CODE 4831-GV-P
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Signature and filing block

### 127. `207c28b1a071bb41` — ⬜ pending

- **Document:** 2026-15112 (chars 2923-3774)
- **Provision:** Because the Regulations involve a foreign affairs function, the provisions of E.O. 12866 of September 30, 1993, ``Regulatory Planning and Review'' (58 FR 51735, October 4, 1993), as amended, and the Administrative Procedure Act (5 U.S.C. 553) requiring notice of proposed rulemaking, opportunity for public participation, and delay in effective date, as well as the provisions of E.O. 14192 of Januar…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Rulemaking-procedure inapplicability statement; no operative duty

### 128. `203f4c37a5a0d7c9` — ⬜ pending

- **Document:** 2026-15112 (chars 10882-11058)
- **Provision:** 0 14. In Sec. 536.308, in paragraphs (b) and (c), remove ``www.treasury.gov/ofac'' and add in its place ``<a href="https://ofac.treasury.gov">https://ofac.treasury.gov</a>''.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instruction to remove/add a URL; no quoted operative text

### 129. `b2dc825fee21632f` — ⬜ pending

- **Document:** 2026-15112 (chars 12786-12895)
- **Provision:** 0 19. In Sec. 546.201, in note 3 to the section, revise and republish the last sentence to read as follows:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instruction to revise a note; operative text not included

### 130. `15a2e6d5d1074f92` — ⬜ pending

- **Document:** 2026-15112 (chars 21433-21555)
- **Provision:** 0 41. In Sec. 553.303, in paragraph (a)(1), remove ``Sec. 533.201(a)(1)'' and add in its place ``Sec. 553.201(a)(1)''.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instruction correcting a cross-reference; no duty imposed

### 131. `ace83a437c524bd3` — ⬜ pending

- **Document:** 2026-15112 (chars 39697-39887)
- **Provision:** Note 3 to Sec. 587.201: * * * Inquiries regarding any such order should be directed to OFAC at <a href="https://ofac.treasury.gov/contact-ofac">https://ofac.treasury.gov/contact-ofac</a>.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Note directing inquiries with hortatory 'should'; not mandatory language

### 132. `2bf0d7a5e29b0618` — ⬜ pending

- **Document:** 2026-15112 (chars 40676-40785)
- **Provision:** 0 89. In Sec. 588.201, in note 3 to the section, revise and republish the last sentence to read as follows:
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Amendatory instruction to revise a note; operative text not included

### 133. `b0c7d6f304ac75a5` — ⬜ pending

- **Document:** 2026-15112 (chars 49752-50482)
- **Provision:** Authority: 3 U.S.C. 301; 8 U.S.C. 1182, 1189; 18 U.S.C. 2339B; 21 U.S.C. 1901-1908; 22 U.S.C. 287c; 31 U.S.C. 321(b); 22 U.S.C. 9201-9255; 22 U.S.C. 10101-10103; 50 U.S.C. App. 1-44; Public Law 110-286, 122 Stat. 2632 (50 U.S.C. 1701 note); Public Law 111-195, 124 Stat. 1312 (22 U.S.C. 8501-8551); Public Law 112-81, 125 Stat. 1298 (22 U.S.C. 8513a); Public Law 112-158, 126 Stat. 1214 (22 U.S.C. 87…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Authority citation list only

### 134. `47e41770c0433165` — ⬜ pending

- **Document:** 31-CFR-223 (chars 0-109)
- **Provision:** PART 223—SURETY COMPANIES DOING BUSINESS WITH THE UNITED STATES Authority: 5 U.S.C. 301; 31 U.S.C. 9304-9308.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Part heading plus authority citation

### 135. `f2e53c43c46705c0` — ⬜ pending

- **Document:** 31-CFR-223 (chars 10244-10952)
- **Provision:** § 223.9, the history of the company, and any further evidence or information that Treasury may, in its discretion, require the company to submit. (b) A certificate of authority will be effective for a term that expires on the last day of the next July. All statutory requirements and regulatory requirements under this part are continuing obligations, and any certificate issued is expressly subject …
- **Proposed:** is_obligation=True, type=requirement, party=the company
- **Rationale (claude-fable-5):** Certificate expressly subject to continuing compliance; company submits required fee

### 136. `0f41fd729911baa8` — ⬜ pending

- **Document:** 31-CFR-223 (chars 31133-32284)
- **Provision:** § 223.12 any single risk in excess of 10 percent of the latter company's paid-up capital and surplus. (c) Other methods. With respect to all risks other than bonds required to be furnished to the United States by the Miller Act (40 U.S.C. 3131, as amended), which must be either coinsured or reinsured in accordance with paragraph (a) or (b)(1)(ii) of this section respectively, the excess liability …
- **Proposed:** is_obligation=True, type=requirement, party=the company
- **Rationale (claude-fable-5):** Miller Act bonds 'must be either coinsured or reinsured'; pledged assets 'cannot also be used'

### 137. `9240442e10fb4cbb` — ⬜ pending

- **Document:** 31-CFR-223 (chars 44056-44893)
- **Provision:** § 223.22. (j) Alien reinsurers. Any company may apply for recognition or annual renewal of such recognition as an alien reinsurer, provided it is licensed to write reinsurance by, and has its head office or domicile in, a non-U.S. jurisdiction that is recognized by a U.S. state as a Qualified Jurisdiction or as a Reciprocal Jurisdiction, provided that the Reciprocal Jurisdiction is not party to an…
- **Proposed:** is_obligation=True, type=requirement, party=the company
- **Rationale (claude-fable-5):** Conditional duty: 'the company must submit to Treasury the fee'

### 138. `9a313a8c0e01ba10` — ⬜ pending

- **Document:** 31-CFR-223 (chars 46003-46284)
- **Provision:** § 223.15 Paid-up capital and surplus for Treasury rating purposes; how determined. Treasury determines the amount of paid-up capital and surplus of any company holding or seeking a certificate of authority or recognized (or seeking recognition) as an admitted reinsurer pursuant to
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Describes how Treasury determines capital/surplus; no must/shall duty

### 139. `ca6cee1c1ad90473` — ⬜ pending

- **Document:** 31-CFR-223 (chars 51396-51678)
- **Provision:** § 223.20, may initiate revocation proceedings against the company upon receipt of a complaint from an agency that the company has not paid or satisfied one or more administratively final bond obligations due the agency. (b) A revocation of a company's certificate of authority under
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Discretionary 'may initiate revocation proceedings'; no bound duty

### 140. `a08d643ce3d3147c` — ⬜ pending

- **Document:** 31-CFR-223 (chars 51693-51989)
- **Provision:** § 223.20 precludes the company from underwriting or reinsuring additional bonds for any agency, and therefore revokes the company's opportunity to have its bonds presented to any agency bond-approving official for acceptance. [79 FR 62001, Oct. 16, 2014, as amended at 89 FR 48837, June 10, 2024]
- **Proposed:** is_obligation=True, type=prohibition, party=the company
- **Rationale (claude-fable-5):** Revocation 'precludes the company from underwriting or reinsuring additional bonds'

## Evening 8 (items 141-160)

### 141. `ecb5fe8465702e73` — ⬜ pending

- **Document:** 31-CFR-285 (chars 0-352)
- **Provision:** PART 285—DEBT COLLECTION AUTHORITIES UNDER THE DEBT COLLECTION IMPROVEMENT ACT OF 1996 Authority: 5 U.S.C. 5514; 26 U.S.C. 6402; 31 U.S.C. 321, 3701, 3711, 3716, 3719, 3720A, 3720B, 3720D; 42 U.S.C. 664; E.O. 13019, 61 FR 51763, 3 CFR, 1996 Comp., p. 216. Source: 62 FR 34179, June 25, 1997, unless otherwise noted. Subpart A—Disbursing Official Offset
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Part heading, authority citation, and source note

### 142. `085e5249f74300e3` — ⬜ pending

- **Document:** 31-CFR-285 (chars 58403-59522)
- **Provision:** § 285.5 Centralized offset of Federal payments to collect nontax debts owed to the United States. (a) Scope. (1) This section governs the centralized offset of Federal payments to collect delinquent, nontax debts owed to Federal agencies in accordance with 31 U.S.C. 3716, 3720A and 26 U.S.C. 6402 and applicable regulations. The Department of the Treasury's Bureau of the Fiscal Service (Fiscal Serv…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Scope paragraph describing what the section governs

### 143. `984c792527a01c19` — ⬜ pending

- **Document:** 31-CFR-285 (chars 93631-94806)
- **Provision:** § 285.6 Administrative offset under reciprocal agreements with states. (a) Scope. (1) This section sets forth the rules that apply to the administrative offset of Federal nontax payments to collect delinquent debts owed to States. As set forth in 31 U.S.C. 3716(h), States may participate in administrative offset so long as they meet certain requirements, including entering into reciprocal agreemen…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Scope and applicability; voluntary participation, no bound duty

### 144. `622a29d8f7509145` — ⬜ pending

- **Document:** 31-CFR-285 (chars 100520-101113)
- **Provision:** § 285.5, States shall only be required to certify that they have complied with the requirements of 31 U.S.C. 3716 (not 31 U.S.C. 3720A or 26 U.S.C. 6402) and this section 285.6. States shall also certify that they have complied with any requirements imposed by State law or procedure that may be applicable to administrative offset. (f) State debts submitted to Fiscal Service for tax refund offset. …
- **Proposed:** is_obligation=True, type=reporting, party=States
- **Rationale (claude-fable-5):** 'States shall also certify that they have complied' with State-law requirements

### 145. `f0aae6daad7f086f` — ⬜ pending

- **Document:** 31-CFR-356 (chars 1080-1218)
- **Provision:** § 356.31.). In addition, these provisions and the auction announcements govern any other types of securities we may issue under this part.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Scope statement about which securities the provisions govern

### 146. `f4dd4efc742a32be` — ⬜ pending

- **Document:** 31-CFR-356 (chars 20723-21343)
- **Provision:** § 356.10 What is the purpose of an auction announcement? By issuing an auction announcement, we provide public notice of the sale of bills, notes, and bonds. The auction announcement lists the specifics of each auction, e.g., offering amount, term and type of security, CUSIP number, and issue and maturity dates. The auction announcement and this part, including the Appendices, specify the terms an…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Explains purpose of auction announcement; only hortatory 'you should read'

### 147. `7deaf40c58a791e7` — ⬜ pending

- **Document:** 31-CFR-356 (chars 21345-21545)
- **Provision:** § 356.11 How are bids submitted in an auction? (a) General. (1) All bids must be submitted using an approved method, which depends on the system into which the awarded securities will be issued. ( See
- **Proposed:** is_obligation=True, type=requirement, party=bidders (implied; passive 'All bids must be submitted')
- **Rationale (claude-fable-5):** 'All bids must be submitted using an approved method'

### 148. `09258e07663ab89e` — ⬜ pending

- **Document:** 31-CFR-356 (chars 26767-27184)
- **Provision:** § 356.22 for award limitations.) (3) Additional restrictions. You may not bid competitively in an auction in which you are bidding noncompetitively. You may not bid competitively for securities to be held directly with Treasury. [69 FR 45202, July 28, 2004, as amended at 69 FR 53621, Sept. 2, 2004; 70 FR 57440, Sept. 30, 2005; 74 FR 26086, June 1, 2009; 78 FR 46428, 46429, July 31, 2013; 87 FR 404…
- **Proposed:** is_obligation=True, type=prohibition, party=you (the bidder)
- **Rationale (claude-fable-5):** 'You may not bid competitively' in two stated circumstances

### 149. `40d4fd608cf00e93` — ⬜ pending

- **Document:** 31-CFR-356 (chars 35931-36152)
- **Provision:** § 356.22(b). (c) Reporting net long positions. If it is bidding competitively, an investment adviser must calculate the amount of its bids and positions for purposes of the net long position reporting requirement found in
- **Proposed:** is_obligation=True, type=reporting, party=an investment adviser
- **Rationale (claude-fable-5):** 'an investment adviser must calculate' bids/positions for net long position reporting

### 150. `adcd0ec0a9571b1b` — ⬜ pending

- **Document:** 31-CFR-356 (chars 52598-53168)
- **Provision:** § 356.13. If a position had to be reported, the statement must provide the amount of the position and the name of the submitter that the customer requested to report the position. (2) Submitter or intermediary requirements. A submitter or intermediary submitting or forwarding bids for a customer must notify the customer of the customer confirmation reporting requirement if we award the customer $2…
- **Proposed:** is_obligation=True, type=reporting, party=a submitter or intermediary
- **Rationale (claude-fable-5):** Statement 'must provide' position amount; submitter 'must notify the customer'

### 151. `439dfe1f0c052e7b` — ⬜ pending

- **Document:** 31-CFR-356 (chars 53170-53371)
- **Provision:** § 356.25 How does the settlement process work? Securities bought in the auction must be paid for by the issue date. The payment amount for awarded securities will be the settlement amount as defined in
- **Proposed:** is_obligation=True, type=requirement, party=purchasers (implied; passive 'Securities bought in the auction must be paid for')
- **Rationale (claude-fable-5):** 'must be paid for by the issue date'

### 152. `1a14e5f045f57bac` — ⬜ pending

- **Document:** 31-CFR-50 (chars 39009-39955)
- **Provision:** § 50.15 Cap disclosure. (a) General. Under section 103(e)(2) of the Act, if the aggregate insured losses exceed $100,000,000,000 during any calendar year, the Secretary shall not make any payment for any portion of the amount of such losses that exceeds $100,000,000,000, and no insurer that has met its insurer deductible shall be liable for the payment of any portion of the amount of such losses t…
- **Proposed:** is_obligation=True, type=disclosure, party=an insurer
- **Rationale (claude-fable-5):** 'an insurer must provide clear and conspicuous disclosure to the policyholder'

### 153. `c2ac126316f25958` — ⬜ pending

- **Document:** 31-CFR-50 (chars 47794-48113)
- **Provision:** § 50.20 and the state permits certain exclusions or allows for other limitations, or an insurance policy is not governed by state law requirements, then the insurer may subsequently offer limited coverage or coverage with exclusions. Subpart D—State Residual Market Insurance Entities; State Workers' Compensation Funds
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Permissive 'the insurer may subsequently offer limited coverage'

### 154. `7031092165ac4743` — ⬜ pending

- **Document:** 31-CFR-50 (chars 68830-70202)
- **Provision:** § 50.71 and to the cap of $100 billion as provided in section 103(e)(2) of the Act. (b) Program Trigger amounts. Notwithstanding paragraph (a) of this section or anything in this subpart to the contrary, Federal compensation will not be paid by Treasury unless the aggregate industry insured losses resulting from one or more certified acts of terrorism exceed the following amounts: (1) For insured …
- **Proposed:** is_obligation=True, type=requirement, party=Treasury
- **Rationale (claude-fable-5):** 'Treasury shall pay the appropriate amount of the Federal share' on determination

### 155. `c80b1a151694848d` — ⬜ pending

- **Document:** 31-CFR-50 (chars 76514-76634)
- **Provision:** § 50.73 and for receiving, disbursing, and distributing payments of the Federal share of compensation in accordance with
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Sentence fragment cross-referencing another section; no operative verb

### 156. `81f6c5a67e8ed420` — ⬜ pending

- **Document:** 31-CFR-50 (chars 78518-79212)
- **Provision:** § 50.73(b)(1) either: Have been paid by the insurer; or will be paid by the insurer upon receipt of an advance payment of the Federal share of compensation as soon as possible, consistent with the insurer's normal business practices, but not longer than five business days after receipt of the Federal share of compensation; (ii) The underlying claims for insured losses were filed by persons who suf…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Fragment listing certification content items; no operative must/shall in text

### 157. `d6b84d4c3ef6e780` — ⬜ pending

- **Document:** 31-CFR-50 (chars 79277-79945)
- **Provision:** § 50.15, for each underlying insured loss that is included in the amount of the insurer's aggregate insured losses; and (v) The insurer has complied with the mandatory availability requirements of subpart C of this part. (3) A certification of the amount of the insurer's direct earned premium, together with the calculation of its insurer deductible (provided this certification was not submitted pr…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Enumerated certification items only; imposing language sits outside this fragment

### 158. `f99630706cad2a95` — ⬜ pending

- **Document:** 31-CFR-50 (chars 107669-108388)
- **Provision:** § 50.95(e), then the insurer is not required to refund any Surcharge that is attributable to the refunded premium. (f) Notwithstanding paragraphs (a), (b), and (c) of this section, if the expense of collecting the Federal terrorism policy surcharge from all policyholders of an insurer during an assessment period exceeds the amount of the Surcharges anticipated to be collected, such insurer may sat…
- **Proposed:** is_obligation=True, type=prohibition, party=insurers (implied; passive 'No fee or commission shall be charged')
- **Rationale (claude-fable-5):** 'No fee or commission shall be charged on the Federal terrorism policy surcharge'

### 159. `b94f1f43d3aa0162` — ⬜ pending

- **Document:** 31-CFR-501 (chars 55072-55214)
- **Provision:** § 501.708 Director's finding of no penalty warranted. If after considering any written response to the Prepenalty Notice submitted pursuant to
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Heading plus truncated conditional clause; no duty stated

### 160. `8399998bb96e77b5` — ⬜ pending

- **Document:** 31-CFR-501 (chars 63838-64192)
- **Provision:** § 501.713 Order Instituting Proceedings. If a respondent makes a timely request for a hearing, the Director shall determine, at his or her option, whether to dismiss the violation(s) set forth in the Penalty Notice or to issue an Order Instituting Proceedings to initiate the hearing process. The Order shall be served on the respondent(s) as provided in
- **Proposed:** is_obligation=True, type=requirement, party=the Director
- **Rationale (claude-fable-5):** 'the Director shall determine' whether to dismiss or issue Order; 'Order shall be served'

## Evening 9 (items 161-168)

### 161. `bc793aff6f77c9a7` — ⬜ pending

- **Document:** 31-CFR-501 (chars 98322-98843)
- **Provision:** § 501.705. (d) Application to quash or modify —(1) Procedure. Any person to whom a subpoena is directed or who is an owner, creator or the subject of the documents or materials that are to be produced pursuant to a subpoena may, prior to the time specified therein for compliance, but not later than 15 days after the date of service of such subpoena, request that the subpoena be quashed or modified…
- **Proposed:** is_obligation=True, type=requirement, party=any person to whom a subpoena is directed
- **Rationale (claude-fable-5):** Conditional duty: request 'shall be made by application filed' and served on all parties

### 162. `fb9bf23377ac6cef` — ⬜ pending

- **Document:** 31-CFR-501 (chars 108347-108485)
- **Provision:** § 501.738; or (iii) In a petition for the Secretary's designee's review of an Administrative Law Judge's decision filed in accordance with
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Cross-reference fragment listing filing contexts; no duty

### 163. `15c91ca6a9050a3a` — ⬜ pending

- **Document:** 31-CFR-501 (chars 117002-117909)
- **Provision:** § 501.726 and requiring the attendance at any such conference of at least one representative of each party who has authority to negotiate concerning the resolution of issues in controversy; (f) Subject to any limitations set forth elsewhere in this subpart, considering and ruling on all procedural and other motions; (g) Upon notice to all parties, reopening any hearing prior to the issuance of a d…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Enumerates Administrative Law Judge powers/authorities, not duties

### 164. `bc4927c381e67387` — ⬜ pending

- **Document:** 31-CFR-501 (chars 121378-122125)
- **Provision:** § 501.732(c), or by motion. Upon notice to all parties to the proceeding, the Administrative Law Judge may, by order, specify corrections to the transcript. (b) Contents of the record. The record of each hearing shall consist of: (1) The Order Instituting Proceedings, Answer to Order Instituting Proceedings, Notice of Hearing and any amendments thereto; (2) Each application, motion, submission or …
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Discretionary 'may specify corrections'; 'record shall consist of' defines contents

### 165. `f374317d90724574` — ⬜ pending

- **Document:** 31-CFR-501 (chars 135784-136264)
- **Provision:** § 501.746 Referral to United States Department of Justice; administrative collection measures. In the event that the respondent does not pay any penalty imposed pursuant to this part within 30 calendar days of the mailing of the written notice of the imposition of the penalty, the matter may be referred for administrative collection measures or to the United States Department of Justice for approp…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Discretionary 'the matter may be referred'; nonpayment is a condition, not a duty

### 166. `d1a58453e9360e2e` — ⬜ pending

- **Document:** C1-2026-10036 (chars 0-356)
- **Provision:** <html> <head> <title>Federal Register, Volume 91 Issue 123 (Monday, June 29, 2026)</title> </head> <body><pre> [Federal Register Volume 91, Number 123 (Monday, June 29, 2026)] [Rules and Regulations] [Page 38991] From the Federal Register Online via the Government Publishing Office [<a href="http://www.gpo.gov">www.gpo.gov</a>] [FR Doc No: C1-2026-10036]
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** HTML header and Federal Register citation boilerplate

### 167. `754706afed881e29` — ⬜ pending

- **Document:** C1-2026-10036 (chars 360-1016)
- **Provision:**  ========================================================================  Rules and Regulations   Federal Register  ________________________________________________________________________    This section of the FEDERAL REGISTER contains regulatory documents  having general applicability and legal effect, most of which are keyed  to and codified in the Code of Federal Regulations, which is publis…
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Federal Register masthead boilerplate describing the Rules section

### 168. `1de05235b44ce736` — ⬜ pending

- **Document:** C1-2026-10036 (chars 1305-1512)
- **Provision:** In rule document 2026-10036 beginning on page 29340 in the issue of Tuesday, May 19, 2026, make the following correction: On page 29340, in the first column, the heading should read as set forth above.
- **Proposed:** is_obligation=False
- **Rationale (claude-fable-5):** Editorial correction notice to a prior document heading


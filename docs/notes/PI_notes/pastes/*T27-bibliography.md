# T27. Bibliography surgery

Date 2026-08-19. Deliverable `docs/notes/PI_notes/pastes/refs-cleaned.bib`.
Replaces the Overleaf `refs.bib` whole. No `.tex` file changes.

The cleaned file was built by script from `docs/paper/refs.bib`, so the diff is
mechanical except for the corrections listed in section 3, each of which names
the record it was checked against.

## 0. The three things worth a minute

1. **Four cited entries described the wrong paper.** `kemmaka2025hybagg`,
   `zhang2024fedsd2c` and `itahara2021dsfl` carried a title that is not the
   paper's title, and `malinovsky2024oneround` had `author = {Anonymous}`. All
   four are corrected against the record. Section 3.
2. **The bibliography alone takes the paper from 21 pages to 20.** Both builds
   ran here with the same sections and the same `IEEEtran` style. That is a
   third of what T29 needs, at no cost to the text.
3. **Three pairs of keys point at the same paper.** One pair shared a key
   outright and is merged. The other two are marked in the file and need a PI to
   say which one goes. Section 6.

## 1. What changed, by category

| change | count |
|---|---|
| entries in, entries out | 139 in, 139 out |
| `url` removed | 23 |
| `doi` removed | 20 |
| `note` removed | 27 |
| `publisher` removed | 15 |
| `series` removed | 5 |
| `organization` removed | 2 |
| `eprint`, `archivePrefix`, `primaryClass` removed | 2 each |
| `booktitle` cut to the short form | 44 |
| `journal` name made consistent | 12 |
| entry type corrected | 10 |
| `pages` dropped from conference entries | 31 |
| `volume` or `number` dropped from conference entries | 12 |
| entries whose facts were corrected against a source | 18 |
| duplicate key merged | 1 |
| stale "verify this before submission" comments now answered | 4 |

The original file has 140 `@` blocks but 139 keys, because `pirillo2025reboot`
appears twice. BibTeX silently keeps the first. The cleaned file has one.

Counts that differ from the T27 brief: `note` is 27 keys, not 23, and the brief
counted 30 long booktitles where the script found 44.

Field order in every entry is now title, author, venue, volume, number, pages,
year. Nothing else appears.

### Short forms used for conferences

`IEEE S&P`, `IEEE EuroS&P`, `IEEE CSF`, `IEEE FOCS`, `IEEE ICDE`, `IEEE ICC`,
`IEEE ICNC`, `IEEE ICASSP`, `IEEE TPS-ISA`, `USENIX Security`, `USENIX ATC`,
`ACM CCS`, `ACM KDD`, `NeurIPS`, `ICLR`, `ICML`, `NDSS`, `EUROCRYPT`,
`ASIACRYPT`, `CANS`, `EMNLP`, `AAAI`, `AISTATS`, `CVPR`, `WACV`, `IJCAI`,
`WPES`, `WAHC`, `KSEM`, `APWeb-WAIM`, `Cloud S&P`, `ACNS Workshops`,
`PriML Workshop, NeurIPS`, `PPML Workshop, ACM CCS`, `NeurIPS FL Workshop`,
`IJCAI Workshop on Federated Learning`.

### Journal names made consistent

The file already used `PoPETs` and `IEEE TIFS` while spelling other journals
out, so the long ones were shortened to match.

| was | is |
|---|---|
| IEEE Transactions on Dependable and Secure Computing | IEEE TDSC |
| IEEE Transactions on Vehicular Technology | IEEE TVT |
| ACM Transactions on Intelligent Systems and Technology | ACM TIST |
| IACR Transactions on Cryptographic Hardware and Embedded Systems | IACR TCHES |
| Transactions on Machine Learning Research (TMLR) | TMLR |
| IEICE Transactions on Fundamentals of Electronics, Communications and Computer Sciences | IEICE Trans. Fundamentals |

Reverse any of these with one search and replace if you prefer the long form.

### Two judgement calls, both reversible

- **Pages dropped from conference entries.** Checklist rule 20 permits it to
  save space, and T29 needs the space. 31 entries lost a page range. Journal
  page ranges are untouched.
- **arXiv preprints keep their identifier.** A preprint with no venue has no
  other handle. `@article` preprints keep `journal = {arXiv preprint
  arXiv:NNNN.NNNNN}` and `@misc` preprints carry `howpublished =
  {arXiv:NNNN.NNNNN}`. This is the one place where content that used to sit in a
  `note` was kept rather than deleted.

### Comments in the file

Every comment line in the original survives, except four blocks that told a
future reader to verify something that is now verified. Those were replaced by
what the check found. The block explaining why `karakoc2024fullsa` is uncited on
purpose is intact and the entry is still there.

The provisions that used to sit in the `note` field of the four legal entries
were moved into `%` comments above each entry. BibTeX ignores them, so the
bibliography is clean, and the record of which article of GDPR, HIPAA, KVKK and
the AI Act the paper relies on is not lost.

## 2. Entries promoted from preprint or corrected to a published form

Ten entry types changed. Each was checked against the record named.

| key | was | is | record checked |
|---|---|---|---|
| `xu2022hercules` | `@misc`, arXiv:2207.04620 | `@article`, IEEE TDSC 20(5):4418--4433, 2023 | DBLP `journals/tdsc/XuHXZLHD23` |
| `atapoor2024vfhe` | `@misc`, ePrint 2024/582 | `@article`, IACR Communications in Cryptology 1(1):24, 2024 | DBLP search record for the title |
| `kasiviswanathan2011can` | `@inproceedings`, booktitle "SIAM Journal on Computing" | `@article`, SIAM J. Comput. 40(3):793--826, 2011 | DBLP search record for the title |
| `liu2023dplora` | `@article`, arXiv:2312.17493 | `@article`, ACM TMIS 16(2):1--24, 2025 | DBLP search record for the title |
| `wang2025towards` | `@article`, arXiv:2505.02426 | `@article`, Neurocomputing 664:132088, 2026 | DBLP search record for the title |
| `xu2024dpdylora` | `@article`, arXiv:2405.06368 | `@inproceedings`, IEEE ICC, 2026 | DBLP search record for the title |
| `li2025shelora` | `@article`, arXiv:2505.21051 | `@inproceedings`, ICLR, 2026 | arXiv 2505.21051, comment field reads "ICLR 2026" |
| `alamin2025vit` | `@article`, arXiv:2511.20983 | `@inproceedings`, IEEE ICNC, 2026 | arXiv 2511.20983, journal_ref reads "IEEE ICNC2026" |
| `kemmaka2025hybagg` | `@article`, arXiv:2511.23252 | `@inproceedings`, IEEE TPS-ISA, 2025 | arXiv 2511.23252, comment names TPS-ISA 2025 |
| `zari2021efficient` | `@misc`, arXiv:2111.00430 | `@inproceedings`, PriML Workshop NeurIPS, 2021 | arXiv 2111.00430, comment names the workshop |
| `li2019fedmd` | `@article`, arXiv:1910.03581 | `@inproceedings`, NeurIPS FL Workshop, 2019 | arXiv 1910.03581, comment names the workshop |
| `itahara2021dsfl` | `@inproceedings`, IEEE ICC | `@article`, IEEE Transactions on Mobile Computing | arXiv 2008.06180, journal_ref and DOI 10.1109/TMC.2021.3070013 |

`agamennone2025polynomial` stayed `@article` and gained the page range
977--980, from the same DBLP record that gives volume 108 and issue 7.

## 3. Corrections beyond formatting, and where they came from

These change what the entry says a paper is. Each names its source.

1. **`kemmaka2025hybagg`, cited, and cited for a number.** The entry gave the
   title as "Hyb-Agg: Communication-Efficient Secure Aggregation via Hybrid
   Multi-Key Homomorphic Encryption and Masking" and the authors as "Kemmaka and
   Tran". arXiv 2511.23252 is titled "One-Shot Secure Aggregation: A Hybrid
   Cryptographic Protocol for Private Federated Learning in IoT", by Imraul
   Emmaka and Tran Viet Xuan Phuong, accepted at IEEE TPS-ISA 2025. Hyb-Agg is
   the protocol's name inside the paper, not the paper's title, and the first
   author's surname was misspelled. Corrected. **The 12 times expansion and the
   6.3 MB figure that T22 draws on are unaffected**, because
   `comparators/REPORTED_RESULTS.md` quotes them from the same arXiv item.
2. **`zhang2024fedsd2c`, cited.** The entry read "Federated One-Shot Learning
   with Data-Free Distillation" by "Zhang, Yuhao and others". The paper is
   "One-shot Federated Learning via Synthetic Distiller-Distillate
   Communication" by Junyuan Zhang, Songhua Liu and Xinchao Wang, NeurIPS 2024,
   arXiv 2412.05186. Corrected. The venue was right.
3. **`itahara2021dsfl`, cited.** The entry read "DS-FL: Distillation-Based
   Semi-Supervised Federated Learning for Medical Image Classification", IEEE
   ICC 2021. arXiv 2008.06180 gives the real title, "Distillation-Based
   Semi-Supervised Federated Learning for Communication-Efficient Collaborative
   Training with Non-IID Private Data", and a journal_ref of IEEE Transactions
   on Mobile Computing with DOI 10.1109/TMC.2021.3070013. There is no medical
   imaging in it. Title and journal corrected, year left at 2021 so the in-text
   citation does not move. **Volume, issue and pages are still missing, see
   section 5.**
4. **`malinovsky2024oneround`, cited.** The author field was `Anonymous`. arXiv
   2412.04650 lists Ziyao Wang, Bowei Tian, Yexiao He, Zheyu Shen, Guoheng Sun,
   Yuhan Liu, Luyang Liu, Meng Liu and Ang Li. Corrected. The key is now a
   misnomer, and it stays, because keys must resolve.
5. **`wei2025fedshe`, cited.** Volume 260 and year 2025 were both wrong. DBLP
   `journals/cn/WeiHLW26` gives Computer Networks 274:111813, 2026. Corrected.
   The title also carried an en dash, `FedSHE--CQ`, now a hyphen.
6. **`wang2025towards`, cited.** The author field said "Wang, Jian and others",
   which matches nobody on the paper. The journal version in Neurocomputing
   lists Flora Amato, Lingyu Qiu, Muhammad Tanveer, Salvatore Cuomo, Daniela
   Annunziata, Fabio Giampaolo and Francesco Piccialli. Corrected, and promoted
   from preprint.
7. **`li2025shelora`, cited.** "Li, Jianmin and others" was a bad split of
   "Jianmin Liu". arXiv 2505.21051 lists Jianmin Liu, Li Yan, Borui Li, Lei Yu
   and Chao Shen. Corrected.
8. **`alamin2025vit`, cited.** Every given name was wrong. arXiv 2511.20983
   lists Al Amin, Kamrul Hasan, Liang Hong and Sharif Ullah, against the
   entry's "Md Al Amin, Mahmudul Hasan, Sangtae Hong, Sami Ullah". The title
   said "with Lightweight" where the paper says "Leveraging Lightweight".
   Corrected.
9. **`zhang2024fedit`, cited.** Yufan Zhou was missing from the author list.
   Added, from arXiv 2305.05644.
10. **`carlini2024stealing`, cited.** "and others" replaced by the full
    fourteen names from arXiv 2403.06634.
11. **`kerkouche2023client`, cited.** Pages read 15--30 where DBLP gives 45--60
    for WPES 2023. Since conference pages are dropped, the wrong range is simply
    gone.
12. **`shao2024selective` and `shao2023selective`, both uncited.** One said
    pages 1--15, the other page 116. PubMed Central record PMC10774276 prints
    "Nat Commun. 2024 Jan 8;15:349". Both corrected to volume 15, article 349.
13. **`kerkouche2023property`, uncited.** Listed five authors and IEEE S&P.
    DBLP shows arXiv 2303.03908 is the same three-author WPES 2023 paper as
    `kerkouche2023client`. Corrected and marked as a duplicate.
14. **`cui2025mia`, uncited.** "Cui, Xiang and Zhang, Hao and Pei, Yizheng" is
    wrong in all three given names. arXiv 2505.11837 lists Ziyao Cui, Minxing
    Zhang and Jian Pei. Corrected.
15. **`beitollahi2024parametric`, uncited.** The file's own comment said the
    author list was written from recollection. It was wrong. arXiv 2402.01862
    lists Mahdi Beitollahi, Alex Bie, Sobhan Hemati, Leo Maxime Brunswic, Xu Li,
    Xi Chen and Guojun Zhang. Corrected. **The venue is still unverified**, see
    section 4.
16. **`gu2023ldia`, cited.** The author field read "Gu, Ying and Yuebin Bai",
    which BibTeX parses as a person called Bai with the given name Yuebin, by
    luck rather than syntax. Re-formatted. The first author's given name is
    still unconfirmed, see section 4.
17. **`lyubashevsky2010ideal`, cited.** Names were in first-last order where
    every other entry uses last-first. Re-ordered, same people.
18. **`pirillo2025reboot`, cited.** Appeared twice under one key. Merged. The
    file's warning that a third author may have been dropped is closed: arXiv
    2506.19693 lists exactly Alberto Pirillo and Luca Colombo.

Four stale comment blocks were replaced by their answers: the Hercules venue
query, the ReBoot author query, the "verify these three" note over Iron, BOLT
and PUMA, and the "verify it against the record" note over FedPFT. Iron is
confirmed at NeurIPS 2022 and BOLT at IEEE S&P 2024, both from DBLP.

## 4. Not verified, so left alone

| key | cited | what is missing |
|---|---|---|
| `dong2023puma` | yes | PUMA has a published version. DBLP holds only the preprint. A journal called Security and Safety appears to carry it in 2025, but that page returns 403 here, so no volume or pages. Left as an arXiv preprint. |
| `beitollahi2024parametric` | no | The venue. arXiv names none. The entry still says NeurIPS FL Workshop 2024, which nothing supports. Either confirm it or drop the entry. |
| `gu2023ldia` | yes | The first author's given name. Every source reached prints "Y. Gu". The entry says Ying. |
| `galichin2025glira` | no | Volume, issue and pages for IEEE TIFS 2025. |
| `kanpak2024cure` | no | Volume, issue and pages. arXiv 2407.08977 gives a journal_ref of "Proceedings on Privacy Enhancing Technologies, 2026" and nothing more. Your own paper, so you will know. |
| `itahara2021dsfl` | yes | Volume, issue, pages and possibly the year. Secondary sources put the final version at IEEE TMC 22(1):191--205, and DBLP confirms that TMC 22(1) is January 2023, so the year may need to move from 2021 to 2023. No first-hand record was reachable, so nothing was written. |
| `wang2024flora`, `bai2024flexlora` | yes | The NeurIPS 2024 venue. Both arXiv records are silent. Left as the file had them. |
| `feddiff2024` | yes | Nothing missing. Noting only that the key says 2024 and the entry says 2025, which is right, because WACV 2025. |
| `wan2024privacy` | no | Nothing missing. The key says 2024 and the year is 2026, which matches arXiv 2606.08252. |

DBLP's search API stopped answering partway through this pass. Everything above
that is still open failed for that reason, not because the record disagrees.

## 5. `@article` entries with no volume, issue or pages

20 of 44, down from 27. Sixteen are unpublished preprints, where there is no
volume to give.

**Preprints with no published version found.** `alhossain2025training`,
`guha2019oneshot`, `cui2025mia`, `wan2024privacy`, `chang2019cronus`,
`cosgun2025federated`, `malinovsky2024oneround`, `chiang2025cnn`,
`bommasani2021opportunities`, `xiao2023offsite`, `li2024privtuner`,
`frery2025private`, `hsu2019measuring`, `dong2023puma`.

**Journals that publish without volume or pages.** `dockhorn2022dpdm`,
`tao2024taskarith`, `mehta2022dpfeatures`, all TMLR. TMLR assigns no volume and
no page range, so there is nothing to add.

**Genuinely incomplete, and listed in section 4.** `kanpak2024cure`,
`itahara2021dsfl`, `galichin2025glira`.

Three `@misc` entries carry no venue field at all: `kvkk2016`, `pipl2021` and
`dpdp2023`. Each is a national statute whose title is its citation. Every entry
in the file carries a year. No entry is a bare link, so the last-access-date
rule in checklist item 21 does not bite anywhere.

## 6. Duplicates

| keys | same paper | state |
|---|---|---|
| `pirillo2025reboot` and `pirillo2025reboot` | yes, one key used twice | **Merged.** One entry now. |
| `kerkouche2023client` and `kerkouche2023property` | yes, WPES 2023, Kerkouche, Ács, Fritz | Both kept, both corrected, `kerkouche2023property` marked in the file for deletion. Only `kerkouche2023client` is cited. |
| `shao2023selective` and `shao2024selective` | yes, Nat Commun 15:349, 2024 | Both kept, both corrected, `shao2023selective` marked in the file for deletion. Neither is cited. |

A title-normalised scan over all 139 entries found no other pair.

## 7. Every cited key still resolves

- Cite commands were pulled from `docs/paper/main.tex` and
  `docs/paper/sections/*.tex`. **107 distinct keys.**
- All 107 are present in `refs-cleaned.bib`. Nothing missing.
- No key was renamed and no entry was deleted. 139 keys in, 139 keys out.
- `karakoc2024fullsa` is present, uncited, with its explanation intact.
- 32 entries are uncited, the same 32 as before this pass.

Two builds were run here to check it:

1. A throwaway document citing all 139 keys. BibTeX finished with no warning of
   any kind.
2. The manuscript itself, with `refs-cleaned.bib` swapped in. Three passes of
   `pdflatex` plus `bibtex`, zero undefined citations, zero BibTeX warnings.

**The manuscript builds at 20 pages with the cleaned file, against 21 with the
current one.** Same sections, same style, only the bibliography differs.

## 8. What needs a person

1. Confirm the four corrections in section 3 that change what a cited paper is,
   above all `kemmaka2025hybagg` and `zhang2024fedsd2c`. Both are load-bearing
   in the related work and the comparison tables.
2. Decide whether `itahara2021dsfl` moves to 2023 with volume 22, issue 1 and
   pages 191--205. That changes an in-text year.
3. Say which of the two duplicate pairs in section 6 to delete.
4. Say whether `beitollahi2024parametric` keeps its unsupported workshop venue
   or leaves the file.
5. Fill in volume, issue and pages for `kanpak2024cure`, which is yours.
6. Say whether the shortened journal names in section 1 are wanted, and whether
   conference page ranges should come back.

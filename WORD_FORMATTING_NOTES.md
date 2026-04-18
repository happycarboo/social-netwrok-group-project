# Word Table Formatting Notes
> Internal reference for group project `G1_Final Report Draft.docx`
> Last updated: Apr 2026

---

## 1. Document layout (measured)

| Property | Value |
|---|---|
| Page size | A4 (8.27 in × 11.69 in) |
| Left margin | 1.00 in |
| Right margin | 1.00 in |
| **Usable page width** | **6.27 in** |
| Body font | Calibri |

> **Rule:** Any table's total column width must not exceed **6.27 in** or it will overflow and clip.

---

## 2. Table styles in the document

Two styles are used across the 18 tables:

| Style | Used for | Border behaviour |
|---|---|---|
| `Table Grid` | Most analysis tables (cohesion, centralisation, Q2.3, appendix) | Full borders all cells |
| `Normal Table` | Mixed / HTML-imported tables (RQ2 top-10, egocentric, RQ4, etc.) | Minimal / no borders |

**Preference:** Use `Table Grid` for all new/updated tables so they look consistent.

---

## 3. Why alignment goes wrong (root cause)

When tables are inserted from HTML (via pandoc or Word's paste-from-HTML), Word sets
each column's `tcW` (cell width in XML) to **~0.001–0.002 in** — effectively zero — and
relies on `autofit` to expand the table.

This causes two problems:
- `autofit=True` ignores any width you set in python-docx — Word does its own thing.
- `autofit=False` with near-zero widths collapses all columns to the left.

**Fix pattern (python-docx):**
```python
table.autofit = False
# set every cell width explicitly, summing to <= 6.27in
for row in table.rows:
    for i, cell in enumerate(row.cells):
        cell.width = Inches(col_widths[i])
# also set the tblW element in XML to the exact total width
from lxml import etree
WD = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
tblPr = table._tbl.find(f'{{{WD}}}tblPr')
tblW  = tblPr.find(f'{{{WD}}}tblW')
if tblW is None:
    tblW = etree.SubElement(tblPr, f'{{{WD}}}tblW')
total_twips = int(sum(col_widths) * 914400)  # EMU -> twentieths of a point: * 914400 / 635
tblW.set(f'{{{WD}}}w',    str(int(sum(col_widths) * 1440 * 20 / 20)))  # in twentieths of pt
tblW.set(f'{{{WD}}}type', 'dxa')
```

---

## 4. Recommended column widths per table

### Appendix A — Full Centrality Table (10 cols, total = 6.27 in)

| Col | Header | Width (in) |
|---|---|---|
| 0 | Username | 1.20 |
| 1 | Party | 0.75 |
| 2 | Out-Deg | 0.52 |
| 3 | In-Deg | 0.52 |
| 4 | Out-Str | 0.52 |
| 5 | In-Str | 0.52 |
| 6 | Betweenness | 0.75 |
| 7 | Closeness | 0.65 |
| 8 | Eigenvector | 0.65 |
| 9 | VC | 0.39 |
| **Total** | | **6.47 in** |

> Reduce VC col or Betweenness to bring to 6.27 if still overflowing.

### RQ4 — What-if table (5 cols, total = 6.27 in)

| Col | Header | Width (in) |
|---|---|---|
| 0 | Metric | 1.50 |
| 1 | Baseline | 0.80 |
| 2 | Remove 15 overall | 1.32 |
| 3 | Remove 15 Dem | 1.32 |
| 4 | Remove 15 Rep | 1.33 |
| **Total** | | **6.27 in** |

---

## 5. Font / spacing settings for compact tables

```python
for r_i, row in enumerate(table.rows):
    for c_i, cell in enumerate(row.cells):
        for p in cell.paragraphs:
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after  = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            # alignment
            if r_i == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER   # header row: centred
            elif c_i in (0, 1):
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT     # text cols: left
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER   # numeric cols: centred
            for run in p.runs:
                run.font.size = Pt(9)
                run.font.bold = (r_i == 0)
                run.font.name = 'Calibri'
```

---

## 6. Things that did NOT work

| Attempt | Problem |
|---|---|
| `table.autofit = True` + set widths | Word overrides widths; columns still uneven |
| Setting only `cell.width` without `autofit = False` | Ignored by Word |
| Copying `tblPr` from reference table without fixing `tblW` | Total table width stayed wrong |
| Setting widths > 6.27 in total | Table overflows right margin; last column clips |

---

## 7. Test files (can be deleted after final report)

| File | Purpose |
|---|---|
| `G1_Final Report Draft_test.docx` | Heading + image replacement test |
| `G1_Final Report Draft_tabletest.docx` | Simple table insert test |
| `G1_Final Report Draft_test_compacttable.docx` | Compact appendix table attempt v1 |
| `G1_Final Report Draft_test_compacttable_v2.docx` | Page-safe width fix |
| `G1_Final Report Draft_nativetable.docx` | Native tblPr copy from Q2.3 table |

---

## 8. TODO — still to resolve

- [ ] Fix appendix table alignment by setting `tblW` in XML explicitly to `6.27 in`
- [ ] Apply same compact style to **all** `Normal Table` style tables (imported from HTML)
- [ ] Verify on Windows Word (not just macOS) — font substitution may shift column widths

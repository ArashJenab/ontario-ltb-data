# Brief: extract dollar amounts from LTB order PDFs, by application type

## Why this needs Claude Code, not claude.ai

In this chat, my `web_fetch` tool can only open a URL that you typed yourself
or that came back from a live web search — and even when a link clears that
check, the document host (`d3hf2qahezjxpx.cloudfront.net`) serves files
without a proper `Content-Type: application/pdf` header, so the tool receives
raw binary it can't parse. Neither restriction applies to Claude Code: it runs
on your machine (or a sandboxed VM you control) with a normal Python HTTP
stack, so `requests.get(url)` just gets the bytes regardless of what header
the server sends.

## Objective

For a sample of LTB orders in each application category, extract whatever
dollar amount(s) the order states (rent arrears, amount ordered paid,
rebate, abatement, above-guideline increase, etc.), then report per-category
statistics: count found, min, max, median, mean.

## Input data

The source file is the open-data export you already have:
`86e75d11-1c2c-4cd9-9b0d-9fccec302b30.json` — a dict with two top-level keys,
`fields` (column definitions) and `records` (a list of 40,844 rows, each a
flat array in the same order as `fields`). Relevant columns and their index:

| Field | Notes |
|---|---|
| `File Number/Numéro de dossier` | e.g. `LTB-L-083514-25` |
| `Applications/Requêtes` | application code, e.g. `L1`, `T2`, or combos like `L1;L2` |
| `Application Type/Type de requête` | single letter: `L`, `T`, or `C` |
| `Document Type/Type de document` | `Order`, `ExParte Order`, `Review Order`, `Amended Order` |
| `Order Date/Date de l'ordonnance` | `YYYY-MM-DD` |
| `Document ID/Identifiant du document` | internal doc id |
| `ContentDownload URL/URL de téléchargement du contenu` | a full string like `=HYPERLINK("https://...pdf","View file")` — you need to regex out the URL between the first pair of quotes |

Load with `json.load()`, then build `field_index = {f['id']: i for i, f in enumerate(data['fields'])}` so you can index rows by name instead of position.

## Sampling plan

Categories already identified as the highest-volume, most meaningful buckets
(counts as of this export):

| Code | Meaning | N in dataset |
|---|---|---|
| L1 | Evict for non-payment + collect rent owed | 20,162 |
| L2 | End tenancy / evict, other reasons | 5,247 |
| L4 | Evict — tenant failed to meet settlement/order | 5,158 |
| T2 | Tenant rights application | 2,200 |
| T6 | Maintenance | 1,079 |
| T1 | Rent rebate | 1,041 |

Filter to rows where `Applications/Requêtes` == exactly that code (skip
combo codes like `L1;L2` for a clean per-category read). Use
`random.sample(pool, N)` with a fixed seed for reproducibility.

Start with **N=10 per category (60 PDFs total)** to validate the pipeline
end-to-end before scaling up. Once the extraction logic is proven, this is
easy to re-run at N=100–200 per category for a statistically sturdier read,
or even the full population if you want it (see "Scaling up" below).

## Download step

- Plain `requests.get(url, headers={'User-Agent': 'Mozilla/5.0 ...'})`,
  `timeout=30`, wrap in try/except, retry once on failure.
- **Be a polite scraper**: this is a real government tribunal's file host.
  Add a small delay between requests (`time.sleep(0.5–1s)`), don't
  parallelize beyond ~4-5 concurrent connections, and stop if you start
  seeing 429/503 responses.
- Save each PDF to a local `./pdfs/<file_number>.pdf` so extraction can be
  re-run without re-downloading.

## Text extraction step

These are LTB orders — some are digitally generated (`Document Type: Order`
with a clean filename), others are scanned/stamped/signed copies (filenames
containing `Signed`, `Certified`, `-EX`, `-SA` often are scans). Plan for
both:

1. Try `pdfplumber` or `PyPDF2` first — fast, works for text-native PDFs.
2. If extracted text is empty or under ~50 characters, fall back to OCR:
   `pdf2image.convert_from_path()` → `pytesseract.image_to_string()` per
   page. (Requires `poppler-utils` and `tesseract-ocr` installed on the
   system — `apt-get install poppler-utils tesseract-ocr` on Linux.)
3. Log which method worked for each doc — this is useful signal on its own
   (e.g. if ExParte orders are systematically scanned and OCR-only, that
   explains lower extraction success there).

## Dollar amount extraction

Don't just regex for `\$[\d,]+(\.\d{2})?` and take the first hit — LTB
orders usually mention several dollar figures (filing fee, arrears, per diem
rent, cost award, total). Instead:

1. Extract **all** dollar amounts with context: for each regex match, keep
   ~80 characters before and after it.
2. Classify each match by nearby keywords, e.g.:
   - "arrears", "rent owing", "amount owing", "shall pay to the Landlord" → arrears/amount owed (L1, L9, L10, L4)
   - "compensation", "abatement", "rent reduction" → tenant remedy (T2, T3, T6)
   - "rebate" → T1
   - "filing fee", "application fee" → exclude from the "amount claimed/owed" figure, but worth tracking separately
   - "per diem", "per day" → exclude (it's a rate, not a total)
3. Where an order clearly states a single total (e.g. "the Tenant owes the
   Landlord $X"), that's your primary figure. Where it's ambiguous or the
   application was dismissed/withdrawn (no monetary order at all — common
   for T2/T6 where the remedy might be a repair order, not money), record
   `amount_found = None` rather than guessing.
4. Keep the raw matched text alongside the parsed number, so you (or Claude
   Code on a later pass) can spot-check extraction accuracy against a few
   PDFs manually.

This step is inherently fuzzy — LTB order templates vary by adjudicator and
are not perfectly standardized. Treat the output as a **best-effort
estimate**, not ground truth, and say so in the final stats.

## Output format

One row per document in a CSV/DataFrame:

```
file_number, category, doc_type, order_date, extraction_method (text/ocr),
all_amounts_found (list), primary_amount, amount_type (arrears/rebate/etc), notes
```

## Aggregation

Group by `category`, then for `primary_amount` (dropping `None`s) report:
`count_with_amount`, `count_total`, `min`, `max`, `median`, `mean`. Also
report the found-vs-not-found rate per category — that rate is itself an
interesting finding (e.g. you'd expect T2/T6 to have money stated far less
often than L1, since a lot of tenant-rights/maintenance orders end in a
repair order or abatement rather than a lump sum).

## Scaling up later

If the 60-doc pilot works and you want a real population-level number
instead of an illustrative sample: at ~1 request/second with politeness
delays, 40,844 downloads would take roughly 11-12 hours single-threaded —
plan for a background/overnight run, modest concurrency (4-5 workers), and
checkpointing (skip files already downloaded) so it's resumable if
interrupted. A stratified sample of a few hundred per category would likely
get you within a reasonable margin of error much faster and is probably the
more practical middle ground.

## Suggested script skeleton

```python
import json, re, time, random
from pathlib import Path
import requests
import pdfplumber

random.seed(42)
Path('pdfs').mkdir(exist_ok=True)

with open('86e75d11-1c2c-4cd9-9b0d-9fccec302b30.json') as f:
    data = json.load(f)

fields = [f['id'] for f in data['fields']]
idx = {name: i for i, name in enumerate(fields)}

def extract_url(cell):
    m = re.search(r'HYPERLINK\("([^"]+)"', cell or '')
    return m.group(1) if m else None

CATEGORIES = ['L1', 'L2', 'L4', 'T2', 'T6', 'T1']
N_PER_CATEGORY = 10

by_cat = {}
for r in data['records']:
    code = r[idx['Applications/Requêtes']]
    if code in CATEGORIES:
        by_cat.setdefault(code, []).append(r)

sample = {cat: random.sample(rows, min(N_PER_CATEGORY, len(rows)))
          for cat, rows in by_cat.items()}

DOLLAR_RE = re.compile(r'\$[\d,]+(?:\.\d{2})?')

results = []
for cat, rows in sample.items():
    for r in rows:
        file_number = r[idx['File Number/Numéro de dossier']]
        url = extract_url(r[idx['ContentDownload URL/URL de téléchargement du contenu']])
        if not url:
            continue
        pdf_path = Path('pdfs') / f'{file_number}.pdf'
        if not pdf_path.exists():
            try:
                resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
                resp.raise_for_status()
                pdf_path.write_bytes(resp.content)
                time.sleep(0.75)
            except Exception as e:
                results.append({'file_number': file_number, 'category': cat, 'error': str(e)})
                continue

        text = ''
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
        except Exception:
            pass

        method = 'text'
        if len(text.strip()) < 50:
            # fall back to OCR here (pdf2image + pytesseract) — see brief
            method = 'ocr_needed'

        amounts = DOLLAR_RE.findall(text)
        results.append({
            'file_number': file_number,
            'category': cat,
            'extraction_method': method,
            'all_amounts_found': amounts,
            # primary_amount: apply the keyword-context logic from the brief here
        })

# then: pandas DataFrame(results), groupby('category'), describe()
```

This skeleton deliberately stops short of the OCR fallback and the
keyword-context classifier — those need real iteration against actual
extracted text to get right, which is exactly the kind of thing Claude Code
can do interactively (run it, look at a few raw extracts, tighten the
regex/keywords, re-run).

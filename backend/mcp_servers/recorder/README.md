# Pima County Recorder MCP Server

A tool for searching and downloading recorded documents (liens, judgments, etc.) from the Pima County Recorder's office.

## Features

- **Search documents** by type (Pre-Foreclosure, Federal Liens, Mechanics Liens, etc.)
- **Download PDFs** with automatic CAPTCHA detection
- **Extract data** from PDFs using Vertex AI (Gemini)
- **Lazy initialization** - browser only opens when needed

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure GCP credentials (for Vertex AI extraction)

Option A: Set environment variable
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
export GOOGLE_CLOUD_PROJECT=your-project-id
```

Option B: Place credentials file in `backend/` folder
```
backend/
├── credentials.json    # Auto-detected
├── .env               # Auto-loaded
```

### 3. Run the tool

```bash
python session.py
```

## Commands

| Command | Description |
|---------|-------------|
| `pre` | Search Pre-Foreclosure (LIS PENDENS, NOTICE SALE) |
| `federal` | Search Federal Liens |
| `mechanic` | Search Mechanics Liens |
| `notice` | Search Notice Liens |
| `judgment` | Search Judgments |
| `divorce` | Search Divorce records |
| `probate` | Search Probate records |
| `download <n>` | Download document by index (1-based) |
| `extract <id>` | Extract data from PDF using Vertex AI |
| `quit` | Exit |

## Example Session

```
>>> pre
Searching Pre-Foreclosure...
Found 34 results:
  1. 20253580357 - LIS PENDENS (12/24/2025)
  2. 20253580343 - LIS PENDENS (12/24/2025)

>>> download 1
✅ Downloaded to: downloads/DOC415S311.pdf

>>> extract DOC415S311
Extracting data...
{
  "document_type": "LIS PENDENS",
  "property_address": "123 Main St, Tucson AZ",
  "debtor_name": "John Doe",
  ...
}
```

## Portability

The code auto-detects configuration from:
1. Environment variables (highest priority)
2. `.env` file in `backend/` folder
3. `credentials.json` in `backend/` or `recorder/` folder
4. gcloud default credentials (`~/.config/gcloud/`)

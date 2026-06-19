
# ⌘ OMNI WORKSPACE v2.0

**Universal Document & Media Processing Suite**  
Industrial Brutalist — Tactical Telemetry Interface

[![Python](https://img.shields.io/badge/Python-3.12+-FF0000?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows-1A1A1A?style=flat-square)](https://github.com/RishavGupta01/OmniDoc)
[![Build](https://img.shields.io/badge/Build-PyInstaller-4AF626?style=flat-square)](https://pyinstaller.org)
[![License](https://img.shields.io/badge/License-MIT-FFB000?style=flat-square)](LICENSE)

---

A self-contained, offline-capable desktop application for processing documents, images, and media. Designed with an **Industrial Brutalist** aesthetic — dark, monochrome tactical interface with red-accented telemetry.

Drop files in, pick an operation, and let the engine handle format detection, conversion, and parallel processing.

---

## Features

### Document Organization
| Operation | Description |
|---|---|
| **Merge PDF** | Combine multiple PDFs into one, with ordered page control |
| **Split PDF** | Extract individual pages or ranges into separate files |
| **Reorder Pages** | Drag-to-reorder page sequences within a PDF |
| **Rotate Pages** | Rotate selected pages by 90°, 180°, or 270° |

### Document Optimization
| Operation | Description |
|---|---|
| **Compress PDF** | Reduce file size via content stream optimization |
| **Watermark** | Stamp text watermarks with configurable opacity |
| **Metadata** | Extract and display PDF metadata (author, title, creation date, etc.) |
| **Extract Text** | Full text extraction from any page |

### Format Conversion
| Input | Output Formats |
|---|---|
| PDF | DOCX, Images (PNG/JPEG/TIFF), TXT |
| DOCX/DOC | PDF |
| PPTX | PDF |
| XLSX | PDF |
| Images | PDF (multi-page), DOCX |
| TXT/CSV | PDF |
| Audio/Video | MP3, WAV, AAC, FLAC, OGG, WMA, M4A, OPUS |

### Security
| Operation | Description |
|---|---|
| **Redact** | Search-and-censor text (regex or plain, case-sensitive toggle) |
| **Encrypt** | Password-protect PDFs with AES-128/256 |

### Analysis & OCR
| Operation | Description |
|---|---|
| **OCR (Image)** | Text recognition from scanned images via EasyOCR* |
| **OCR (PDF)** | Page-by-page OCR with image fallback |
| **Summarize** | Multi-algorithm text summarization (Luhn, LSA, KL, TextRank)* |
| **Keywords** | TF-IDF keyword extraction |

> *\* Optional — auto-installed on first use via DependencyManager*

### Batch Processing
- Recursive folder scanning with type-based filtering
- Multi-threaded parallel execution with configurable worker count
- Per-file progress tracking and cancellation support

### System
- Job queue with concurrent execution (ThreadPoolExecutor)
- Real-time system log (TTY-style terminal in sidebar)
- Configurable max worker threads
- Keyboard shortcuts (`Ctrl+O` mount files, `Ctrl+Shift+O` mount directory, `Ctrl+Q` quit, `Esc` cancel all)
- Drag-and-drop file mounting via DropZone

---

## Tech Stack

| Layer | Technology |
|---|---|
| **UI Framework** | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) 5.2+ |
| **PDF Engine** | [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) 1.23+ |
| **PDF I/O** | [pypdf](https://pypdf.readthedocs.io/) 4.0+ |
| **PDF→DOCX** | [pdf2docx](https://github.com/dothinking/pdf2docx) 0.5+ |
| **Image** | [Pillow](https://python-pillow.org/) 10.0+ |
| **Data** | [pandas](https://pandas.pydata.org/) 2.0+, [openpyxl](https://openpyxl.readthedocs.io/) 3.1+ |
| **OCR** | [EasyOCR](https://github.com/JaidedAI/EasyOCR) *(optional)* |
| **Summarization** | [Sumy](https://github.com/miso-belica/sumy) + [NLTK](https://www.nltk.org/) *(optional)* |
| **Office→PDF** | comtypes (Windows + MS Office) or LibreOffice CLI |
| **Binary** | ffmpeg, pandoc *(optional, place in `bin/`)* |
| **Build** | [PyInstaller](https://pyinstaller.org/) 6.21+ |
| **Design** | Industrial Brutalist — Tactical Telemetry Palette |

---

## Installation

### Option 1: Pre-built Binary (Windows)

1. Download the latest release from [Releases](https://github.com/RishavGupta01/OmniDoc/releases)
2. Extract `OmniWorkspace.zip` and run `OmniWorkspace.exe`
3. No Python or pip required

### Option 2: Run from Source

```bash
# Clone the repository
git clone https://github.com/RishavGupta01/OmniDoc.git
cd OmniDoc

# Install core dependencies
pip install -r requirements.txt

# Launch
python main.py
```

*Optional dependencies (EasyOCR, Sumy, NLTK) auto-install on first use.*

### Option 3: Build from Source

```bash
pip install pyinstaller
pip install -r requirements.txt
pyinstaller build.spec
```

Output: `dist/OmniWorkspace.exe` + `dist/OmniWorkspace/` (~260 MB)

---

## Usage

1. **Launch** — Run `OmniWorkspace.exe` (or `python main.py`)
2. **Mount Files** — Drag files into the drop bar, use `Ctrl+O`, or click **MOUNT**
3. **Select Panel** — Choose from sidebar: `[ORGANIZE]`, `[OPTIMIZE]`, `[CONVERT]`, `[SECURITY]`, `[ANALYZE]`, `[BATCH]`, `[HISTORY]`, `[SETTINGS]`
4. **Execute** — Configure options in the panel and click **EXECUTE**
5. **Monitor** — Watch progress bar and TTY system log

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Mount file(s) |
| `Ctrl+Shift+O` | Mount directory |
| `Ctrl+Q` | Quit |
| `Esc` | Cancel all jobs |

---

## Build Architecture

```
OmniDoc/
├── main.py              # Application entry point (~1400 lines)
├── build.spec           # PyInstaller build specification
├── requirements.txt     # Python dependency manifest
├── .gitignore
├── bin/                 # External binaries (ffmpeg, pandoc, etc.)
├── build/               # PyInstaller build cache (gitignored)
└── dist/                # Compiled output (gitignored)
    ├── OmniWorkspace.exe
    └── OmniWorkspace/   # Bundle directory
```

### Core Classes

| Class | Responsibility |
|---|---|
| `OmniWorkspaceApp` | Main application window, layout, panel routing |
| `OmniCoreEngine` | All document processing operations (PDF, images, Office, media) |
| `DependencyManager` | Self-contained dependency checking and auto-install |
| `JobController` | Thread-pooled job queue with cancellation |
| `DropZone` | Drag-and-drop handler with file staging |
| `LogHandler` | Real-time log routing to TTY widget |

### Self-Containment

The app is designed to work fully offline after build:
- **Core packages** (PyMuPDF, pypdf, Pillow, pandas, openpyxl, pdf2docx) are bundled in the executable
- **Optional packages** (EasyOCR, Sumy, NLTK, comtypes) are auto-installed on first use via pip
- **External binaries** (ffmpeg, pandoc) can be placed in `bin/` alongside the executable
- **Office→PDF** uses comtypes (Windows+Office) or LibreOffice CLI as fallback

---

## Screenshots

> *(Add screenshots here)*

---

## Development

### Prerequisites

- Python 3.12+
- Windows (primary target; Linux/macOS compatible with adjustments)

### Setup

```bash
pip install -r requirements.txt
```

### Build

```bash
pyinstaller build.spec
```

The build spec is optimized for minimal bundle size:
- Only core document-processing packages included
- ML frameworks (torch, tensorflow, etc.) excluded
- Web servers, databases, async libraries excluded
- Optional deps installed at runtime by DependencyManager

### Design System

The Tactical Telemetry palette is defined as a lightweight namedtuple at the top of `main.py`:

| Token | Value | Usage |
|---|---|---|
| `BG_ROOT` | `#0A0A0A` | Window background |
| `BG_SURFACE` | `#121212` | Sidebar, cards |
| `BG_ELEVATED` | `#1A1A1A` | Buttons, headers |
| `BG_INPUT` | `#0D0D0D` | Entry fields, textboxes |
| `TEXT` | `#EAEAEA` | Primary text |
| `TEXT_DIM` | `#888888` | Secondary text |
| `TEXT_MUTED` | `#555555` | Placeholder, hints |
| `RED` | `#E61919` | Accent, progress |
| `GREEN` | `#4AF626` | Success, mounted |
| `AMBER` | `#FFB000` | Warnings |

---

## License

MIT License — see [LICENSE](LICENSE).

---

*Built with Python • CustomTkinter • PyMuPDF • Industrial Brutalist Design*

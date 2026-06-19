
# ⌘ OMNI WORKSPACE v2.0

**Universal Document & Media Processing Suite**  
Industrial Brutalist — Tactical Telemetry Interface

[![Python](https://img.shields.io/badge/Python-3.12%2B-FF0000?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows-1A1A1A?style=flat-square)](https://github.com/RishavGupta01/OmniDoc)
[![Build](https://img.shields.io/badge/Build-PyInstaller-4AF626?style=flat-square)](https://pyinstaller.org)
[![Release](https://img.shields.io/github/v/release/RishavGupta01/OmniDoc?style=flat-square&color=FFB000)](https://github.com/RishavGupta01/OmniDoc/releases)
[![License](https://img.shields.io/badge/License-MIT-888888?style=flat-square)](LICENSE)

---

A self-contained, offline-capable desktop application for PDF manipulation, format conversion, OCR, batch processing, and media transcoding. Dark Industrial Brutalist interface with real-time progress logging and thread-pooled job execution.

No Python installation required — download the release and run.

---

## Quick Start

```
1. Download OmniWorkspace-v2.0.zip from Releases
2. Extract and run OmniWorkspace.exe
3. Drop files in, pick an operation, execute
```

Or [build from source](#build-from-source).

---

## At a Glance

| Area | What You Can Do |
|---|---|
| **Organize** | Merge, split, reorder, rotate PDFs |
| **Optimize** | Compress, watermark, extract metadata & text |
| **Convert** | PDF ↔ DOCX ↔ Images ↔ TXT ↔ CSV, Office docs to PDF, audio/video transcoding |
| **Secure** | Redact text (regex/plain), encrypt with password |
| **Analyze** | OCR scanned documents, multi-algorithm summarization, keyword extraction |
| **Batch** | Recursive folder processing with parallel workers |

---

## Installation

### Download (Windows)

Get the latest portable build from the [Releases page](https://github.com/RishavGupta01/OmniDoc/releases). Extract and run `OmniWorkspace.exe`.

### Run from Source

```bash
git clone https://github.com/RishavGupta01/OmniDoc.git
cd OmniDoc
pip install -r requirements.txt
python main.py
```

### Build from Source

```bash
pip install pyinstaller
pip install -r requirements.txt
pyinstaller build.spec
```

Output: `dist/OmniWorkspace.exe` — ~260 MB portable bundle.

---

## Usage

| Step | Action |
|---|---|
| **1. Launch** | Run `OmniWorkspace.exe` |
| **2. Mount** | Drag files to the drop bar, or `Ctrl+O` / `Ctrl+Shift+O` to browse |
| **3. Select Panel** | Sidebar: `[ORGANIZE]`, `[OPTIMIZE]`, `[CONVERT]`, `[SECURITY]`, `[ANALYZE]`, `[BATCH]`, `[HISTORY]`, `[SETTINGS]` |
| **4. Execute** | Configure options, hit **EXECUTE** |
| **5. Monitor** | Track progress bar and TTY log |

### Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Mount file(s) |
| `Ctrl+Shift+O` | Mount directory |
| `Ctrl+Q` | Quit |
| `Esc` | Cancel all jobs |

---

## Format Conversion Matrix

| Input | Output Formats |
|---|---|
| PDF | DOCX, images (PNG/JPEG/TIFF), TXT |
| DOCX / DOC | PDF |
| PPTX | PDF |
| XLSX | PDF |
| Images (PNG/JPG/TIFF) | PDF (multi-page), DOCX |
| TXT / CSV | PDF |
| Audio / Video | MP3, WAV, AAC, FLAC, OGG, WMA, M4A, OPUS |

---

## Architecture

```
OmniDoc/
├── main.py               # Entry point — 1,400+ lines
├── build.spec            # PyInstaller build config
├── requirements.txt      # Dependency manifest
├── distribute.ps1        # One-command build + ZIP packaging
├── bin/                  # External binaries (ffmpeg, pandoc)
├── build/                # PyInstaller cache (gitignored)
└── dist/                 # Compiled output (gitignored)
```

### Core Classes

| Class | Role |
|---|---|
| `OmniWorkspaceApp` | Window, layout, panel routing |
| `OmniCoreEngine` | All document/image/media processing |
| `DependencyManager` | Self-contained auto-install of optional packages |
| `JobController` | ThreadPoolExecutor queue with cancellation |
| `DropZone` | Drag-and-drop mount handler |
| `LogHandler` | Real-time log → TTY widget |

### Self-Containment

- **Bundled:** PyMuPDF, pypdf, Pillow, pandas, openpyxl, pdf2docx
- **Auto-installed:** EasyOCR, Sumy, NLTK, comtypes (on first use)
- **External:** ffmpeg, pandoc (optional, place in `bin/`)

---

## Design System: Tactical Telemetry

| Token | Value | Usage |
|---|---|---|
| `BG_ROOT` | `#0A0A0A` | Window background |
| `BG_SURFACE` | `#121212` | Sidebar, panels |
| `BG_ELEVATED` | `#1A1A1A` | Buttons, headers |
| `BG_INPUT` | `#0D0D0D` | Entry fields |
| `TEXT` | `#EAEAEA` | Primary |
| `TEXT_DIM` | `#888888` | Secondary |
| `TEXT_MUTED` | `#555555` | Placeholder |
| `RED` | `#E61919` | Accent, progress |
| `GREEN` | `#4AF626` | Success |
| `AMBER` | `#FFB000` | Warning |

---

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-idea`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push (`git push origin feature/your-idea`)
5. Open a Pull Request

---

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center"><sub>Built with Python · CustomTkinter · PyMuPDF · Industrial Brutalist Design</sub></p>

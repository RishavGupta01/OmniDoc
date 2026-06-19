#!/usr/bin/env python3
"""
OMNI WORKSPACE // v2.0
Universal Document & Media Processing Suite
Industrial Brutalist — Tactical Telemetry Interface

Self-contained: auto-installs missing dependencies.
Advanced: drag-drop, batch jobs, cancellation, thread pool, multi-algorithm analysis.
"""
import os, sys, json, io, re, queue, time, shutil, struct, hashlib, threading, subprocess, traceback, importlib, itertools, functools, warnings
from pathlib import Path
from datetime import datetime
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from tkinter import filedialog, messagebox, TclError
_FROZEN = getattr(sys, "frozen", False)

def _bootstrap_imports():
    missing = []
    for mod, pip_name in [
        ("customtkinter", "customtkinter"),
        ("fitz", "PyMuPDF"),
        ("pypdf", "pypdf"),
        ("PIL", "Pillow"),
        ("pandas", "pandas"),
        ("pdf2docx", "pdf2docx"),
    ]:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return

    if _FROZEN:
        sys.exit(f"[FATAL] Bundled dependencies missing: {', '.join(missing)}")

    # Running from source — auto-install
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    print(f"[BOOT] Missing: {', '.join(missing)}. Installing...")
    code = subprocess.call([sys.executable, "-m", "pip", "install", "-r", req_file],
                           shell=(os.name == "nt"))
    if code != 0:
        sys.exit(f"[FATAL] pip install failed. Run: pip install -r {req_file}")

    # Retry after install
    for mod in ["customtkinter", "fitz", "pypdf", "PIL", "pandas", "pdf2docx"]:
        try:
            importlib.import_module(mod)
        except ImportError:
            sys.exit(f"[FATAL] Could not import {mod} after install.")

_bootstrap_imports()

import customtkinter as ctk
import fitz
from pypdf import PdfMerger, PdfReader, PdfWriter
from PIL import Image
import pandas as pd
from pdf2docx import Converter as PDF2DocxConverter

warnings.filterwarnings("ignore")
# =====================================================================
# TACTICAL TELEMETRY PALETTE
# =====================================================================
TT = type("TT", (), {
    "BG_ROOT": "#0A0A0A", "BG_SURFACE": "#121212", "BG_ELEVATED": "#1A1A1A",
    "BG_INPUT": "#0D0D0D", "TEXT": "#EAEAEA", "TEXT_DIM": "#888888",
    "TEXT_MUTED": "#555555", "RED": "#E61919", "GREEN": "#4AF626",
    "AMBER": "#FFB000", "BORDER": "#2A2A2A", "BORDER_SUBTLE": "#1E1E1E",
    "HOVER": "#222222", "MONO": "Consolas", "UI": "Segoe UI",
})()

def ctk_init():
    ctk.set_appearance_mode("Dark")
    for cls, props in {
        "CTk": {"fg_color": TT.BG_ROOT},
        "CTkFrame": {"fg_color": TT.BG_SURFACE, "top_fg_color": TT.BG_SURFACE, "border_color": TT.BORDER},
        "CTkButton": {"fg_color": TT.BG_ELEVATED, "hover_color": TT.HOVER, "text_color": TT.TEXT, "border_color": TT.BORDER, "border_width": 1},
        "CTkEntry": {"fg_color": TT.BG_INPUT, "text_color": TT.TEXT, "border_color": TT.BORDER, "placeholder_text_color": TT.TEXT_MUTED},
        "CTkLabel": {"text_color": TT.TEXT},
        "CTkComboBox": {"fg_color": TT.BG_INPUT, "text_color": TT.TEXT, "border_color": TT.BORDER, "button_color": TT.BG_ELEVATED, "button_hover_color": TT.HOVER, "dropdown_fg_color": TT.BG_SURFACE, "dropdown_hover_color": TT.HOVER, "dropdown_text_color": TT.TEXT},
        "CTkTextbox": {"fg_color": TT.BG_INPUT, "text_color": TT.TEXT, "border_color": TT.BORDER},
        "CTkProgressBar": {"fg_color": TT.BG_SURFACE, "progress_color": TT.RED, "border_color": TT.BORDER},
        "CTkScrollbar": {"fg_color": TT.BG_SURFACE, "button_color": TT.BG_ELEVATED, "button_hover_color": TT.HOVER},
        "CTkSwitch": {"fg_color": TT.BG_ELEVATED, "progress_color": TT.RED, "button_color": TT.TEXT_DIM, "button_hover_color": TT.TEXT},
    }.items():
        for k, v in props.items():
            ctk.ThemeManager.theme[cls][k] = v

def get_bin_path(name):
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    if sys.platform == "win32" and not name.endswith(".exe"): name += ".exe"
    p = os.path.join(base, "bin", name)
    return p if os.path.exists(p) else name

# =====================================================================
# DEPENDENCY MANAGER (Self-Contained)
# =====================================================================
_PACKAGE_MAP = {
    "fitz": "PyMuPDF", "pypdf": "pypdf", "PIL": "Pillow", "pandas": "pandas",
    "openpyxl": "openpyxl", "docx": "python-docx", "pptx": "python-pptx",
    "pdf2docx": "pdf2docx", "easyocr": "easyocr", "comtypes": "comtypes",
    "sumy": "sumy", "bs4": "beautifulsoup4",
}
_CORE_REQUIRED = ["fitz", "pypdf", "PIL", "pandas", "openpyxl", "pdf2docx"]

class DependencyManager:
    def __init__(self, log_fn=None):
        self._log = log_fn
        self._registry = {}
        self._installing = set()
        self._lock = threading.Lock()

    def log(self, msg):
        if self._log: self._log(msg)

    def check(self, mod_name):
        with self._lock:
            if mod_name in self._registry:
                return self._registry[mod_name]
            try:
                importlib.import_module(mod_name)
                self._registry[mod_name] = True
                return True
            except ImportError:
                self._registry[mod_name] = False
                return False

    def ensure(self, mod_name, label=None):
        if self.check(mod_name):
            return True
        pkg = _PACKAGE_MAP.get(mod_name, mod_name)
        return self._install(pkg, label or mod_name)

    def _install(self, pkg, label):
        with self._lock:
            if pkg in self._installing:
                return False
            self._installing.add(pkg)
        self.log(f"[DEPS] Installing {pkg} (auto-setup)...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", pkg],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                self.log(f"[DEPS] Install failed: {result.stderr.strip()}")
                return False
            self.log(f"[DEPS] {pkg} installed.")
            mod_name = next((k for k, v in _PACKAGE_MAP.items() if v == pkg), pkg)
            try:
                importlib.import_module(mod_name)
                self._registry[mod_name] = True
            except ImportError:
                pass
            return True
        except subprocess.TimeoutExpired:
            self.log(f"[DEPS] {pkg} install timed out.")
            return False
        except Exception as ex:
            self.log(f"[DEPS] {pkg} error: {ex}")
            return False
        finally:
            self._installing.discard(pkg)

    def check_core(self, parent_widget=None):
        missing = [m for m in _CORE_REQUIRED if not self.check(m)]
        if not missing:
            return True
        names = ", ".join(_PACKAGE_MAP.get(m, m) for m in missing)
        if parent_widget:
            ok = messagebox.askyesno(
                "Missing Dependencies",
                f"Core packages not found:\n{names}\n\nInstall automatically?",
                parent=parent_widget
            )
            if not ok:
                return False
        for m in missing:
            if not self.ensure(m):
                return False
        return True

# =====================================================================
# JOB CONTROLLER (Bounded Thread Pool + Cancellation + History)
# =====================================================================
_JOB_ID = itertools.count(1)

class Job:
    PENDING, RUNNING, DONE, FAILED, CANCELLED = range(5)
    def __init__(self, name, fn, args=None, kwargs=None, priority=0):
        self.id = next(_JOB_ID)
        self.name = name
        self.fn = fn
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.priority = priority
        self.status = self.PENDING
        self.progress = 0.0
        self.status_text = ""
        self.result = None
        self.error = None
        self._cancel = threading.Event()
        self.start_time = None
        self.end_time = None
        self._future = None

    def cancel(self):
        self._cancel.set()
        self.status = self.CANCELLED

    @property
    def cancelled(self):
        return self._cancel.is_set()

    def elapsed(self):
        if self.start_time is None: return 0
        end = self.end_time or time.time()
        return end - self.start_time

class JobController:
    def __init__(self, max_workers=None):
        self._max = min(max_workers or (os.cpu_count() or 4) * 2, 16)
        self._executor = ThreadPoolExecutor(max_workers=self._max, thread_name_prefix="omni")
        self._jobs = []
        self._active = {}
        self._lock = threading.Lock()
        self._history = []
        self._max_history = 50
        self._on_change = []

    @property
    def max_workers(self): return self._max

    def on_change(self, cb):
        self._on_change.append(cb)

    def _notify(self):
        for cb in self._on_change:
            try: cb()
            except Exception: pass

    def submit(self, name, fn, args=None, kwargs=None, priority=0):
        job = Job(name, fn, args, kwargs, priority)
        with self._lock:
            self._jobs.append(job)
        def wrapper():
            job.status = Job.RUNNING
            job.start_time = time.time()
            with self._lock:
                self._active[job.id] = job
            self._notify()
            try:
                result = fn(*job.args, **job.kwargs)
                if job.cancelled:
                    job.status = Job.CANCELLED
                else:
                    job.status = Job.DONE
                    job.result = result
            except Exception as ex:
                job.status = Job.FAILED
                job.error = traceback.format_exc()
            finally:
                job.end_time = time.time()
                with self._lock:
                    self._active.pop(job.id, None)
                    self._history.append(job)
                    if len(self._history) > self._max_history:
                        self._history = self._history[-self._max_history:]
            self._notify()
        job._future = self._executor.submit(wrapper)
        self._notify()
        return job

    def cancel_job(self, job_id):
        with self._lock:
            for j in self._jobs:
                if j.id == job_id:
                    j.cancel()
                    self._notify()
                    return True
        return False

    def cancel_all(self):
        with self._lock:
            for j in self._jobs:
                if j.status in (Job.PENDING, Job.RUNNING):
                    j.cancel()
            self._notify()

    @property
    def pending_count(self):
        with self._lock:
            return sum(1 for j in self._jobs if j.status == Job.PENDING)

    @property
    def active_count(self):
        return len(self._active)

    def recent(self, n=10):
        with self._lock:
            return list(self._history[-n:])

    def active_jobs(self):
        with self._lock:
            return list(self._active.values())

    def shutdown(self, wait=True):
        self._executor.shutdown(wait=wait)

# =====================================================================
# OMNI-CORE ENGINE v2
# =====================================================================
class OmniCoreEngine:
    def __init__(self, log_fn=None, depman=None):
        self.log = log_fn or (lambda x: None)
        self.dep = depman or DependencyManager(self.log)
        self._ocr_reader = None
        self._ocr_lock = threading.Lock()
        self._nltk_ready = False
        self._nltk_lock = threading.Lock()

    # ---- helpers ----
    def stream_pdf_pages(self, path):
        """Generator: yields (page_num, page_obj) for memory-efficient iteration."""
        doc = fitz.open(path)
        try:
            for i in range(len(doc)):
                yield i, doc[i]
        finally:
            doc.close()

    def _progress(self, job, val, text=""):
        if job:
            job.progress = val
            job.status_text = text
            import gc; gc.collect(0)

    # ==================== PDF SUITE ====================
    def merge_pdfs(self, paths, out, job=None):
        self.log(f"[MERGE] {len(paths)} sources")
        merger = PdfMerger(strict=False)
        try:
            for p in paths:
                merger.append(p)
            merger.write(out)
        finally:
            merger.close()
        self.log(f"[MERGE] → {out}")

    def split_pdf(self, path, out_dir, job=None):
        self.log(f"[SPLIT] {os.path.basename(path)}")
        reader = PdfReader(path)
        base = os.path.splitext(os.path.basename(path))[0]
        n = len(reader.pages)
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            writer.write(os.path.join(out_dir, f"{base}_p{i+1:03d}.pdf"))
            self._progress(job, (i+1)/n, f"Page {i+1}/{n}")
        self.log(f"[SPLIT] {n} pages → {out_dir}")

    def compress_pdf(self, path, out, job=None):
        self.log(f"[COMPRESS] {os.path.basename(path)}")
        reader = PdfReader(path)
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            writer.add_page(page)
            self._progress(job, (i+1)/len(reader.pages))
        writer.compress_identical_objects()
        with open(out, "wb") as f:
            writer.write(f)
        b, a = os.path.getsize(path), os.path.getsize(out)
        r = (1 - a/b) * 100 if b else 0
        self.log(f"[COMPRESS] {b:,} → {a:,} ({r:.0f}%)")

    def redact_text(self, path, out, match, job=None):
        self.log(f"[REDACT] '{match}'")
        doc = fitz.open(path)
        total = len(doc)
        for i, page in enumerate(doc):
            rects = page.search_for(match)
            for r in rects:
                page.add_redact_annot(r, fill=(0, 0, 0))
            page.apply_redactions()
            self._progress(job, (i+1)/total, f"Page {i+1}/{total}")
        doc.save(out)
        doc.close()
        self.log(f"[REDACT] → {out}")

    def encrypt_pdf(self, path, out, pw, job=None):
        self.log(f"[ENCRYPT] AES-128")
        writer = PdfWriter()
        reader = PdfReader(path)
        for i, page in enumerate(reader.pages):
            writer.add_page(page)
            self._progress(job, (i+1)/len(reader.pages))
        writer.encrypt(user_password=pw, owner_password=None, use_128bit=True)
        with open(out, "wb") as f:
            writer.write(f)
        self.log(f"[ENCRYPT] → {out}")

    def watermark_pdf(self, path, out, watermark_text, opacity=0.3, job=None):
        self.log(f"[WATERMARK] '{watermark_text}'")
        doc = fitz.open(path)
        total = len(doc)
        for i, page in enumerate(doc):
            r = page.rect
            page.insert_text(
                (r.width/2 - 100, r.height/2),
                watermark_text,
                fontsize=48, color=(*[0.5]*3, opacity),
                rotate=45, overlay=False
            )
            self._progress(job, (i+1)/total)
        doc.save(out)
        doc.close()
        self.log(f"[WATERMARK] → {out}")

    def reorder_pdf_pages(self, path, out, page_order, job=None):
        """page_order: list of 0-based indices in desired order."""
        self.log(f"[REORDER] {len(page_order)} pages")
        reader = PdfReader(path)
        writer = PdfWriter()
        for idx in page_order:
            writer.add_page(reader.pages[idx])
        with open(out, "wb") as f:
            writer.write(f)
        self.log(f"[REORDER] → {out}")

    def rotate_pdf_pages(self, path, out, angle, pages=None, job=None):
        self.log(f"[ROTATE] {angle}°")
        reader = PdfReader(path)
        writer = PdfWriter()
        for i, page in enumerate(reader.pages):
            if pages is None or i in pages:
                page.rotate(angle)
            writer.add_page(page)
        with open(out, "wb") as f:
            writer.write(f)
        self.log(f"[ROTATE] → {out}")

    def extract_pdf_metadata(self, path):
        reader = PdfReader(path)
        meta = reader.metadata or {}
        return {
            "pages": len(reader.pages),
            "title": meta.get("/Title", ""),
            "author": meta.get("/Author", ""),
            "subject": meta.get("/Subject", ""),
            "creator": meta.get("/Creator", ""),
            "producer": meta.get("/Producer", ""),
            "size": os.path.getsize(path),
        }

    def extract_pdf_text(self, path):
        doc = fitz.open(path)
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()

    # ==================== CONVERSION SUITE ====================
    def convert(self, src, dst_fmt):
        se = os.path.splitext(src)[1].lstrip(".").lower()
        de = dst_fmt.lower().lstrip(".")
        out = os.path.splitext(src)[0] + f".{de}"
        self.log(f"[CONV] {se.upper()} → {de.upper()}")

        _IMG_R = {"png","jpg","jpeg","webp","bmp","tiff","gif"}
        _IMG_W = {"png","jpg","jpeg","webp","bmp","tiff","pdf"}
        _DATA = {"csv","xlsx","json","html","xml","tsv"}
        _MEDIA = {"mp4","mkv","avi","mov","mp3","wav","flac","ogg","webm"}
        _DOC = {"md","txt","epub","html","pdf","rst","latex"}

        # Image
        if se in _IMG_R and de in _IMG_W:
            img = Image.open(src)
            if img.mode in ("RGBA","P") and de in ("jpg","jpeg"):
                img = img.convert("RGB")
            elif img.mode == "P":
                img = img.convert("RGBA")
            img.save(out) if de != "pdf" else img.save(out, "PDF", resolution=100)
            self.log(f"[CONV] Image → {out}")
            return out

        # Office → PDF
        if se in ("docx","pptx","xlsx") and de == "pdf":
            od = os.path.dirname(src)
            if sys.platform == "win32" and self.dep.check("comtypes"):
                self._office_to_pdf_comtypes(src, se)
            else:
                self._office_to_pdf_libreoffice(src, od)
            pdf = os.path.join(od, os.path.splitext(os.path.basename(src))[0] + ".pdf")
            self.log(f"[CONV] Office → PDF")
            return pdf

        # PDF → DOCX
        if se == "pdf" and de == "docx":
            cv = PDF2DocxConverter(src)
            try:
                cv.convert(out, start=0, end=None)
            finally:
                cv.close()
            self.log(f"[CONV] PDF → DOCX: {out}")
            return out

        # Data transforms
        if se in _DATA and de in _DATA:
            readers = {
                "xlsx": pd.read_excel, "json": pd.read_json,
                "html": lambda p: pd.read_html(p)[0],
                "tsv": lambda p: pd.read_csv(p, sep="\t"),
                "xml": lambda p: pd.read_xml(p),
            }
            writers = {
                "xlsx": lambda df, p: df.to_excel(p, index=False),
                "csv": lambda df, p: df.to_csv(p, index=False),
                "json": lambda df, p: df.to_json(p, orient="records", indent=2),
                "html": lambda df, p: df.to_html(p, index=False),
                "tsv": lambda df, p: df.to_csv(p, sep="\t", index=False),
                "xml": lambda df, p: df.to_xml(p, index=False),
            }
            reader = readers.get(se, pd.read_csv)
            writer = writers[de]
            try:
                df = reader(src)
                writer(df, out)
            except Exception as ex:
                raise RuntimeError(f"Data transform {se}→{de}: {ex}")
            self.log(f"[CONV] Data: {out}")
            return out

        # Media via FFmpeg
        if se in _MEDIA and de in _MEDIA:
            ffmpeg = get_bin_path("ffmpeg")
            if not shutil.which(ffmpeg) and not os.path.exists(ffmpeg):
                raise RuntimeError("FFmpeg not found. Drop ffmpeg.exe in bin/ or add to PATH.")
            subprocess.run([ffmpeg, "-y", "-i", src, out], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log(f"[CONV] Media: {out}")
            return out

        # Document via Pandoc
        if se in _DOC or de in _DOC:
            pandoc = get_bin_path("pandoc")
            if not shutil.which(pandoc) and not os.path.exists(pandoc):
                raise RuntimeError("Pandoc not found. Drop pandoc.exe in bin/ or add to PATH.")
            subprocess.run([pandoc, src, "-o", out], check=True)
            self.log(f"[CONV] Document: {out}")
            return out

        # PDF → Images
        if se == "pdf" and de in _IMG_W:
            doc = fitz.open(src)
            try:
                for i, page in enumerate(doc):
                    pix = page.get_pixmap(dpi=200)
                    pix.save(os.path.splitext(src)[0] + f"_p{i+1:03d}.{de}")
            finally:
                doc.close()
            self.log(f"[CONV] PDF → {de.upper()} frames")
            return os.path.splitext(src)[0] + f"_p001.{de}"

        raise NotImplementedError(f"Route {se}→{de} not supported")

    def _office_to_pdf_comtypes(self, path, ext):
        import comtypes.client
        apps = {"docx": "Word.Application", "pptx": "Powerpoint.Application", "xlsx": "Excel.Application"}
        fmts = {"docx": 17, "pptx": 32}
        try:
            app = comtypes.client.CreateObject(apps[ext])
            if ext == "docx":
                doc = app.Documents.Open(path)
                doc.SaveAs(os.path.splitext(path)[0] + ".pdf", FileFormat=17)
                doc.Close()
            elif ext == "pptx":
                pres = app.Presentations.Open(path, WithWindow=False)
                pres.SaveAs(os.path.splitext(path)[0] + ".pdf", FileFormat=32)
                pres.Close()
            elif ext == "xlsx":
                wb = app.Workbooks.Open(path)
                wb.ExportAsFixedFormat(0, os.path.splitext(path)[0] + ".pdf")
                wb.Close()
            app.Quit()
        except Exception as ex:
            raise RuntimeError(f"MS Office automation failed: {ex}")

    def _office_to_pdf_libreoffice(self, path, out_dir):
        lo = shutil.which("libreoffice") or shutil.which("soffice")
        if not lo:
            raise RuntimeError("LibreOffice not found. Install or add to PATH.")
        result = subprocess.run(
            [lo, "--headless", "--convert-to", "pdf", path, "--outdir", out_dir],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice: {result.stderr.strip()}")

    # ==================== ANALYSIS SUITE ====================
    def ocr_image(self, path):
        reader = self._get_ocr()
        self.log("[OCR] Processing...")
        results = reader.readtext(path, paragraph=True)
        return "\n".join(r[1] for r in results)

    def ocr_pdf(self, path, job=None):
        reader = self._get_ocr()
        doc = fitz.open(path)
        total, full = len(doc), []
        try:
            import numpy as np
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                arr = np.array(img)
                results = reader.readtext(arr, paragraph=True)
                full.append(f"--- Page {i+1} ---\n" + "\n".join(r[1] for r in results))
                self._progress(job, (i+1)/total, f"OCR page {i+1}/{total}")
                self.log(f"[OCR] Page {i+1}/{total} complete")
        finally:
            doc.close()
        return "\n\n".join(full)

    def _get_ocr(self):
        if self._ocr_reader is None:
            with self._ocr_lock:
                if self._ocr_reader is None:
                    self.dep.ensure("easyocr")
                    import easyocr
                    self.log("[OCR] Loading model (~1.5GB download first run)...")
                    self._ocr_reader = easyocr.Reader(["en"], gpu=False)
                    self.log("[OCR] Ready.")
        return self._ocr_reader

    def summarize(self, text, method="luhn", sentences=5):
        if not self.dep.ensure("sumy"):
            raise RuntimeError("Install sumy: pip install sumy")
        self._ensure_nltk()
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.luhn import LuhnSummarizer
        from sumy.summarizers.lsa import LsaSummarizer
        from sumy.summarizers.kl import KLSummarizer
        from sumy.summarizers.text_rank import TextRankSummarizer

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        algos = {
            "luhn": LuhnSummarizer, "lsa": LsaSummarizer,
            "kl": KLSummarizer, "textrank": TextRankSummarizer,
        }
        algo = algos.get(method, LuhnSummarizer)()
        summary = algo(parser.document, sentences)
        return " ".join(str(s) for s in summary)

    def _ensure_nltk(self):
        with self._nltk_lock:
            if self._nltk_ready: return
            try:
                import nltk
                for pkg in ("punkt_tab", "punkt"):
                    try:
                        nltk.data.find(f"tokenizers/{pkg}")
                        self._nltk_ready = True
                        return
                    except LookupError:
                        try:
                            nltk.download(pkg, quiet=True)
                            self._nltk_ready = True
                            return
                        except Exception:
                            continue
                self._nltk_ready = True
            except Exception:
                pass

    def extract_keywords(self, text, top_n=10):
        """Simple TF-based keyword extraction (no external deps)."""
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        stopwords = {"the","and","for","are","but","not","you","all","can","had",
                     "her","was","one","our","out","has","have","been","some","them",
                     "than","its","over","such","that","with","from","this","they",
                     "will","what","when","which","their","there","would","about",
                     "into","could","other","after","also","more","these","very"}
        freq = defaultdict(int)
        for w in words:
            if w not in stopwords:
                freq[w] += 1
        return sorted(freq.items(), key=lambda x: -x[1])[:top_n]

# =====================================================================
# FILE DROP ZONE (Drag & Drop)
# =====================================================================
class DropZone(ctk.CTkFrame):
    def __init__(self, parent, on_drop, **kw):
        super().__init__(parent, corner_radius=0, **kw)
        self.on_drop = on_drop
        self.configure(height=100)
        self.pack_propagate(False)
        ctk.CTkLabel(
            self, text="[ DROP FILES HERE ]",
            font=ctk.CTkFont(family=TT.MONO, size=13),
            text_color=TT.TEXT_DIM
        ).place(relx=0.5, rely=0.5, anchor="center")

        # tkinterdnd2 integration
        self._dnd = None
        try:
            from tkinterdnd2 import DND_FILES
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_dnd)
            self._dnd = True
        except Exception:
            self._dnd = False

        # Fallback: click-to-browse label
        self.bind("<Button-1>", lambda e: self._browse())
        self.configure(cursor="hand2")

    def _on_dnd(self, event):
        raw = event.data
        files = []
        for f in self._parse_dnd(raw):
            if os.path.isdir(f):
                for root, _, filenames in os.walk(f):
                    for fn in filenames:
                        files.append(os.path.join(root, fn))
            else:
                files.append(f)
        if files and self.on_drop:
            self.on_drop(files)

    def _parse_dnd(self, raw):
        items = []
        for part in raw.split():
            part = part.strip("{}")
            if os.path.exists(part):
                items.append(part)
        return items

    def _browse(self):
        files = filedialog.askopenfilenames(title="[ SELECT FILES ]")
        if files and self.on_drop:
            self.on_drop(list(files))

# =====================================================================
# THREAD-SAFE LOG QUEUE
# =====================================================================
class LogHandler:
    def __init__(self, widget):
        self._q = queue.Queue()
        self._w = widget
        self._active = True
        self._poll()

    def emit(self, msg):
        self._q.put(str(msg))

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                self._w.configure(state="normal")
                self._w.insert("end", f">> {msg}\n")
                self._w.see("end")
                self._w.configure(state="disabled")
        except queue.Empty:
            pass
        if self._active:
            self._w.after(100, self._poll)

    def stop(self):
        self._active = False

# =====================================================================
# MAIN APPLICATION
# =====================================================================
class OmniWorkspaceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OMNI WORKSPACE // v2.0")
        self.geometry("1200x760")
        self.minsize(1000, 680)

        self.depman = DependencyManager(self._log_line)
        self.jobs = JobController()
        self.jobs.on_change(self._refresh_job_indicator)
        self.engine = OmniCoreEngine(self._log_line, self.depman)

        self._build_layout()
        self._init_keyboard()
        self._log("OmniWorkspace v2.0 // Tactical Telemetry Interface")
        self._log("Drop files anywhere, or use [MOUNT] buttons.")

        # Core dep check async
        threading.Thread(target=self._check_deps, daemon=True).start()

    def _check_deps(self):
        for m in _CORE_REQUIRED:
            if not self.depman.check(m):
                self._log(f"[DEPS] Core package '{m}' missing — install on demand.")

    def _log_line(self, msg):
        if hasattr(self, "_log_handler"):
            self._log_handler.emit(msg)

    log = _log_line

    # ============ LAYOUT ============
    def _build_layout(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=TT.BG_SURFACE)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color=TT.BG_ROOT)
        self.main.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._build_terminal()
        self._build_main()

    def _build_sidebar(self):
        ctk.CTkLabel(self.sidebar, text="[ OMNI WORKSPACE ]",
                     font=ctk.CTkFont(family=TT.MONO, size=13, weight="bold"),
                     text_color=TT.RED).pack(pady=(20, 2), padx=20, anchor="w")
        ctk.CTkLabel(self.sidebar, text="Universal Document Suite v2",
                     font=ctk.CTkFont(family=TT.MONO, size=9),
                     text_color=TT.TEXT_DIM).pack(pady=(0, 20), padx=20, anchor="w")

        self._job_indicator = ctk.CTkLabel(
            self.sidebar, text="[IDLE]",
            font=ctk.CTkFont(family=TT.MONO, size=10),
            text_color=TT.TEXT_MUTED, anchor="w"
        )
        self._job_indicator.pack(pady=(0, 10), padx=20, anchor="w")

        panels = [
            ("[ ORGANIZE ]", "Merge / Split / Reorder / Rotate"),
            ("[ OPTIMIZE ]", "Compress / Watermark / Metadata"),
            ("[ CONVERT  ]", "Omni-Format Routing"),
            ("[ SECURITY ]", "Redact / Encrypt"),
            ("[ ANALYZE  ]", "OCR / Summarize / Keywords"),
            ("[ BATCH    ]", "Folder Processing"),
            ("[ HISTORY  ]", "Job Log"),
            ("[ SETTINGS ]", "Workers / Theme"),
        ]
        for title, hint in panels:
            f = ctk.CTkFrame(self.sidebar, corner_radius=0, fg_color="transparent")
            f.pack(fill="x", padx=0, pady=0)
            btn = ctk.CTkButton(
                f, text=title, anchor="w",
                fg_color="transparent", hover_color=TT.HOVER,
                text_color=TT.TEXT, height=36,
                corner_radius=0, border_width=0,
                font=ctk.CTkFont(family=TT.MONO, size=11),
                command=lambda t=title: self._show_panel(t)
            )
            btn.pack(fill="x", padx=12, pady=1)
            ctk.CTkLabel(f, text=hint, anchor="w",
                         font=ctk.CTkFont(family=TT.MONO, size=8),
                         text_color=TT.TEXT_MUTED
            ).pack(pady=(0, 4), padx=24, anchor="w")

    def _build_terminal(self):
        self.term_frame = ctk.CTkFrame(self.sidebar, height=180, corner_radius=0,
                                        fg_color=TT.BG_ROOT, border_width=1, border_color=TT.BORDER)
        self.term_frame.pack(side="bottom", fill="x", padx=0, pady=0)
        self.term_frame.pack_propagate(False)

        hdr = ctk.CTkFrame(self.term_frame, height=22, fg_color=TT.BG_ELEVATED, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="SYSTEM LOG // TTY",
                     font=ctk.CTkFont(family=TT.MONO, size=9),
                     text_color=TT.TEXT_DIM).pack(side="left", padx=8, pady=2)

        self._term = ctk.CTkTextbox(self.term_frame,
            font=ctk.CTkFont(family=TT.MONO, size=10),
            fg_color=TT.BG_ROOT, text_color=TT.TEXT, state="disabled",
            corner_radius=0, border_width=0)
        self._term.pack(fill="both", expand=True, padx=0, pady=0)
        self._log_handler = LogHandler(self._term)

    def _build_main(self):
        self._panel_frame = ctk.CTkScrollableFrame(self.main, corner_radius=0, fg_color=TT.BG_ROOT)
        self._panel_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self._drop_bar = ctk.CTkFrame(self.main, height=60, corner_radius=0,
                                       fg_color=TT.BG_SURFACE, border_width=1, border_color=TT.BORDER)
        self._drop_bar.pack(side="bottom", fill="x")
        self._drop_bar.pack_propagate(False)
        self._add_drop_bar()

    def _add_drop_bar(self):
        inner = ctk.CTkFrame(self._drop_bar, corner_radius=0, fg_color="transparent")
        inner.pack(fill="x", padx=15, pady=8)
        self._drop_zone = DropZone(inner, self._on_files_dropped,
                                    fg_color="transparent", border_width=0)
        self._drop_zone.pack(fill="x", expand=True)

    def _on_files_dropped(self, files):
        with self._file_lock:
            self._pipeline = files
        self._pipeline_label.configure(
            text=f"[ MOUNTED ] // {len(files)} files",
            text_color=TT.GREEN
        )
        self._log(f"[MOUNT] {len(files)} files staged")

    # ============ KEYBOARD ============
    def _init_keyboard(self):
        self.bind("<Control-o>", lambda e: self._stage_files(False))
        self.bind("<Control-O>", lambda e: self._stage_files(False))
        self.bind("<Control-Shift-O>", lambda e: self._stage_files(True))
        self.bind("<Control-q>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.jobs.cancel_all())

    # ============ PANEL SWITCHING ============
    def _show_panel(self, title):
        for w in self._panel_frame.winfo_children():
            w.destroy()
        key = title.strip("[]").replace(" ", "_").replace("/", "_")
        with self._file_lock:
            self._pipeline = []

        body = self._panel_frame

        ctk.CTkLabel(body, text=f">> {title.strip('[]')} //",
                     font=ctk.CTkFont(family=TT.MONO, size=14, weight="bold"),
                     text_color=TT.TEXT).pack(pady=(20, 2), padx=25, anchor="w")

        self._pipeline_label = ctk.CTkLabel(
            body, text="[ AWAITING INPUT ]",
            font=ctk.CTkFont(family=TT.MONO, size=10),
            text_color=TT.TEXT_MUTED, anchor="w"
        )
        self._pipeline_label.pack(pady=(0, 10), padx=25, anchor="w", fill="x")

        self._progress_bar = ctk.CTkProgressBar(body, corner_radius=0, height=3,
                                                  fg_color=TT.BG_ELEVATED, progress_color=TT.RED)
        self._progress_bar.pack(fill="x", padx=25, pady=(0, 10))
        self._progress_bar.set(0)
        self._progress_label = ctk.CTkLabel(
            body, text="", font=ctk.CTkFont(family=TT.MONO, size=9), text_color=TT.RED)
        self._progress_label.pack(pady=(0, 5), padx=25, anchor="w")

        sep = ctk.CTkFrame(body, height=1, fg_color=TT.BORDER, corner_radius=0)
        sep.pack(fill="x", padx=25, pady=(0, 10))

        actions = ctk.CTkFrame(body, corner_radius=0, fg_color="transparent")
        actions.pack(fill="x", padx=25, pady=(0, 10))

        fn = getattr(self, f"_panel_{key}", None)
        if fn:
            fn(actions, body)
        else:
            ctk.CTkLabel(body, text="[ PANEL NOT IMPLEMENTED ]",
                         font=ctk.CTkFont(family=TT.MONO, size=11),
                         text_color=TT.RED).pack(pady=20, padx=25, anchor="w")

    # ============ PANELS ============
    # -- shared helpers --
    _pipeline = []
    _file_lock = threading.Lock()

    def _stage_files(self, multi=True):
        files = filedialog.askopenfilenames() if multi else [filedialog.askopenfilename()]
        files = [f for f in files if f]
        if not files: return
        with self._file_lock:
            self._pipeline = files
        self._pipeline_label.configure(text=f"[ MOUNTED ] // {len(files)} files", text_color=TT.GREEN)
        self._log(f"[MOUNT] {len(files)} file(s) staged")

    def _stage_dir(self):
        d = filedialog.askdirectory()
        if not d: return
        with self._file_lock:
            self._pipeline = [d]
        self._pipeline_label.configure(text=f"[ MOUNTED ] // DIRECTORY: {os.path.basename(d)}", text_color=TT.GREEN)
        self._log(f"[MOUNT] Directory: {d}")

    def _btn(self, parent, text, cmd, fg=TT.BG_ELEVATED):
        btn = ctk.CTkButton(parent, text=text, command=cmd,
            fg_color=fg, hover_color=TT.HOVER, text_color=TT.TEXT,
            font=ctk.CTkFont(family=TT.MONO, size=11),
            corner_radius=0, border_width=1, border_color=TT.BORDER, height=30)
        btn.pack(pady=3, anchor="w")
        return btn

    def _add_textbox(self, parent):
        tb = ctk.CTkTextbox(parent, wrap="word", fg_color=TT.BG_INPUT,
                             font=ctk.CTkFont(family=TT.MONO, size=11),
                             corner_radius=0, border_width=1, border_color=TT.BORDER)
        tb.pack(fill="both", expand=True, padx=25, pady=(10, 25))
        return tb

    def _submit_job(self, name, fn, args=None, kwargs=None):
        self.jobs.submit(name, fn, args, kwargs)

    def _refresh_job_indicator(self):
        n = self.jobs.active_count
        if n:
            self._job_indicator.configure(text=f"[ ACTIVE ] // {n} job(s) running", text_color=TT.AMBER)
        else:
            self._job_indicator.configure(text="[ IDLE ]", text_color=TT.TEXT_MUTED)

    def _progress_cb(self, job):
        def cb(v, t=""):
            if job:
                self._progress_bar.set(v)
                self._progress_label.configure(text=t)
            self._refresh_job_indicator()
        return cb

    # -- Panel: ORGANIZE --
    def _panel_ORGANIZE(self, actions, body):
        self._btn(actions, "[ MOUNT FILES ]", lambda: self._stage_files(True))
        self._btn(actions, "[ EXECUTE: MERGE ]", self._run_merge, TT.RED)
        self._btn(actions, "[ EXECUTE: SPLIT ]", self._run_split, TT.RED)
        self._btn(actions, "[ EXECUTE: REORDER ]", self._run_reorder)
        self._btn(actions, "[ EXECUTE: ROTATE 90° ]", self._run_rotate)

    def _run_merge(self):
        with self._file_lock:
            files = list(self._pipeline)
        if len(files) < 2:
            messagebox.showerror("Error", "Mount at least 2 PDFs.")
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not out: return
        def task():
            self.engine.merge_pdfs(files, out)
            self._log(f"[DONE] Merged {len(files)} files → {out}")
        self._submit_job("Merge PDFs", task)

    def _run_split(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a PDF.")
            return
        d = filedialog.askdirectory(title="[ OUTPUT DIRECTORY ]")
        if not d: return
        def task():
            self.engine.split_pdf(files[0], d)
            self._log(f"[DONE] Split → {d}")
        self._submit_job("Split PDF", task, [files[0], d])

    def _run_reorder(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a PDF.")
            return
        import tkinter.simpledialog as sd
        order = sd.askstring("Page Order", "Enter page order (0-based, comma-sep):\ne.g. 3,2,1,0", parent=self)
        if not order: return
        try:
            indices = [int(x.strip()) for x in order.split(",")]
        except ValueError:
            messagebox.showerror("Error", "Invalid page numbers.")
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not out: return
        def task():
            self.engine.reorder_pdf_pages(files[0], out, indices)
            self._log(f"[DONE] Reordered → {out}")
        self._submit_job("Reorder PDF", task)

    def _run_rotate(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a PDF.")
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not out: return
        def task():
            self.engine.rotate_pdf_pages(files[0], out, 90)
            self._log(f"[DONE] Rotated → {out}")
        self._submit_job("Rotate PDF", task)

    # -- Panel: OPTIMIZE --
    def _panel_OPTIMIZE(self, actions, body):
        self._btn(actions, "[ MOUNT FILE ]", lambda: self._stage_files(False))
        self._btn(actions, "[ COMPRESS ]", self._run_compress, TT.RED)
        self._btn(actions, "[ ADD WATERMARK ]", self._run_watermark)
        self._btn(actions, "[ VIEW METADATA ]", self._run_metadata)

    def _run_compress(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a PDF.")
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not out: return
        def task():
            self.engine.compress_pdf(files[0], out)
            self._log(f"[DONE] Compressed → {out}")
        self._submit_job("Compress PDF", task)

    def _run_watermark(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a PDF.")
            return
        import tkinter.simpledialog as sd
        text = sd.askstring("Watermark", "Watermark text:", parent=self)
        if not text: return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not out: return
        def task():
            self.engine.watermark_pdf(files[0], out, text)
            self._log(f"[DONE] Watermarked → {out}")
        self._submit_job("Watermark PDF", task)

    def _run_metadata(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a PDF.")
            return
        meta = self.engine.extract_pdf_metadata(files[0])
        info = "\n".join(f"{k}: {v}" for k, v in meta.items())
        self._add_textbox(self._panel_frame)
        # find last textbox
        for w in self._panel_frame.winfo_children():
            if isinstance(w, ctk.CTkTextbox):
                w.delete("1.0", "end")
                w.insert("1.0", info)
                break

    # -- Panel: CONVERT --
    def _panel_CONVERT(self, actions, body):
        self._btn(actions, "[ MOUNT SOURCE ]", lambda: self._stage_files(False))

        ctk.CTkLabel(actions, text="TARGET FORMAT:",
                     font=ctk.CTkFont(family=TT.MONO, size=10),
                     text_color=TT.TEXT_DIM).pack(pady=(8, 2), anchor="w")
        self._combo_fmt = ctk.CTkComboBox(actions,
            values=["pdf","docx","xlsx","csv","json","html","png","jpg","mp3",
                     "mp4","md","epub","webp","tiff","xml","tsv"],
            width=240, corner_radius=0,
            font=ctk.CTkFont(family=TT.MONO, size=11),
            dropdown_font=ctk.CTkFont(family=TT.MONO, size=10))
        self._combo_fmt.pack(pady=(0, 8), anchor="w")

        self._btn(actions, "[ EXECUTE: CONVERT ]", self._run_convert, TT.RED)

    def _run_convert(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a source file.")
            return
        fmt = self._combo_fmt.get()
        if not fmt: return
        def task():
            result = self.engine.convert(files[0], fmt)
            self._log(f"[DONE] → {os.path.basename(result)}")
        self._submit_job(f"Convert to {fmt}", task, [files[0], fmt])

    # -- Panel: SECURITY --
    def _panel_SECURITY(self, actions, body):
        self._btn(actions, "[ MOUNT FILE ]", lambda: self._stage_files(False))

        ctk.CTkLabel(actions, text="PASSPHRASE:",
                     font=ctk.CTkFont(family=TT.MONO, size=10),
                     text_color=TT.TEXT_DIM).pack(pady=(8, 2), anchor="w")
        self._entry_pw = ctk.CTkEntry(actions, show="*", width=320,
            placeholder_text="[ ENCRYPTION KEY ]",
            font=ctk.CTkFont(family=TT.MONO, size=11), corner_radius=0)
        self._entry_pw.pack(pady=(0, 8), anchor="w")
        self._btn(actions, "[ ENCRYPT ]", self._run_encrypt, TT.RED)

        ctk.CTkLabel(actions, text="REDACTION PHRASE:",
                     font=ctk.CTkFont(family=TT.MONO, size=10),
                     text_color=TT.TEXT_DIM).pack(pady=(12, 2), anchor="w")
        self._entry_redact = ctk.CTkEntry(actions, width=320,
            placeholder_text="[ TARGET STRING ]",
            font=ctk.CTkFont(family=TT.MONO, size=11), corner_radius=0)
        self._entry_redact.pack(pady=(0, 8), anchor="w")
        self._btn(actions, "[ REDACT ]", self._run_redact)

    def _run_encrypt(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a file.")
            return
        pw = self._entry_pw.get()
        if not pw:
            messagebox.showerror("Error", "Enter a passphrase.")
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not out: return
        def task():
            self.engine.encrypt_pdf(files[0], out, pw)
            self._log(f"[DONE] Encrypted → {out}")
        self._submit_job("Encrypt PDF", task, [files[0], out, pw])

    def _run_redact(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a file.")
            return
        s = self._entry_redact.get()
        if not s:
            messagebox.showerror("Error", "Enter target phrase.")
            return
        out = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF","*.pdf")])
        if not out: return
        def task():
            self.engine.redact_text(files[0], out, s)
            self._log(f"[DONE] Redacted → {out}")
        self._submit_job("Redact PDF", task, [files[0], out, s])

    # -- Panel: ANALYZE --
    def _panel_ANALYZE(self, actions, body):
        self._btn(actions, "[ MOUNT PDF / IMAGE ]", lambda: self._stage_files(False))

        ctk.CTkLabel(actions, text="SUMMARY METHOD:",
                     font=ctk.CTkFont(family=TT.MONO, size=10),
                     text_color=TT.TEXT_DIM).pack(pady=(8, 2), anchor="w")
        self._combo_summary = ctk.CTkComboBox(actions,
            values=["luhn", "lsa", "kl", "textrank"],
            width=200, corner_radius=0,
            font=ctk.CTkFont(family=TT.MONO, size=11),
            dropdown_font=ctk.CTkFont(family=TT.MONO, size=10))
        self._combo_summary.pack(pady=(0, 8), anchor="w")
        self._combo_summary.set("luhn")

        self._btn(actions, "[ RUN OCR ]", self._run_ocr, TT.RED)
        self._btn(actions, "[ SUMMARIZE ]", self._run_summarize)
        self._btn(actions, "[ EXTRACT KEYWORDS ]", self._run_keywords)

        self._txt_out = self._add_textbox(body)

    def _run_ocr(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a PDF or image.")
            return
        def task():
            ext = os.path.splitext(files[0])[1].lower()
            if ext in (".png",".jpg",".jpeg",".webp",".bmp",".tiff"):
                text = self.engine.ocr_image(files[0])
            else:
                text = self.engine.ocr_pdf(files[0])
            self._txt_out.delete("1.0", "end")
            self._txt_out.insert("1.0", text or "[No text detected]")
            self._log(f"[DONE] OCR complete ({len(text or '')} chars)")
        self._submit_job("OCR", task, [files[0]])

    def _run_summarize(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a file.")
            return
        method = getattr(self, "_combo_summary", None)
        m = method.get() if method else "luhn"
        def task():
            text = self.engine.extract_pdf_text(files[0])
            if not text.strip():
                self._log("[WARN] No text found. Try OCR first.")
                return
            summary = self.engine.summarize(text, method=m)
            self._txt_out.delete("1.0", "end")
            self._txt_out.insert("1.0", summary)
            self._log(f"[DONE] Summary ({m}) complete")
        self._submit_job(f"Summarize ({m})", task, [files[0], m])

    def _run_keywords(self):
        with self._file_lock:
            files = list(self._pipeline)
        if not files:
            messagebox.showerror("Error", "Mount a file.")
            return
        def task():
            text = self.engine.extract_pdf_text(files[0])
            kw = self.engine.extract_keywords(text)
            lines = "\n".join(f"  {w:20s} {n:5d}" for w, n in kw)
            self._txt_out.delete("1.0", "end")
            self._txt_out.insert("1.0", f"Keywords (TF):\n\n{lines}")
            self._log(f"[DONE] Keywords extracted")
        self._submit_job("Keywords", task, [files[0]])

    # -- Panel: BATCH --
    def _panel_BATCH(self, actions, body):
        self._btn(actions, "[ MOUNT DIRECTORY ]", self._stage_dir)
        ctk.CTkLabel(actions, text="PATTERN (glob, e.g. *.pdf):",
                     font=ctk.CTkFont(family=TT.MONO, size=10),
                     text_color=TT.TEXT_DIM).pack(pady=(8, 2), anchor="w")
        self._entry_glob = ctk.CTkEntry(actions, width=240,
            placeholder_text="*.pdf",
            font=ctk.CTkFont(family=TT.MONO, size=11), corner_radius=0)
        self._entry_glob.pack(pady=(0, 8), anchor="w")

        ctk.CTkLabel(actions, text="ACTION:",
                     font=ctk.CTkFont(family=TT.MONO, size=10),
                     text_color=TT.TEXT_DIM).pack(pady=(8, 2), anchor="w")
        self._combo_batch = ctk.CTkComboBox(actions,
            values=["compress", "split", "to_docx", "to_txt", "ocr", "summarize"],
            width=240, corner_radius=0,
            font=ctk.CTkFont(family=TT.MONO, size=11),
            dropdown_font=ctk.CTkFont(family=TT.MONO, size=10))
        self._combo_batch.pack(pady=(0, 8), anchor="w")
        self._combo_batch.set("compress")

        out_f = ctk.CTkFrame(actions, corner_radius=0, fg_color="transparent")
        out_f.pack(fill="x", pady=5)
        self._btn(out_f, "[ SET OUTPUT DIR ]", self._set_batch_out)
        self._batch_out = ""
        self._batch_out_label = ctk.CTkLabel(out_f,
            text="[ OUTPUT: source dir ]", font=ctk.CTkFont(family=TT.MONO, size=9), text_color=TT.TEXT_MUTED)
        self._batch_out_label.pack(pady=2, anchor="w")

        self._btn(actions, "[ EXECUTE BATCH ]", self._run_batch, TT.RED)

        self._batch_progress = ctk.CTkTextbox(body, wrap="word",
            fg_color=TT.BG_INPUT, font=ctk.CTkFont(family=TT.MONO, size=10),
            corner_radius=0, border_width=1, border_color=TT.BORDER, height=200)
        self._batch_progress.pack(fill="x", padx=25, pady=(10, 25))

    def _set_batch_out(self):
        d = filedialog.askdirectory(title="[ BATCH OUTPUT ]")
        if d:
            self._batch_out = d
            self._batch_out_label.configure(text=f"[ OUTPUT: {d} ]")

    def _run_batch(self):
        with self._file_lock:
            items = list(self._pipeline)
        if not items or not os.path.isdir(items[0]):
            messagebox.showerror("Error", "Mount a directory first.")
            return
        pattern = self._entry_glob.get() or "*.pdf"
        action = self._combo_batch.get()
        src_dir = items[0]
        out_dir = self._batch_out or src_dir

        files = sorted(Path(src_dir).glob(pattern))
        if not files:
            messagebox.showerror("Error", f"No files match '{pattern}' in {src_dir}")
            return

        self._log(f"[BATCH] {action} on {len(files)} files [{pattern}]")
        self._batch_progress.delete("1.0", "end")

        def task():
            for i, f in enumerate(files):
                f = str(f)
                self._batch_progress.insert("end", f"[{i+1}/{len(files)}] {os.path.basename(f)}...\n")
                self._batch_progress.see("end")
                try:
                    if action == "compress":
                        out = os.path.join(out_dir, f"compressed_{os.path.basename(f)}")
                        self.engine.compress_pdf(f, out)
                    elif action == "split":
                        self.engine.split_pdf(f, out_dir)
                    elif action == "to_docx":
                        self.engine.convert(f, "docx")
                    elif action == "to_txt":
                        text = self.engine.extract_pdf_text(f)
                        with open(os.path.join(out_dir, Path(f).stem + ".txt"), "w") as wf:
                            wf.write(text)
                    elif action == "ocr":
                        text = self.engine.ocr_pdf(f)
                        with open(os.path.join(out_dir, Path(f).stem + "_ocr.txt"), "w") as wf:
                            wf.write(text)
                    elif action == "summarize":
                        text = self.engine.extract_pdf_text(f)
                        summary = self.engine.summarize(text)
                        with open(os.path.join(out_dir, Path(f).stem + "_summary.txt"), "w") as wf:
                            wf.write(summary)
                    self._batch_progress.insert("end", f"  ✓ {os.path.basename(f)}\n")
                except Exception as ex:
                    self._batch_progress.insert("end", f"  ✗ {ex}\n")
                self._batch_progress.see("end")
            self._batch_progress.insert("end", f"\n[BATCH DONE] {len(files)} files processed.\n")
            self._log(f"[BATCH] Completed {action} on {len(files)} files")

        self._submit_job(f"Batch {action}", task)

    # -- Panel: HISTORY --
    def _panel_HISTORY(self, actions, body):
        self._btn(actions, "[ REFRESH ]", lambda: self._refresh_history(body))
        self._history_body = body
        self._refresh_history(body)

    def _refresh_history(self, body):
        for w in body.winfo_children():
            if isinstance(w, ctk.CTkTextbox) or w == body.winfo_children()[0]:
                continue
        recent = self.jobs.recent(20)
        tb = ctk.CTkTextbox(body, wrap="word",
            fg_color=TT.BG_INPUT, font=ctk.CTkFont(family=TT.MONO, size=10),
            corner_radius=0, border_width=1, border_color=TT.BORDER)
        tb.pack(fill="both", expand=True, padx=25, pady=(10, 25))

        status_map = ["PENDING", "RUNNING", "DONE", "FAILED", "CANCELLED"]
        for j in reversed(recent):
            s = status_map[j.status] if j.status < len(status_map) else "UNKNOWN"
            elapsed = f"{j.elapsed():.1f}s" if j.elapsed() else ""
            tb.insert("end", f"[{s:8s}] #{j.id:03d}  {j.name:30s}  {elapsed}\n")
        tb.configure(state="disabled")

    # -- Panel: SETTINGS --
    def _panel_SETTINGS(self, actions, body):
        sw_f = ctk.CTkFrame(actions, corner_radius=0, fg_color="transparent")
        sw_f.pack(fill="x", pady=5)
        ctk.CTkLabel(sw_f, text="MAX WORKERS:",
                     font=ctk.CTkFont(family=TT.MONO, size=10),
                     text_color=TT.TEXT_DIM).pack(side="left", padx=(0, 10))
        w = ctk.CTkEntry(sw_f, width=60, font=ctk.CTkFont(family=TT.MONO, size=11),
                         corner_radius=0, justify="center")
        w.insert(0, str(self.jobs.max_workers))
        w.pack(side="left")
        ctk.CTkButton(sw_f, text="SET", width=50,
            font=ctk.CTkFont(family=TT.MONO, size=10),
            corner_radius=0, border_width=1, border_color=TT.BORDER,
            command=lambda: self._set_workers(w.get())
        ).pack(side="left", padx=5)

        info = [
            ("Workers", str(self.jobs.max_workers)),
            ("Active Jobs", str(self.jobs.active_count)),
            ("Python", sys.version.split()[0]),
            ("Platform", sys.platform),
            ("PyMuPDF", fitz.version if hasattr(fitz, "version") else "ok"),
            ("pypdf", PdfReader),
        ]
        info_f = ctk.CTkFrame(body, corner_radius=0, fg_color="transparent")
        info_f.pack(fill="x", padx=25, pady=(15, 25))
        for k, v in info:
            ctk.CTkLabel(info_f, text=f"  {k:15s}  {v}",
                         font=ctk.CTkFont(family=TT.MONO, size=10),
                         text_color=TT.TEXT_DIM, anchor="w"
            ).pack(fill="x", pady=1)

    def _set_workers(self, val):
        try:
            n = max(1, min(int(val), 32))
            self.jobs._max = n
            self._log(f"[SETTINGS] Max workers → {n}")
        except ValueError:
            pass

    # ============ CLEANUP ============
    def destroy(self):
        self._log_handler.stop()
        self.jobs.shutdown(wait=False)
        super().destroy()

# =====================================================================
# ENTRY
# =====================================================================
if __name__ == "__main__":
    ctk_init()
    app = OmniWorkspaceApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.destroy()

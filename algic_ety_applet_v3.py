#!/usr/bin/env python3
"""
algic_ety_applet_v3.py — Algic Etymology Applet (Integrated with Kilahkwaani v2)
=============================================================================
"""
from __future__ import annotations
import argparse, json, os, re, secrets, sqlite3, struct, tempfile, uuid, zipfile
from datetime import datetime
from functools import wraps
from io import BytesIO, StringIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from flask import (Flask, Response, g, jsonify, render_template_string,
                   request, send_file, send_from_directory, session)

# ── Expanded Algic Language Registry ─────────────────────────────────────────
ALGIC: Dict[str, Dict] = {
    # --- Plains Algonquian ---
    "bft": {"name": "Blackfoot",           "branch": "Plains",   "script": "roman"},
    "arp": {"name": "Arapaho",             "branch": "Plains",   "script": "roman"},
    "ats": {"name": "Gros Ventre",         "branch": "Plains",   "script": "roman"},
    "chy": {"name": "Cheyenne",            "branch": "Plains",   "script": "roman"},

    # --- Central Algonquian ---
    "men": {"name": "Menominee",           "branch": "Central",  "script": "roman"},
    "cre": {"name": "Plains/Woods Cree",   "branch": "Central",  "script": "syllabics", "priority": True},
    "csw": {"name": "Swampy Cree",         "branch": "Central",  "script": "syllabics"},
    "crj": {"name": "Southern East Cree",  "branch": "Central",  "script": "syllabics"},
    "atj": {"name": "Atikamekw",           "branch": "Central",  "script": "roman"},
    "pot": {"name": "Potawatomi",          "branch": "Central",  "script": "roman",     "priority": True},
    "oji": {"name": "Ojibwe",              "branch": "Central",  "script": "roman"},
    "otw": {"name": "Ottawa",              "branch": "Central",  "script": "roman"},
    "ciw": {"name": "Chippewa",            "branch": "Central",  "script": "roman"},
    "mia": {"name": "Miami-Illinois",      "branch": "Central",  "script": "roman",     "priority": True},
    "sac": {"name": "Meskwaki (Fox)",      "branch": "Central",  "script": "roman",     "priority": True},
    "kic": {"name": "Kickapoo",            "branch": "Central",  "script": "roman",     "priority": True},
    "sjw": {"name": "Shawnee",             "branch": "Central",  "script": "roman"},

    # --- Eastern Algonquian ---
    "mic": {"name": "Mi'kmaq",             "branch": "Eastern",  "script": "roman"},
    "abe": {"name": "Western Abenaki",     "branch": "Eastern",  "script": "roman"},
    "aaq": {"name": "Eastern Abnaki",      "branch": "Eastern",  "script": "roman"},
    "mal": {"name": "Maliseet-Passamaquoddy","branch": "Eastern","script": "roman"},
    "moo": {"name": "Mohegan-Pequot",      "branch": "Eastern",  "script": "roman"},
    "mua": {"name": "Munsee",              "branch": "Eastern",  "script": "roman"},
    "unm": {"name": "Unami",               "branch": "Eastern",  "script": "roman"},

    # --- Ritwan & Western Algic Sister Languages ---
    "yur": {"name": "Yurok",               "branch": "Ritwan",   "script": "roman"},
    "wiy": {"name": "Wiyot",               "branch": "Ritwan",   "script": "roman"},

    # --- Proto-Languages ---
    "alg-x-proto": {"name": "Proto-Algonquian★", "branch": "Proto", "script": "roman"},

    # --- Lost / Unattested / Remnant Languages ---
    "bue": {"name": "Beothuk (Remnant)",   "branch": "Remnant",  "script": "roman",     "remnant": True},
    "etc": {"name": "Etchemin (Remnant)",  "branch": "Remnant",  "script": "roman",     "remnant": True},
    "xlo": {"name": "Loup A (Mots loups)", "branch": "Remnant",  "script": "roman",     "remnant": True},
    "xlb": {"name": "Loup B (Remnant)",    "branch": "Remnant",  "script": "roman",     "remnant": True},
    "crr": {"name": "Lumbee / Pamlico",    "branch": "Remnant",  "script": "roman",     "remnant": True},
    "pim": {"name": "Powhatan (Virginia)", "branch": "Remnant",  "script": "roman",     "remnant": True},
    "qyp": {"name": "Quiripi / Naugatuck", "branch": "Remnant",  "script": "roman",     "remnant": True},
}

OLAC_SCHEMAS = {
    "olac": "http://language-archives.org",
    "dc": "http://purl.org",
}
NS_OAI, NS_DC, NS_OAIDC = "http://openarchives.org", "http://purl.org", "http://openarchives.orgoai_dc"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, role TEXT NOT NULL DEFAULT 'user', api_key TEXT UNIQUE, created TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS entries (id TEXT PRIMARY KEY, lang TEXT NOT NULL, form TEXT NOT NULL, ipa TEXT, pos TEXT, gloss_en TEXT, gloss_fr TEXT, gloss_es TEXT, proto_form TEXT, morph_seg TEXT, source_url TEXT, source_type TEXT, confidence REAL DEFAULT 0.5, media_urls TEXT, created_at TEXT DEFAULT (datetime('now')));
CREATE TABLE IF NOT EXISTS cognate_sets (id TEXT PRIMARY KEY, proto_form TEXT, proto_gloss TEXT, confidence REAL DEFAULT 0.7, source_ref TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS cognate_members (set_id TEXT REFERENCES cognate_sets(id), entry_id TEXT REFERENCES entries(id), PRIMARY KEY (set_id, entry_id));
CREATE TABLE IF NOT EXISTS examples (id TEXT PRIMARY KEY, entry_id TEXT REFERENCES entries(id), sentence TEXT, translation TEXT, lang_trans TEXT DEFAULT 'en', source TEXT);
CREATE TABLE IF NOT EXISTS olac_records (id TEXT PRIMARY KEY, oai_id TEXT, title TEXT, description TEXT, lang TEXT, rights TEXT, source_repo TEXT, raw_xml TEXT, harvested_at TEXT);
CREATE TABLE IF NOT EXISTS import_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now')), username TEXT, action TEXT, source TEXT, records_in INTEGER DEFAULT 0, records_new INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS export_permissions (role TEXT, format TEXT, PRIMARY KEY (role, format));
CREATE INDEX IF NOT EXISTS idx_entries_lang ON entries(lang);
CREATE INDEX IF NOT EXISTS idx_entries_form ON entries(form);
"""

DEFAULT_EXPORT_PERMS = [
    ("admin", "tmx"), ("admin", "xliff"), ("admin", "lift"), ("admin", "eaf"),
    ("admin", "tei"), ("admin", "stardict"), ("admin", "json"), ("admin", "csv"),
    ("admin", "sql"), ("admin", "ollama-jsonl"), ("user", "tmx"), ("user", "json"), ("user", "csv"),
]

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    for role, fmt in DEFAULT_EXPORT_PERMS:
        conn.execute("INSERT OR IGNORE INTO export_permissions VALUES(?,?)", (role, fmt))
    aid, akey = str(uuid.uuid4()), secrets.token_hex(16)
    conn.execute("INSERT OR IGNORE INTO users(id,username,role,api_key) VALUES(?,?,?,?)", (aid, "admin", "admin", akey))
    conn.commit()
    key_row = conn.execute("SELECT api_key FROM users WHERE username='admin'").fetchone()
    conn.close()
    return key_row[0] if key_row else akey

def db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_current_user(db_path: str) -> Optional[Dict]:
    key = request.headers.get("X-API-Key") or request.args.get("api_key") or request.cookies.get("api_key")
    if not key: return None
    row = db(db_path).execute("SELECT * FROM users WHERE api_key=?", (key,)).fetchone()
    return dict(row) if row else None

def require_role(role: str, db_path_ref):
    def dec(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            user = get_current_user(db_path_ref())
            if not user: return jsonify({"error": "Unauthorised"}), 401
            if role == "admin" and user["role"] != "admin": return jsonify({"error": "Admin required"}), 403
            g.user = user
            return fn(*a, **kw)
        return wrapper
    return dec

XSLT_DIRECTIONS = {
    "lift2tmx": ("lift-to-tmx.xsl", "source-lang", None),
    "lift2xliff": ("lift-to-xliff.xsl", "source-lang", "target-lang"),
    "tmx2lift": ("tmx-to-lift.xsl", "source-lang", None),
    "tmx2xliff": ("tmx-to-xliff.xsl", "source-lang", "target-lang"),
}

def saxon_transform(xslt_dir: str, direction: str, xml_bytes: bytes, src_lang: str, tgt_lang: str = "en") -> bytes:
    if direction not in XSLT_DIRECTIONS: raise ValueError(f"Unknown direction: {direction}")
    sheet_file, src_param, tgt_param = XSLT_DIRECTIONS[direction]
    sheet_path = Path(xslt_dir) / sheet_file
    if not sheet_path.exists(): raise FileNotFoundError(f"XSLT sheet not found: {sheet_path}")
    try:
        from saxonche import PySaxonProcessor
        with PySaxonProcessor(license=False) as proc:
            xslt = proc.new_xslt30_processor()
            exe = xslt.compile_stylesheet(stylesheet_file=str(sheet_path))
            exe.set_parameter(src_param, proc.make_string_value(src_lang))
            if tgt_param: exe.set_parameter(tgt_param, proc.make_string_value(tgt_lang))
            with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
                tf.write(xml_bytes); tf_name = tf.name
            result = exe.transform_to_string(source_file=tf_name)
            os.unlink(tf_name)
            return result.encode("utf-8") if isinstance(result, str) else result
    except ImportError:
        return b"<error>SaxonCHE fallback missing</error>"

def db_search(q, langs, db_path):
    conn = db(db_path)
    ph = ",".join("?"*len(langs))
    rows = conn.execute(
        f"SELECT lang,form,ipa,gloss_en,gloss_fr,gloss_es,proto_form,morph_seg,confidence "
        f"FROM entries WHERE (form LIKE ? OR gloss_en LIKE ? or gloss_fr LIKE ? or gloss_es LIKE ?) "
        f"AND lang IN ({ph}) ORDER BY confidence DESC LIMIT 200",
        [f"%{q}%"]*4 + langs).fetchall()
    conn.close(); return [dict(r) for r in rows]

def db_cognates(word, lang, db_path):
    conn = db(db_path); entry = conn.execute("SELECT * FROM entries WHERE lang=? AND form=? LIMIT 1",(lang,word)).fetchone()

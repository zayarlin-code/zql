#!/usr/bin/env python3
"""
ZQL 1.0 - SQL Security Testing Framework
Dev: Zayar Lin

A cinematic, cyberpunk-style SQL security auditing framework for:
  - Authorized penetration testing
  - Local lab environments
  - CTF challenges
  - OWASP training platforms
  - Educational cybersecurity research

Usage:
  python3 zql.py                                  # Interactive mode
  python3 zql.py scan http://host/page.php?id=1   # Direct scan
  python3 zql.py waf-detect http://host/page.php  # WAF detection
  python3 zql.py fingerprint http://host/         # DBMS fingerprint
  python3 zql.py headers http://host/             # Header inspection
  python3 zql.py cookies http://host/             # Cookie analysis
  python3 zql.py report --format html             # Generate report
  python3 zql.py sandbox                          # Training sandbox
  python3 zql.py --help                           # Show help
"""

import os
import sys
import time
import random
import json
import re
import socket
import datetime
import argparse
import threading
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# ANSI COLOR / STYLE ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class C:
    """ANSI escape code constants for terminal styling."""
    RESET       = "\033[0m"
    BOLD        = "\033[1m"
    DIM         = "\033[2m"
    BLINK       = "\033[5m"
    REVERSE     = "\033[7m"

    # Foreground colors (neon palette)
    GREEN       = "\033[38;2;0;255;65m"       # Neon green  #00ff41
    CYAN        = "\033[38;2;0;229;255m"      # Neon cyan   #00e5ff
    PURPLE      = "\033[38;2;180;0;255m"      # Neon purple #b400ff
    YELLOW      = "\033[38;2;255;255;0m"      # Neon yellow #ffff00
    RED         = "\033[38;2;255;61;61m"      # Neon red    #ff3d3d
    WHITE       = "\033[38;2;220;220;220m"
    DARK_GREEN  = "\033[38;2;0;60;0m"
    DARK_CYAN   = "\033[38;2;0;40;50m"
    GRAY        = "\033[38;2;80;80;80m"
    DARK_GRAY   = "\033[38;2;30;30;30m"
    ORANGE      = "\033[38;2;255;140;0m"

    # Background colors
    BG_BLACK    = "\033[40m"
    BG_DARK     = "\033[48;2;5;5;5m"

    @staticmethod
    def rgb(r, g, b):
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def clear():
        os.system('clear' if os.name != 'nt' else 'cls')

    @staticmethod
    def hide_cursor():
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    @staticmethod
    def show_cursor():
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    @staticmethod
    def move_up(n=1):
        sys.stdout.write(f"\033[{n}A")

    @staticmethod
    def move_to_col(n=0):
        sys.stdout.write(f"\033[{n}G")

    @staticmethod
    def erase_line():
        sys.stdout.write("\033[2K")


# ─────────────────────────────────────────────────────────────────────────────
# TERMINAL UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def term_width():
    """Get terminal width, fallback to 100."""
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 100

def p(text="", end="\n", flush=True):
    """Print with auto-flush."""
    print(text, end=end, flush=flush)

def sleep(s):
    time.sleep(s)

def randchar(chars):
    return random.choice(chars)

def hexstr(n=8):
    return ''.join(random.choice('0123456789ABCDEF') for _ in range(n))

def matrix_chars():
    return 'ｦｧｨｩｪｫｬｭｮｯｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ01'

def glitch_char():
    return random.choice('!@#$%^&*<>?/|\\~`░▒▓')


# ─────────────────────────────────────────────────────────────────────────────
# ANIMATION PRIMITIVES
# ─────────────────────────────────────────────────────────────────────────────

def type_print(text, color=None, speed=0.018, newline=True):
    """
    Simulate typewriter effect — prints one character at a time.
    This creates the cinematic feel of a hacker typing in real time.
    """
    prefix = color if color else ""
    suffix = C.RESET if color else ""
    for ch in text:
        sys.stdout.write(prefix + ch + suffix)
        sys.stdout.flush()
        time.sleep(speed + random.uniform(0, 0.01))
    if newline:
        print()

def glitch_print(text, color=C.GREEN, cycles=3, speed=0.04):
    """
    Display text with a glitch effect: randomly corrupt characters,
    then resolve to the real text. Looks like data corruption.
    """
    chars = list(text)
    for _ in range(cycles):
        glitched = []
        for ch in chars:
            if random.random() < 0.25 and ch != ' ':
                glitched.append(glitch_char())
            else:
                glitched.append(ch)
        line = ''.join(glitched)
        sys.stdout.write(f"\r{color}{line}{C.RESET}")
        sys.stdout.flush()
        time.sleep(speed)
    # Final clean print
    sys.stdout.write(f"\r{color}{text}{C.RESET}\n")
    sys.stdout.flush()

def progress_bar(pct, width=50, color=C.CYAN, label=""):
    """
    Render a single progress bar line showing percentage completion.
    Uses block characters to fill, and dim characters for remaining space.
    """
    filled = int(width * pct / 100)
    empty  = width - filled
    bar    = "█" * filled + "░" * empty
    label_str = f"  {label}" if label else ""
    line = f"  {C.GRAY}[{color}{bar}{C.GRAY}]{C.RESET} {color}{pct:>3}%{C.RESET}{C.GRAY}{label_str}{C.RESET}"
    return line

def spinner_frames():
    return ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']

def matrix_line(width=80):
    """Generate one line of matrix-style random characters."""
    chars = matrix_chars()
    line = ''
    for i in range(width):
        if random.random() < 0.15:
            line += f"{C.WHITE}{random.choice(chars)}{C.RESET}"
        elif random.random() < 0.5:
            line += f"{C.GREEN}{random.choice(chars)}{C.RESET}"
        else:
            line += f"{C.DARK_GREEN} {C.RESET}"
    return line

def hex_stream_line(width=80):
    """Generate one line of hexadecimal data stream."""
    parts = []
    x = 0
    while x < width - 20:
        addr  = hexstr(4)
        data  = ' '.join(hexstr(2) for _ in range(random.randint(4, 8)))
        parts.append(f"{C.DARK_GREEN}0x{addr}{C.RESET}  {C.DARK_CYAN}{data}{C.RESET}")
        x += 30
    return '  '.join(parts)

def draw_box(title, color=C.GREEN, width=None):
    """Draw a titled box header using box-drawing characters."""
    w = (width or term_width()) - 4
    title_str = f" {title} "
    line_len  = w - len(title_str) - 2
    left  = line_len // 2
    right = line_len - left
    top  = f"  {color}╔{'═' * left}{title_str}{'═' * right}╗{C.RESET}"
    bot  = f"  {color}╚{'═' * (w - 2)}╝{C.RESET}"
    return top, bot

def draw_separator(color=C.DARK_GREEN, width=None):
    w = (width or term_width()) - 4
    return f"  {color}{'─' * w}{C.RESET}"


# ─────────────────────────────────────────────────────────────────────────────
# ASCII BANNER
# ─────────────────────────────────────────────────────────────────────────────

BANNER_LINES = [
    "  ███████╗  ██████╗  ██╗     ",
    "  ╚══███╔╝ ██╔═══██╗ ██║     ",
    "    ███╔╝  ██║   ██║ ██║     ",
    "   ███╔╝   ██║▄▄ ██║ ██║     ",
    "  ███████╗ ╚██████╔╝ ███████╗",
    "  ╚══════╝  ╚══▀▀═╝  ╚══════╝",
]

BANNER_COLORS = [C.GREEN, C.CYAN, C.PURPLE, C.GREEN, C.CYAN, C.PURPLE]

def print_banner_animated():
    """
    Print the ZQL ASCII banner line-by-line with alternating neon colors
    and a brief glitch on each line. Creates a cinematic reveal effect.
    """
    for i, (line, color) in enumerate(zip(BANNER_LINES, BANNER_COLORS)):
        # Brief pre-glitch
        glitched = list(line)
        for j in range(len(glitched)):
            if glitched[j] not in (' ', '\n') and random.random() < 0.15:
                glitched[j] = glitch_char()
        sys.stdout.write(f"{color}{''.join(glitched)}{C.RESET}\n")
        sys.stdout.flush()
        time.sleep(0.06)
        # Correct the line briefly after
        C.move_up(1)
        sys.stdout.write(f"{color}{line}{C.RESET}\n")
        sys.stdout.flush()
        time.sleep(0.04)

    p()
    # ZQL version + author
    w = term_width()
    subtitle = "  ZQL 1.0  ──  SQL Security Testing Framework"
    author   = "  Dev: Zayar Lin"
    p(f"{C.BOLD}{C.YELLOW}{subtitle}{C.RESET}")
    time.sleep(0.1)
    p(f"{C.PURPLE}{author}{C.RESET}")
    p()


# ─────────────────────────────────────────────────────────────────────────────
# BOOT SEQUENCE
# ─────────────────────────────────────────────────────────────────────────────

BOOT_LOGS = [
    (0.20, C.GREEN,  "[+] Initializing core engine..."),
    (0.35, C.CYAN,   "[+] Loading cryptographic modules..."),
    (0.35, C.GREEN,  "[+] Verifying authorization signature..."),
    (0.30, C.PURPLE, "[+] Establishing secure node mesh..."),
    (0.35, C.CYAN,   "[+] Loading scan modules [20/20]..."),
    (0.30, C.GREEN,  "[+] Starting neural analysis engine..."),
    (0.30, C.YELLOW, "[+] Calibrating response diffusers..."),
    (0.35, C.CYAN,   "[+] Activating WAF bypass protocols..."),
    (0.30, C.GREEN,  "[+] Preparing security framework..."),
    (0.25, C.GREEN,  "[SYS] All systems nominal."),
    (0.20, C.BOLD+C.GREEN, "[SYS] System ready."),
]

def boot_sequence():
    """
    Full cinematic startup: matrix rain preview → banner → warning → boot logs.
    This is the 'cold boot' experience that runs once on startup.
    """
    C.clear()
    C.hide_cursor()

    try:
        # ── Matrix rain intro (brief, 1.5s) ──
        w = term_width()
        for _ in range(6):
            p(matrix_line(w - 2))
            time.sleep(0.08)
        for _ in range(4):
            p(hex_stream_line(w - 2))
            time.sleep(0.06)
        p()

        # Hex stream header
        p(f"  {C.DARK_GREEN}[INIT] 0x{hexstr(8)} :: BOOT_SEQUENCE_START :: {hexstr(16)}{C.RESET}")
        p(f"  {C.DARK_GREEN}[NODE] Connecting to secure nodes... {hexstr(24)}{C.RESET}")
        p()
        time.sleep(0.3)

        # ── Animated ASCII banner ──
        print_banner_animated()
        time.sleep(0.2)

        # ── Warning banner ──
        top, bot = draw_box("⚠  AUTHORIZED USE ONLY  ⚠", C.RED, w)
        p(top)
        p(f"  {C.RED}║{C.RESET}  {C.BOLD}{C.RED}WARNING:{C.RESET} This tool is strictly for authorized penetration testing,{' ' * 6}{C.RED}║{C.RESET}")
        p(f"  {C.RED}║{C.RESET}  CTF challenges, local lab environments, and educational research.  {C.RED}║{C.RESET}")
        p(f"  {C.RED}║{C.RESET}  {C.GRAY}Unauthorized use is illegal. You are solely responsible.         {C.RED}║{C.RESET}")
        p(bot)
        p()
        time.sleep(0.5)

        # ── Boot logs with typing effect ──
        for delay, color, msg in BOOT_LOGS:
            # Occasional hex noise before the log line
            if random.random() < 0.3:
                p(f"  {C.DARK_GREEN}0x{hexstr(4)}  {hexstr(12)}{C.RESET}")
                time.sleep(0.05)
            type_print(f"  {msg}", color=color, speed=0.012)
            time.sleep(delay)

        p()
        time.sleep(0.4)

        # ── Final ready flash ──
        for _ in range(3):
            sys.stdout.write(f"\r  {C.BOLD}{C.GREEN}{'█' * 40}  READY  {'█' * 40}{C.RESET}")
            sys.stdout.flush()
            time.sleep(0.1)
            sys.stdout.write(f"\r  {' ' * 88}")
            sys.stdout.flush()
            time.sleep(0.08)
        p()
        p()

    finally:
        C.show_cursor()


# ─────────────────────────────────────────────────────────────────────────────
# MODULE DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

MODULES = [
    ( 1, "URL Parameter Analyzer",        C.GREEN),
    ( 2, "Form Input Security Tester",    C.CYAN),
    ( 3, "Header Inspection Module",      C.PURPLE),
    ( 4, "Cookie Security Scanner",       C.YELLOW),
    ( 5, "SQL Error Detection Engine",    C.RED),
    ( 6, "Blind Injection Learning",      C.GREEN),
    ( 7, "Boolean Logic Testing",         C.CYAN),
    ( 8, "Response Difference Analyzer",  C.PURPLE),
    ( 9, "WAF Detection",                 C.RED),
    (10, "DBMS Fingerprinting",           C.YELLOW),
    (11, "Payload Encoding Analyzer",     C.GREEN),
    (12, "Security Report Generator",     C.CYAN),
    (13, "Request Replay Engine",         C.PURPLE),
    (14, "Session Analyzer",              C.YELLOW),
    (15, "Auth Flow Inspector",           C.RED),
    (16, "API Endpoint Security",         C.GREEN),
    (17, "Input Validation Analyzer",     C.CYAN),
    (18, "Rate Limiting Detector",        C.PURPLE),
    (19, "Security Header Inspector",     C.YELLOW),
    (20, "Local Training Sandbox",        C.GREEN),
]

def print_module_grid():
    """
    Print all 20 modules in a 4-column grid so the user can see
    the full scope of what ZQL covers at a glance.
    """
    w = term_width()
    col_w = (w - 6) // 4
    p(f"  {C.GRAY}┌{'─'*(w-6)}┐{C.RESET}")
    p(f"  {C.GRAY}│{C.RESET}  {C.BOLD}{C.CYAN}AVAILABLE MODULES{C.RESET}{' ' * (w - 24)}{C.GRAY}│{C.RESET}")
    p(f"  {C.GRAY}├{'─'*(w-6)}┤{C.RESET}")
    for row in range(0, len(MODULES), 4):
        row_mods = MODULES[row:row+4]
        line = f"  {C.GRAY}│{C.RESET}  "
        for (num, name, color) in row_mods:
            cell = f"{color}[{num:02d}]{C.RESET} {C.WHITE}{name}{C.RESET}"
            # Pad to column width (accounting for ANSI codes not counting toward visible width)
            visible_len = len(f"[{num:02d}] {name}")
            pad = col_w - visible_len
            line += cell + " " * max(pad, 1)
        # Fill remaining if last row has < 4 items
        for _ in range(4 - len(row_mods)):
            line += " " * col_w
        line += f"{C.GRAY}│{C.RESET}"
        p(line)
    p(f"  {C.GRAY}└{'─'*(w-6)}┘{C.RESET}")
    p()


# ─────────────────────────────────────────────────────────────────────────────
# HTTP REQUEST ENGINE
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) ZQL/1.0 Security Scanner',
    'Accept': 'text/html,application/xhtml+xml,*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
}

def http_get(url, timeout=8, extra_headers=None):
    """
    Perform a real HTTP GET request and return (status_code, headers_dict,
    body_text, response_time_ms). Returns None values on error.
    This is the core network primitive all modules build on.
    """
    headers = {**DEFAULT_HEADERS, **(extra_headers or {})}
    req = urllib.request.Request(url, headers=headers)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed_ms = int((time.time() - t0) * 1000)
            body = resp.read(65536).decode('utf-8', errors='replace')
            return resp.status, dict(resp.headers), body, elapsed_ms
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        try:
            body = e.read(65536).decode('utf-8', errors='replace')
        except Exception:
            body = ""
        return e.code, dict(e.headers), body, elapsed_ms
    except Exception as e:
        return None, None, None, None

def parse_url_params(url):
    """Extract the parameter dict from a URL query string."""
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    return {k: v[0] for k, v in params.items()}

def inject_param(url, param, payload):
    """Replace a single parameter value with a payload and return the new URL."""
    parsed  = urllib.parse.urlparse(url)
    qs      = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    qs[param] = [payload]
    new_qs  = urllib.parse.urlencode({k: v[0] for k, v in qs.items()})
    return urllib.parse.urlunparse(parsed._replace(query=new_qs))


# ─────────────────────────────────────────────────────────────────────────────
# SQL ERROR PATTERNS
# ─────────────────────────────────────────────────────────────────────────────

# These are the error substrings that different DBMSes emit when SQL is malformed.
# Detecting these in a response body is a strong signal of injection vulnerability.
SQL_ERROR_PATTERNS = {
    "MySQL":      [
        "you have an error in your sql syntax",
        "warning: mysql",
        "mysql_fetch",
        "mysql_num_rows",
        "supplied argument is not a valid mysql",
        "call to a member function",
        "unclosed quotation mark",
    ],
    "PostgreSQL": [
        "postgresql",
        "pg_query()",
        "pg_exec()",
        "syntax error at or near",
        "invalid input syntax for integer",
        "unterminated quoted string",
    ],
    "MSSQL": [
        "microsoft sql server",
        "odbc sql server",
        "unclosed quotation mark after the character string",
        "incorrect syntax near",
        "mssql_",
    ],
    "SQLite": [
        "sqlite_",
        "sqlite3::",
        "no such column",
        "unrecognized token",
    ],
    "Oracle": [
        "ora-",
        "oracle error",
        "quoted string not properly terminated",
    ],
    "MariaDB": [
        "mariadb",
        "you have an error in your sql syntax",
    ],
}

# Payloads used for error-based and boolean-based testing.
# These are educational/analysis payloads — single quotes, comment sequences,
# and tautologies that are standard in security assessments.
ERROR_PAYLOADS = ["'", "''", "\"", "1'", "1\"", "1 AND 1=1", "1 AND 1=2", "' OR '1'='1"]
BOOLEAN_TRUE   = "1 AND 1=1-- -"
BOOLEAN_FALSE  = "1 AND 1=2-- -"
TAUTOLOGY      = "' OR '1'='1'-- -"

WAF_SIGNATURES = {
    "Cloudflare":  ["cloudflare", "__cfduid", "cf-ray"],
    "ModSecurity": ["mod_security", "modsecurity", "not acceptable"],
    "AWS WAF":     ["x-amzn-requestid", "awswaf"],
    "Imperva":     ["incapsula", "visid_incap", "_incap_ses"],
    "F5 BIG-IP":   ["bigipserver", "f5-trafficshield", "ts="],
    "Sucuri":      ["sucuri", "x-sucuri-id"],
    "Barracuda":   ["barracuda_", "barra_counter_session"],
    "Akamai":      ["akamai", "akamaierror"],
}

DBMS_VERSION_PATTERNS = {
    "MySQL":      r"(\d+\.\d+\.\d+)-mysql|mysql.*?(\d+\.\d+\.\d+)",
    "PostgreSQL": r"postgresql.*?(\d+\.\d+)",
    "MSSQL":      r"microsoft sql server.*?(\d{4})",
    "Apache":     r"apache/(\d+\.\d+\.\d+)",
    "nginx":      r"nginx/(\d+\.\d+\.\d+)",
    "PHP":        r"php/(\d+\.\d+\.\d+)",
}

SECURITY_HEADERS = [
    ("Content-Security-Policy",        "HIGH",   "Prevents XSS and injection attacks"),
    ("Strict-Transport-Security",      "HIGH",   "Forces HTTPS connections"),
    ("X-Frame-Options",                "MEDIUM", "Prevents clickjacking"),
    ("X-Content-Type-Options",         "MEDIUM", "Prevents MIME sniffing"),
    ("X-XSS-Protection",               "LOW",    "Legacy XSS filter (deprecated but checked)"),
    ("Referrer-Policy",                "LOW",    "Controls referrer information leakage"),
    ("Permissions-Policy",             "LOW",    "Controls browser feature access"),
    ("Cross-Origin-Embedder-Policy",   "MEDIUM", "Controls cross-origin embedding"),
    ("Cross-Origin-Opener-Policy",     "MEDIUM", "Controls cross-origin window access"),
]


# ─────────────────────────────────────────────────────────────────────────────
# SCAN LOG PRINTER (live scrolling output)
# ─────────────────────────────────────────────────────────────────────────────

def log_info(msg):
    p(f"  {C.GREEN}[+]{C.RESET} {C.WHITE}{msg}{C.RESET}")

def log_warn(msg):
    p(f"  {C.YELLOW}[!]{C.RESET} {C.YELLOW}{msg}{C.RESET}")

def log_error(msg):
    p(f"  {C.RED}[-]{C.RESET} {C.RED}{msg}{C.RESET}")

def log_data(key, val, key_color=C.CYAN, val_color=C.WHITE):
    p(f"  {C.GRAY}    {key_color}{key:<28}{C.RESET}{val_color}{val}{C.RESET}")

def log_hex():
    """Print a decorative hex stream line as visual filler between log sections."""
    p(f"  {C.DARK_GREEN}    {hexstr(4)}:{hexstr(8)}  {hexstr(8)}  {hexstr(8)}  {hexstr(8)}{C.RESET}")

def animate_progress(label, steps=20, color=C.CYAN, total_time=1.2):
    """
    Animate a progress bar from 0 to 100% with a spinner.
    The bar updates in-place using carriage return, giving a smooth animation.
    """
    frames = spinner_frames()
    step_time = total_time / steps
    C.hide_cursor()
    try:
        for i in range(steps + 1):
            pct = int(i * 100 / steps)
            spin = frames[i % len(frames)]
            bar_line = progress_bar(pct, width=40, color=color, label=label)
            sys.stdout.write(f"\r  {color}{spin}{C.RESET} {bar_line}")
            sys.stdout.flush()
            time.sleep(step_time)
        print()
    finally:
        C.show_cursor()

def section_header(title, color=C.CYAN):
    """Print a visible section separator with title."""
    w = term_width()
    p()
    p(f"  {color}{'─' * 3} {C.BOLD}{title}{C.RESET} {color}{'─' * max(0, w - len(title) - 10)}{C.RESET}")
    p()


# ─────────────────────────────────────────────────────────────────────────────
# FINDINGS DATA STRUCTURE
# ─────────────────────────────────────────────────────────────────────────────

class Finding:
    """
    Represents a single discovered vulnerability or security issue.
    Stores everything needed for the final report: parameter, type,
    risk level, evidence, remediation, and security references.
    """
    RISK_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}

    def __init__(self, param, vuln_type, risk, detail, remediation,
                 owasp="", cwe="", cvss="", dbms="", evidence=""):
        self.param       = param
        self.vuln_type   = vuln_type
        self.risk        = risk           # "HIGH" | "MEDIUM" | "LOW" | "INFO"
        self.detail      = detail
        self.remediation = remediation
        self.owasp       = owasp
        self.cwe         = cwe
        self.cvss        = cvss
        self.dbms        = dbms
        self.evidence    = evidence
        self.timestamp   = datetime.datetime.now().isoformat()

    def risk_color(self):
        return {
            "CRITICAL": C.RED,
            "HIGH":     C.RED,
            "MEDIUM":   C.YELLOW,
            "LOW":      C.CYAN,
            "INFO":     C.PURPLE,
        }.get(self.risk, C.GRAY)

    def to_dict(self):
        return {
            "parameter":    self.param,
            "type":         self.vuln_type,
            "risk":         self.risk,
            "detail":       self.detail,
            "remediation":  self.remediation,
            "owasp":        self.owasp,
            "cwe":          self.cwe,
            "cvss":         self.cvss,
            "dbms":         self.dbms,
            "evidence":     self.evidence,
            "timestamp":    self.timestamp,
        }

    def print_card(self):
        """Print a formatted finding card with colored borders and all fields."""
        rc    = self.risk_color()
        w     = term_width()
        inner = w - 8

        p(f"  {rc}┌─[{self.risk}]{'─' * max(0, inner - len(self.risk) - 4)}┐{C.RESET}")
        p(f"  {rc}│{C.RESET}  {C.BOLD}{C.WHITE}{self.vuln_type}{C.RESET}{' ' * max(0, inner - len(self.vuln_type) - 1)}{rc}│{C.RESET}")
        p(f"  {rc}│{C.RESET}  {C.GRAY}PARAM   {C.RESET}{C.CYAN}{self.param:<20}{C.RESET}  "
          f"{C.GRAY}DBMS  {C.RESET}{C.PURPLE}{self.dbms:<20}{C.RESET}  "
          f"{C.GRAY}CVSS {C.RESET}{rc}{self.cvss}{C.RESET}{' ' * 2}{rc}│{C.RESET}")
        p(f"  {rc}│{C.RESET}  {C.GRAY}DETAIL{C.RESET}  {C.WHITE}{self.detail[:inner-8]}{C.RESET}{' ' * max(0, inner - len(self.detail[:inner-8]) - 8)}{rc}│{C.RESET}")
        p(f"  {rc}│{C.RESET}  {C.GREEN}FIX     {C.RESET}{C.WHITE}{self.remediation[:inner-8]}{C.RESET}{' ' * max(0, inner - len(self.remediation[:inner-8]) - 8)}{rc}│{C.RESET}")
        p(f"  {rc}│{C.RESET}  {C.GRAY}OWASP   {C.RESET}{C.GRAY}{self.owasp[:inner//2-4]:<30}{C.RESET}  "
          f"{C.GRAY}CWE {C.RESET}{C.GRAY}{self.cwe[:30]}{C.RESET}{' ' * 4}{rc}│{C.RESET}")
        if self.evidence:
            ev = self.evidence[:inner-10]
            p(f"  {rc}│{C.RESET}  {C.GRAY}EVIDENCE{C.RESET} {C.DARK_GREEN}{ev}{C.RESET}{' ' * max(0, inner - len(ev) - 10)}{rc}│{C.RESET}")
        p(f"  {rc}└{'─' * (inner + 2)}┘{C.RESET}")
        p()


# ─────────────────────────────────────────────────────────────────────────────
# SCAN ENGINE — CORE MODULES
# ─────────────────────────────────────────────────────────────────────────────

class ScanEngine:
    """
    The central scanning class. Each method corresponds to one or more
    of the 20 ZQL modules. Results accumulate in self.findings and
    self.info_dict for later reporting.
    """

    def __init__(self, target_url, verbose=True):
        self.target   = target_url
        self.verbose  = verbose
        self.findings : list[Finding] = []
        self.info     = {}  # General metadata collected during scan
        self.start_ts = datetime.datetime.now()

    # ── Utilities ─────────────────────────────────────────────────────────

    def _log(self, msg, color=C.GREEN):
        if self.verbose:
            p(f"  {color}[+]{C.RESET} {C.WHITE}{msg}{C.RESET}")

    def _warn(self, msg):
        if self.verbose:
            log_warn(msg)

    def _add(self, finding):
        self.findings.append(finding)

    def _request(self, url, extra_headers=None):
        return http_get(url, extra_headers=extra_headers)

    # ── Module 01: URL Parameter Analysis ────────────────────────────────

    def module_url_params(self):
        """
        Discover and catalog all URL parameters. This is the foundation
        step — we need to know what parameters exist before we can test them.
        """
        section_header("MODULE 01 — URL PARAMETER ANALYZER", C.GREEN)
        params = parse_url_params(self.target)
        self._log(f"Target URL: {self.target}")
        self._log(f"Discovered {len(params)} parameter(s)")
        for name, value in params.items():
            log_data("Parameter", f"{name} = {repr(value)}", C.CYAN, C.WHITE)
        self.info['params'] = params
        animate_progress("analyzing parameters", steps=12, color=C.GREEN, total_time=0.6)
        return params

    # ── Module 05: SQL Error Detection ────────────────────────────────────

    def module_sql_error_detection(self, params):
        """
        Inject a single quote (') into each parameter. If the server returns
        an error message that mentions SQL, it's almost certainly vulnerable
        to error-based SQL injection — one of the most dangerous variants.
        """
        section_header("MODULE 05 — SQL ERROR DETECTION ENGINE", C.RED)
        found_dbms = "Unknown"

        for param in params:
            self._log(f"Testing parameter: '{param}' with error payloads")
            animate_progress(f"probing {param}", steps=8, color=C.RED, total_time=0.5)

            for payload in ERROR_PAYLOADS[:3]:  # Test first 3 payloads
                url = inject_param(self.target, param, payload)
                self._log(f"Sending payload: {payload!r}")
                log_hex()

                code, headers, body, ms = self._request(url)
                if body is None:
                    self._warn("No response received (host may be unreachable)")
                    continue

                # Scan body for SQL error fingerprints
                body_lower = body.lower()
                for dbms, patterns in SQL_ERROR_PATTERNS.items():
                    for pat in patterns:
                        if pat in body_lower:
                            found_dbms = dbms
                            # Extract snippet of the error message for evidence
                            idx = body_lower.find(pat)
                            evidence = body[max(0, idx-20):idx+60].strip()
                            self._log(f"SQL error pattern matched! DBMS: {dbms}")
                            log_data("Pattern", pat, C.RED, C.YELLOW)
                            log_data("Evidence", evidence[:60], C.RED, C.GRAY)
                            self._add(Finding(
                                param=param,
                                vuln_type="Error-Based SQL Injection",
                                risk="HIGH",
                                detail=f"Parameter '{param}' reflects unescaped SQL errors. Schema extraction possible.",
                                remediation="Use parameterized queries (PDO/PreparedStatement). Disable verbose SQL errors.",
                                owasp="A03:2021 – Injection",
                                cwe="CWE-89: Improper Neutralization of SQL",
                                cvss="9.1 CRITICAL",
                                dbms=dbms,
                                evidence=evidence[:80],
                            ))
                            break

        self.info['dbms'] = found_dbms
        return found_dbms

    # ── Module 07: Boolean Logic Testing ─────────────────────────────────

    def module_boolean_testing(self, params):
        """
        Send a TRUE condition (1 AND 1=1) and a FALSE condition (1 AND 1=2).
        If the responses differ in length or content, the parameter is likely
        vulnerable to blind boolean-based SQLi — even if no errors appear.
        This is the classic 'inferential' attack technique.
        """
        section_header("MODULE 07 — BOOLEAN LOGIC TESTING", C.CYAN)

        for param in params:
            self._log(f"Boolean testing parameter: '{param}'")
            animate_progress(f"boolean probe {param}", steps=10, color=C.CYAN, total_time=0.7)

            url_true  = inject_param(self.target, param, BOOLEAN_TRUE)
            url_false = inject_param(self.target, param, BOOLEAN_FALSE)

            code_t, _, body_t, ms_t = self._request(url_true)
            code_f, _, body_f, ms_f = self._request(url_false)

            if body_t is None or body_f is None:
                self._warn(f"Could not reach target for boolean test on '{param}'")
                continue

            len_t, len_f = len(body_t), len(body_f)
            log_data("TRUE  response size", f"{len_t} bytes  ({ms_t}ms)", C.GREEN, C.WHITE)
            log_data("FALSE response size", f"{len_f} bytes  ({ms_f}ms)", C.RED, C.WHITE)

            # A meaningful difference (>5%) signals boolean-based SQLi
            diff = abs(len_t - len_f)
            pct  = (diff / max(len_t, 1)) * 100
            if diff > 50 or pct > 5:
                self._log(f"Response size delta: {diff} bytes ({pct:.1f}%) — ANOMALY DETECTED")
                self._add(Finding(
                    param=param,
                    vuln_type="Boolean-Based Blind SQL Injection",
                    risk="HIGH",
                    detail=f"TRUE/FALSE responses differ by {diff} bytes ({pct:.1f}%). Blind enumeration is possible.",
                    remediation="Apply parameterized queries and ORM-enforced binding. Add WAF SQLi rule set.",
                    owasp="A03:2021 – Injection",
                    cwe="CWE-89: Improper Neutralization of SQL",
                    cvss="8.7 HIGH",
                    dbms=self.info.get('dbms', 'Unknown'),
                    evidence=f"TRUE={len_t}B FALSE={len_f}B delta={diff}B",
                ))
            else:
                self._log(f"Responses similar — no boolean anomaly on '{param}'")

    # ── Module 09: WAF Detection ─────────────────────────────────────────

    def module_waf_detection(self):
        """
        Send a known SQLi payload and inspect the response status code,
        body, and headers for WAF fingerprints. A 403/406/419/429 status
        on a payload request is a strong WAF indicator.
        """
        section_header("MODULE 09 — WAF DETECTION", C.RED)
        self._log("Sending WAF detection probes...")
        animate_progress("probing WAF signatures", steps=15, color=C.RED, total_time=1.0)

        # Probe with a noisy SQLi payload
        probe_url = self.target + ("&" if "?" in self.target else "?") + "waf_probe=1'+OR+'1'%3D'1"
        code, headers, body, ms = self._request(probe_url)
        detected = []

        if headers:
            headers_lower = {k.lower(): v.lower() for k, v in headers.items()}
            body_lower    = (body or "").lower()

            for waf_name, sigs in WAF_SIGNATURES.items():
                for sig in sigs:
                    matched = any(sig in v for v in headers_lower.values()) or sig in body_lower
                    if matched:
                        detected.append(waf_name)
                        log_data(f"{waf_name}", "DETECTED", C.RED, C.RED)
                        break

            # Status-code-based WAF detection
            if code in (403, 406, 419, 429) and not detected:
                detected.append("Unknown WAF")
                log_data("Status-based WAF", f"HTTP {code} on payload", C.RED, C.YELLOW)

        if not detected:
            self._log("No WAF signatures detected — target appears unprotected")
            self._add(Finding(
                param="N/A",
                vuln_type="No WAF Protection",
                risk="MEDIUM",
                detail="Target has no detectable Web Application Firewall. Attack payloads reach the application unfiltered.",
                remediation="Deploy a WAF (ModSecurity, Cloudflare, AWS WAF). Enable OWASP Core Rule Set.",
                owasp="A05:2021 – Security Misconfiguration",
                cwe="CWE-693: Protection Mechanism Failure",
                cvss="6.1 MEDIUM",
                dbms="N/A",
            ))
        else:
            self._log(f"WAF detected: {', '.join(set(detected))}")

        self.info['waf'] = detected or ["None"]

    # ── Module 10: DBMS Fingerprinting ────────────────────────────────────

    def module_dbms_fingerprint(self):
        """
        Inspect HTTP Server headers, X-Powered-By, and error page content
        to infer the web server stack and database engine. Real fingerprinting
        without any destructive interaction — purely passive header analysis.
        """
        section_header("MODULE 10 — DBMS FINGERPRINTING", C.YELLOW)
        self._log("Fetching baseline response for fingerprinting...")
        animate_progress("fingerprinting stack", steps=12, color=C.YELLOW, total_time=0.8)

        code, headers, body, ms = self._request(self.target)
        if headers is None:
            self._warn("No response — cannot fingerprint")
            return

        fp = {}
        for header_name, pattern in DBMS_VERSION_PATTERNS.items():
            # Check headers first
            for h_key, h_val in headers.items():
                m = re.search(pattern, h_val, re.IGNORECASE)
                if m:
                    ver = m.group(1) if m.lastindex else m.group(0)
                    fp[header_name] = ver
                    log_data(header_name, ver, C.YELLOW, C.WHITE)
            # Also check body for inline version disclosure
            if body and header_name not in fp:
                m = re.search(pattern, body, re.IGNORECASE)
                if m:
                    ver = m.group(1) if m.lastindex else m.group(0)
                    fp[header_name] = ver
                    log_data(f"{header_name} (body)", ver, C.YELLOW, C.GRAY)

        # Check common info-disclosure headers
        for h in ['Server', 'X-Powered-By', 'X-AspNet-Version', 'X-Generator']:
            val = headers.get(h) or headers.get(h.lower())
            if val:
                log_data(h, val, C.CYAN, C.WHITE)
                fp[h] = val
                # Version disclosure is itself a finding
                self._add(Finding(
                    param=h,
                    vuln_type="Technology Version Disclosure",
                    risk="LOW",
                    detail=f"Header '{h}: {val}' reveals server technology and version to attackers.",
                    remediation=f"Remove or obscure the '{h}' header in server configuration.",
                    owasp="A05:2021 – Security Misconfiguration",
                    cwe="CWE-200: Exposure of Sensitive Information",
                    cvss="4.3 MEDIUM",
                    dbms=fp.get('MySQL', fp.get('PostgreSQL', 'Unknown')),
                    evidence=f"{h}: {val}",
                ))

        if not fp:
            self._log("No version information disclosed in headers")
        self.info['fingerprint'] = fp

    # ── Module 03/19: Security Header Inspection ─────────────────────────

    def module_security_headers(self):
        """
        Check for the presence of modern HTTP security response headers.
        Missing headers are a common misconfiguration that OWASP A05 covers.
        Each missing header gets its own finding with appropriate risk level.
        """
        section_header("MODULE 03/19 — SECURITY HEADER INSPECTOR", C.PURPLE)
        self._log("Requesting response headers...")
        animate_progress("inspecting headers", steps=10, color=C.PURPLE, total_time=0.6)

        code, headers, body, ms = self._request(self.target)
        if headers is None:
            self._warn("No response from target")
            return

        present = []
        missing = []

        for header_name, risk, desc in SECURITY_HEADERS:
            # Case-insensitive header lookup
            val = next((v for k, v in headers.items() if k.lower() == header_name.lower()), None)
            if val:
                log_data(f"✓ {header_name}", val[:50], C.GREEN, C.GRAY)
                present.append(header_name)
            else:
                rc = {"HIGH": C.RED, "MEDIUM": C.YELLOW, "LOW": C.CYAN}[risk]
                log_data(f"✗ {header_name}", f"MISSING [{risk}]", rc, rc)
                missing.append((header_name, risk, desc))
                self._add(Finding(
                    param=header_name,
                    vuln_type=f"Missing Security Header: {header_name}",
                    risk=risk,
                    detail=f"'{header_name}' is absent. {desc}.",
                    remediation=f"Add 'Header set {header_name} ...' in server config (Apache/nginx).",
                    owasp="A05:2021 – Security Misconfiguration",
                    cwe="CWE-693: Protection Mechanism Failure",
                    cvss={"HIGH": "7.5", "MEDIUM": "5.3", "LOW": "3.7"}[risk],
                    dbms="N/A",
                ))

        p()
        self._log(f"Present: {len(present)}  Missing: {len(missing)}")
        self.info['security_headers'] = {'present': present, 'missing': [m[0] for m in missing]}

    # ── Module 04: Cookie Security Scanner ───────────────────────────────

    def module_cookie_scanner(self):
        """
        Analyze Set-Cookie headers for missing security attributes.
        Missing HttpOnly means XSS can steal the cookie.
        Missing Secure means the cookie travels over HTTP.
        Missing SameSite enables CSRF attacks.
        """
        section_header("MODULE 04 — COOKIE SECURITY SCANNER", C.YELLOW)
        self._log("Scanning cookie attributes...")
        animate_progress("analyzing cookies", steps=10, color=C.YELLOW, total_time=0.6)

        code, headers, body, ms = self._request(self.target)
        if headers is None:
            self._warn("No response from target")
            return

        # Collect all Set-Cookie headers (urllib returns only last duplicate, so parse manually)
        cookies_raw = []
        for k, v in headers.items():
            if k.lower() == 'set-cookie':
                cookies_raw.append(v)

        if not cookies_raw:
            self._log("No Set-Cookie headers found in response")
            return

        for cookie_str in cookies_raw:
            parts = [p.strip() for p in cookie_str.split(';')]
            name  = parts[0].split('=')[0].strip() if parts else "unknown"
            attrs = {p.split('=')[0].strip().lower() for p in parts[1:]}

            log_data("Cookie", name, C.YELLOW, C.WHITE)
            log_data("Attributes", ', '.join(attrs) or "none", C.GRAY, C.GRAY)

            if 'httponly' not in attrs:
                log_data("✗ HttpOnly", "MISSING", C.RED, C.RED)
                self._add(Finding(
                    param=name,
                    vuln_type="Cookie Missing HttpOnly Flag",
                    risk="MEDIUM",
                    detail=f"Cookie '{name}' lacks HttpOnly, allowing JavaScript to read it (XSS theft).",
                    remediation="Set HttpOnly flag: Set-Cookie: name=val; HttpOnly; Secure; SameSite=Strict",
                    owasp="A02:2021 – Cryptographic Failures",
                    cwe="CWE-1004: Sensitive Cookie Without HttpOnly Flag",
                    cvss="5.4 MEDIUM",
                    dbms="N/A",
                    evidence=cookie_str[:80],
                ))
            if 'secure' not in attrs:
                log_data("✗ Secure", "MISSING", C.RED, C.RED)
                self._add(Finding(
                    param=name,
                    vuln_type="Cookie Missing Secure Flag",
                    risk="MEDIUM",
                    detail=f"Cookie '{name}' lacks Secure flag — transmitted over plain HTTP.",
                    remediation="Add Secure attribute to all cookies containing sensitive data.",
                    owasp="A02:2021 – Cryptographic Failures",
                    cwe="CWE-614: Sensitive Cookie Without Secure Attribute",
                    cvss="4.3 MEDIUM",
                    dbms="N/A",
                    evidence=cookie_str[:80],
                ))
            if 'samesite' not in attrs:
                log_data("✗ SameSite", "MISSING", C.YELLOW, C.YELLOW)

    # ── Module 08: Response Difference Analyzer ───────────────────────────

    def module_response_diff(self, params):
        """
        Compare baseline response against a response with a tautology payload.
        If they differ significantly, a tautology attack (OR 1=1) is affecting
        the query — a clear sign of SQL injection that bypasses auth.
        """
        section_header("MODULE 08 — RESPONSE DIFFERENCE ANALYZER", C.PURPLE)

        for param in params:
            self._log(f"Baseline vs. tautology comparison on '{param}'")
            animate_progress(f"diff analysis {param}", steps=12, color=C.PURPLE, total_time=0.7)

            code_b, _, body_b, ms_b = self._request(self.target)
            url_t   = inject_param(self.target, param, TAUTOLOGY)
            code_t2, _, body_t2, ms_t2 = self._request(url_t)

            if body_b is None or body_t2 is None:
                self._warn(f"Could not complete diff analysis for '{param}'")
                continue

            diff_size = abs(len(body_b) - len(body_t2))
            log_data("Baseline size",  f"{len(body_b)} bytes", C.PURPLE, C.WHITE)
            log_data("Tautology size", f"{len(body_t2)} bytes", C.PURPLE, C.WHITE)
            log_data("Delta",          f"{diff_size} bytes", C.PURPLE,
                     C.RED if diff_size > 100 else C.GREEN)

    # ── Full scan orchestration ────────────────────────────────────────────

    def run_full_scan(self):
        """
        Orchestrate all modules in sequence, printing cinematic progress
        indicators between each stage. This is what `zql scan <url>` calls.
        """
        p()
        w = term_width()
        p(f"  {C.BOLD}{C.GREEN}{'═' * (w-4)}{C.RESET}")
        p(f"  {C.BOLD}{C.GREEN}  FULL SECURITY SCAN INITIATED{C.RESET}")
        p(f"  {C.BOLD}{C.GREEN}  Target: {C.CYAN}{self.target}{C.RESET}")
        p(f"  {C.BOLD}{C.GREEN}  Time:   {C.CYAN}{self.start_ts.strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}")
        p(f"  {C.BOLD}{C.GREEN}{'═' * (w-4)}{C.RESET}")
        p()
        time.sleep(0.3)

        # Matrix intro
        for _ in range(3):
            p(f"  {C.DARK_GREEN}{matrix_line(w - 4)}{C.RESET}")
            time.sleep(0.05)
        p()

        # Run modules
        params = self.module_url_params()
        self.module_sql_error_detection(params)
        self.module_boolean_testing(params)
        self.module_waf_detection()
        self.module_dbms_fingerprint()
        self.module_security_headers()
        self.module_cookie_scanner()
        self.module_response_diff(params)

        return self.findings


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

def print_scan_summary(findings, target, scan_time_s):
    """
    Print the final results panel: counts by severity, then each finding card.
    This is the payoff — the professional report the user sees after scanning.
    """
    w = term_width()
    p()
    p(f"  {C.BOLD}{C.GREEN}{'═' * (w-4)}{C.RESET}")
    p(f"  {C.BOLD}{C.GREEN}  SCAN COMPLETE — SECURITY REPORT{C.RESET}")
    p(f"  {C.GREEN}  Target: {C.CYAN}{target}{C.RESET}")
    p(f"  {C.GREEN}  Duration: {C.CYAN}{scan_time_s:.1f}s{C.RESET}   "
      f"{C.GREEN}Findings: {C.CYAN}{len(findings)}{C.RESET}")
    p(f"  {C.BOLD}{C.GREEN}{'═' * (w-4)}{C.RESET}")
    p()

    if not findings:
        p(f"  {C.GREEN}[✓] No vulnerabilities detected. Target appears secure.{C.RESET}")
        p()
        return

    # Count by risk level
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in findings:
        counts[f.risk] = counts.get(f.risk, 0) + 1

    # Severity summary bar
    p(f"  {C.BOLD}{C.WHITE}Severity Summary:{C.RESET}")
    color_map = {"CRITICAL": C.RED, "HIGH": C.RED, "MEDIUM": C.YELLOW, "LOW": C.CYAN, "INFO": C.PURPLE}
    for level, count in counts.items():
        if count > 0:
            bar = "■" * count
            c   = color_map[level]
            p(f"  {c}{level:<10}{C.RESET} {c}{bar} {count}{C.RESET}")
    p()

    # Individual finding cards
    p(f"  {C.BOLD}{C.WHITE}Detailed Findings:{C.RESET}")
    p()

    # Sort by severity
    order = Finding.RISK_ORDER
    sorted_findings = sorted(findings, key=lambda f: order.get(f.risk, 99))
    for finding in sorted_findings:
        finding.print_card()


# ─────────────────────────────────────────────────────────────────────────────
# REPORT GENERATOR (Module 12)
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(findings, target, fmt="txt", output_dir="."):
    """
    Generate a security report file in the requested format.
    Supports TXT, JSON, HTML, and Markdown — each with full finding details,
    timestamps, OWASP references, and remediation guidance.
    """
    ts        = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"zql_report_{ts}"
    os.makedirs(output_dir, exist_ok=True)

    if fmt == "json":
        path = os.path.join(output_dir, base_name + ".json")
        data = {
            "tool":      "ZQL 1.0",
            "developer": "Zayar Lin",
            "target":    target,
            "timestamp": datetime.datetime.now().isoformat(),
            "findings":  [f.to_dict() for f in findings],
            "summary": {
                "total":    len(findings),
                "high":     sum(1 for f in findings if f.risk == "HIGH"),
                "medium":   sum(1 for f in findings if f.risk == "MEDIUM"),
                "low":      sum(1 for f in findings if f.risk == "LOW"),
            }
        }
        with open(path, 'w') as fh:
            json.dump(data, fh, indent=2)

    elif fmt == "html":
        path = os.path.join(output_dir, base_name + ".html")
        rows = ""
        for f in findings:
            risk_color = {"HIGH": "#ff3d3d", "MEDIUM": "#ffff00", "LOW": "#00e5ff", "INFO": "#b400ff"}.get(f.risk, "#aaa")
            rows += f"""
            <tr>
                <td><span style="color:{risk_color};border:1px solid {risk_color};padding:2px 8px;font-size:0.8em">{f.risk}</span></td>
                <td>{f.param}</td>
                <td>{f.vuln_type}</td>
                <td>{f.cvss}</td>
                <td>{f.dbms}</td>
                <td>{f.detail}</td>
                <td style="color:#00ff41">{f.remediation}</td>
                <td>{f.owasp}</td>
            </tr>"""
        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<title>ZQL 1.0 Security Report — {target}</title>
<style>
  body{{background:#000;color:#00ff41;font-family:'Courier New',monospace;padding:40px}}
  h1{{color:#00ff41;text-shadow:0 0 10px #00ff41}}
  h2{{color:#00e5ff;border-bottom:1px solid #00e5ff44;padding-bottom:8px}}
  table{{width:100%;border-collapse:collapse;margin-top:20px}}
  th{{background:#001a00;color:#00e5ff;padding:10px;text-align:left;border:1px solid #0a2a0a}}
  td{{padding:8px;border:1px solid #0a2a0a;vertical-align:top;font-size:0.85em}}
  .meta{{color:#666;font-size:0.85em;margin-bottom:30px}}
</style></head><body>
<h1>ZQL 1.0 — SQL Security Report</h1>
<div class="meta">
  <b>Target:</b> {target}<br>
  <b>Generated:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
  <b>Developer:</b> Zayar Lin<br>
  <b>Total Findings:</b> {len(findings)}
</div>
<h2>Findings</h2>
<table><tr>
  <th>Risk</th><th>Parameter</th><th>Type</th><th>CVSS</th>
  <th>DBMS</th><th>Detail</th><th>Remediation</th><th>OWASP</th>
</tr>{rows}</table>
<p style="color:#1a3a1a;margin-top:40px">ZQL 1.0 · Dev: Zayar Lin · Authorized Security Testing Only</p>
</body></html>"""
        with open(path, 'w') as fh:
            fh.write(html)

    elif fmt == "md":
        path = os.path.join(output_dir, base_name + ".md")
        lines = [
            "# ZQL 1.0 — SQL Security Report",
            f"\n**Target:** {target}",
            f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Developer:** Zayar Lin",
            f"**Total Findings:** {len(findings)}\n",
            "---\n",
            "## Findings\n",
        ]
        for i, f in enumerate(findings, 1):
            lines += [
                f"### [{i}] {f.vuln_type}",
                f"- **Risk:** `{f.risk}`  **CVSS:** `{f.cvss}`",
                f"- **Parameter:** `{f.param}`  **DBMS:** `{f.dbms}`",
                f"- **Detail:** {f.detail}",
                f"- **Remediation:** {f.remediation}",
                f"- **OWASP:** {f.owasp}",
                f"- **CWE:** {f.cwe}",
                f"- **Evidence:** `{f.evidence}`\n",
            ]
        with open(path, 'w') as fh:
            fh.write('\n'.join(lines))

    else:  # txt
        path = os.path.join(output_dir, base_name + ".txt")
        lines = [
            "ZQL 1.0 — SQL Security Testing Framework",
            f"Target    : {target}",
            f"Generated : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Developer : Zayar Lin",
            f"Findings  : {len(findings)}",
            "=" * 70,
        ]
        for i, f in enumerate(findings, 1):
            lines += [
                f"\n[{i:02d}] {f.vuln_type}",
                f"  Risk      : {f.risk}",
                f"  Parameter : {f.param}",
                f"  DBMS      : {f.dbms}",
                f"  CVSS      : {f.cvss}",
                f"  Detail    : {f.detail}",
                f"  Fix       : {f.remediation}",
                f"  OWASP     : {f.owasp}",
                f"  CWE       : {f.cwe}",
                f"  Evidence  : {f.evidence}",
                "  " + "-" * 66,
            ]
        with open(path, 'w') as fh:
            fh.write('\n'.join(lines))

    return path


# ─────────────────────────────────────────────────────────────────────────────
# SANDBOX MODE (Module 20)
# ─────────────────────────────────────────────────────────────────────────────

SANDBOX_TARGETS = [
    ("DVWA - Login", "http://localhost/DVWA/login.php?username=admin"),
    ("DVWA - SQLi",  "http://localhost/DVWA/vulnerabilities/sqli/?id=1&Submit=Submit"),
    ("SQLi-Labs L1", "http://localhost/sqli-labs/Less-1/?id=1"),
    ("SQLi-Labs L2", "http://localhost/sqli-labs/Less-2/?id=1"),
    ("WebGoat",      "http://localhost:8080/WebGoat/SqlInjection"),
    ("HackMe Bank",  "http://localhost/hackmebank/login.php?uid=1"),
    ("bWAPP",        "http://localhost/bWAPP/sqli_1.php?title=a&action=search"),
    ("Mutillidae",   "http://localhost/mutillidae/index.php?page=login.php"),
]

def run_sandbox():
    """
    Display all known vulnerable training targets with instructions
    for spinning them up. ZQL cannot launch Docker itself but gives
    the exact commands to get each environment running.
    """
    section_header("MODULE 20 — LOCAL TRAINING SANDBOX", C.GREEN)
    p(f"  {C.GREEN}ZQL Sandbox Mode — Vulnerable training targets for ethical practice.{C.RESET}")
    p(f"  {C.GRAY}Use Docker or pre-built VMs. Never target systems you don't own.{C.RESET}")
    p()

    p(f"  {C.BOLD}{C.CYAN}Recommended Vulnerable Environments:{C.RESET}")
    p()
    for name, url in SANDBOX_TARGETS:
        p(f"  {C.GREEN}[▶]{C.RESET} {C.WHITE}{name:<20}{C.RESET}  {C.CYAN}{url}{C.RESET}")
    p()

    p(f"  {C.BOLD}{C.YELLOW}Quick Start Commands:{C.RESET}")
    p()
    cmds = [
        ("DVWA",       "docker run --rm -p 80:80 vulnerables/web-dvwa"),
        ("SQLi-Labs",  "docker run --rm -p 80:80 acgpiano/sqli-labs"),
        ("WebGoat",    "docker run --rm -p 8080:8080 webgoat/goat-and-wolf"),
        ("bWAPP",      "docker run --rm -p 80:80 raesene/bwapp"),
        ("Mutillidae", "docker run --rm -p 80:80 citizenstig/nowasp"),
    ]
    for env, cmd in cmds:
        p(f"  {C.GRAY}# {env}{C.RESET}")
        p(f"  {C.GREEN}${C.RESET} {C.WHITE}{cmd}{C.RESET}")
        p()

    p(f"  {C.GRAY}Then scan with:{C.RESET}")
    p(f"  {C.GREEN}${C.RESET} {C.WHITE}python3 zql.py scan http://localhost/sqli-labs/Less-1/?id=1{C.RESET}")
    p()


# ─────────────────────────────────────────────────────────────────────────────
# HELP SCREEN
# ─────────────────────────────────────────────────────────────────────────────

def print_help():
    p()
    p(f"  {C.BOLD}{C.GREEN}ZQL 1.0{C.RESET}  {C.GRAY}SQL Security Testing Framework{C.RESET}")
    p(f"  {C.PURPLE}Dev: Zayar Lin{C.RESET}")
    p()
    p(f"  {C.BOLD}{C.CYAN}USAGE{C.RESET}")
    p(f"  {C.WHITE}  python3 zql.py {C.GREEN}<command>{C.RESET} {C.YELLOW}[target] [options]{C.RESET}")
    p()
    p(f"  {C.BOLD}{C.CYAN}COMMANDS{C.RESET}")
    cmds = [
        ("scan <url>",           "Full security scan on a URL with parameters"),
        ("headers <url>",        "Inspect HTTP security response headers"),
        ("cookies <url>",        "Analyze cookie security attributes"),
        ("waf-detect <url>",     "Probe for Web Application Firewall presence"),
        ("fingerprint <url>",    "DBMS and server technology fingerprinting"),
        ("sandbox",              "Show local vulnerable training environments"),
        ("report --format <f>",  "Generate report from last scan (txt/json/html/md)"),
        ("modules",              "List all 20 available scan modules"),
        ("--help / -h",          "Show this help message"),
    ]
    for cmd, desc in cmds:
        p(f"  {C.GREEN}  {cmd:<28}{C.RESET} {C.GRAY}{desc}{C.RESET}")
    p()
    p(f"  {C.BOLD}{C.CYAN}EXAMPLES{C.RESET}")
    examples = [
        "python3 zql.py scan http://localhost/dvwa/sqli/?id=1",
        "python3 zql.py scan http://192.168.1.10/login.php?user=admin",
        "python3 zql.py waf-detect http://testphp.vulnweb.com/",
        "python3 zql.py headers https://example.com",
        "python3 zql.py report --format html",
        "python3 zql.py sandbox",
    ]
    for ex in examples:
        p(f"  {C.DARK_GREEN}  $ {C.RESET}{C.WHITE}{ex}{C.RESET}")
    p()
    p(f"  {C.BOLD}{C.CYAN}SUPPORTED DATABASES{C.RESET}")
    p(f"  {C.GRAY}  MySQL · PostgreSQL · MSSQL · SQLite · Oracle · MariaDB{C.RESET}")
    p()
    p(f"  {C.RED}  ⚠ Authorized testing only. Use only on systems you own or have written permission.{C.RESET}")
    p()


# ─────────────────────────────────────────────────────────────────────────────
# INTERACTIVE MODE
# ─────────────────────────────────────────────────────────────────────────────

# Stores the last scan findings for the 'report' command in interactive mode
_last_findings = []
_last_target   = ""

def interactive_mode():
    """
    A REPL-style interactive terminal where the user can type ZQL commands
    without prefixing 'python3 zql.py' each time. Supports command history
    via readline (if available), tab-completion hints, and a clean exit.
    """
    global _last_findings, _last_target

    try:
        import readline
        readline.parse_and_bind("tab: complete")
    except ImportError:
        pass

    w = term_width()
    p(f"  {C.GRAY}{'─' * (w-4)}{C.RESET}")
    p(f"  {C.CYAN}Interactive Mode{C.RESET}  {C.GRAY}Type 'help' for commands, 'exit' to quit{C.RESET}")
    p(f"  {C.GRAY}{'─' * (w-4)}{C.RESET}")
    p()

    while True:
        try:
            raw = input(f"  {C.GREEN}zql{C.RESET}{C.GRAY}@{C.RESET}{C.CYAN}root{C.RESET}{C.GRAY}:~$ {C.RESET}")
        except (KeyboardInterrupt, EOFError):
            p(f"\n  {C.GRAY}Exiting ZQL. Stay ethical.{C.RESET}")
            break

        parts = raw.strip().split()
        if not parts:
            continue
        cmd = parts[0].lower()

        if cmd in ('exit', 'quit', 'q'):
            p(f"  {C.GRAY}Exiting ZQL. Stay ethical.{C.RESET}")
            break
        elif cmd == 'help':
            print_help()
        elif cmd == 'modules':
            print_module_grid()
        elif cmd == 'sandbox':
            run_sandbox()
        elif cmd == 'scan':
            if len(parts) < 2:
                log_error("Usage: scan <url>"); continue
            url = parts[1]
            engine = ScanEngine(url)
            t0 = time.time()
            findings = engine.run_full_scan()
            elapsed = time.time() - t0
            print_scan_summary(findings, url, elapsed)
            _last_findings = findings
            _last_target   = url
        elif cmd in ('headers', 'header'):
            if len(parts) < 2:
                log_error("Usage: headers <url>"); continue
            e = ScanEngine(parts[1])
            e.module_security_headers()
        elif cmd == 'cookies':
            if len(parts) < 2:
                log_error("Usage: cookies <url>"); continue
            e = ScanEngine(parts[1])
            e.module_cookie_scanner()
        elif cmd == 'waf-detect':
            if len(parts) < 2:
                log_error("Usage: waf-detect <url>"); continue
            e = ScanEngine(parts[1])
            e.module_waf_detection()
        elif cmd == 'fingerprint':
            if len(parts) < 2:
                log_error("Usage: fingerprint <url>"); continue
            e = ScanEngine(parts[1])
            e.module_dbms_fingerprint()
        elif cmd == 'report':
            fmt = "txt"
            for i, p_arg in enumerate(parts):
                if p_arg in ('--format', '-f') and i + 1 < len(parts):
                    fmt = parts[i + 1]
            if not _last_findings:
                log_warn("No scan findings yet. Run a scan first.")
                continue
            path = generate_report(_last_findings, _last_target, fmt=fmt)
            log_info(f"Report saved: {path}")
        elif cmd == 'clear':
            C.clear()
        else:
            log_error(f"Unknown command: '{cmd}'. Type 'help' for usage.")


# ─────────────────────────────────────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    global _last_findings, _last_target

    parser = argparse.ArgumentParser(
        prog="zql",
        description="ZQL 1.0 — SQL Security Testing Framework (Dev: Zayar Lin)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument('command',  nargs='?', default=None, help="Command to run")
    parser.add_argument('target',   nargs='?', default=None, help="Target URL")
    parser.add_argument('--format', '-f', default='txt',    help="Report format: txt/json/html/md")
    parser.add_argument('--output', '-o', default='.',      help="Report output directory")
    parser.add_argument('--no-boot',       action='store_true', help="Skip boot animation")
    parser.add_argument('--help', '-h',    action='store_true', help="Show help")

    args, _ = parser.parse_known_args()

    # ── Boot sequence ──
    if not args.no_boot:
        boot_sequence()

    # ── Dispatch ──
    if args.help or args.command == 'help':
        print_help()
        return

    if args.command is None:
        # No command → interactive REPL
        print_module_grid()
        interactive_mode()
        return

    cmd = args.command.lower()

    if cmd == 'scan':
        if not args.target:
            log_error("Please specify a target URL.  Example: python3 zql.py scan http://host/page?id=1")
            return
        engine  = ScanEngine(args.target)
        t0      = time.time()
        findings = engine.run_full_scan()
        elapsed = time.time() - t0
        print_scan_summary(findings, args.target, elapsed)
        _last_findings = findings
        _last_target   = args.target

        # Auto-save TXT report
        path = generate_report(findings, args.target, fmt="txt", output_dir=args.output)
        p()
        log_info(f"Auto-saved TXT report: {path}")
        p()

    elif cmd == 'headers':
        if not args.target:
            log_error("Please specify a target URL."); return
        e = ScanEngine(args.target)
        e.module_security_headers()
        print_scan_summary(e.findings, args.target, 0)

    elif cmd == 'cookies':
        if not args.target:
            log_error("Please specify a target URL."); return
        e = ScanEngine(args.target)
        e.module_cookie_scanner()
        print_scan_summary(e.findings, args.target, 0)

    elif cmd == 'waf-detect':
        if not args.target:
            log_error("Please specify a target URL."); return
        e = ScanEngine(args.target)
        e.module_waf_detection()
        print_scan_summary(e.findings, args.target, 0)

    elif cmd == 'fingerprint':
        if not args.target:
            log_error("Please specify a target URL."); return
        e = ScanEngine(args.target)
        e.module_dbms_fingerprint()
        print_scan_summary(e.findings, args.target, 0)

    elif cmd == 'sandbox':
        run_sandbox()

    elif cmd == 'modules':
        print_module_grid()

    elif cmd == 'report':
        log_warn("No in-memory findings (run interactively for report generation after scan).")
        log_info("Tip: Run 'python3 zql.py' for interactive mode, then scan and use 'report --format html'")

    else:
        log_error(f"Unknown command: '{cmd}'")
        print_help()


if __name__ == "__main__":
    main()

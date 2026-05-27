ZQL 1.0
SQL Security Testing Framework

ZQL 1.0 is a cinematic cyberpunk-style SQL security auditing framework designed for:
Authorized penetration testing
Local lab environments
CTF challenges
OWASP training platforms
Educational cybersecurity research

Features

URL Parameter Analyzer
SQL Error Detection
Boolean-Based Blind SQLi Detection
WAF Detection
DBMS Fingerprinting
Security Header Inspection
Cookie Security Scanner
Response Difference Analyzer
Interactive Terminal Mode
HTML / JSON / Markdown Reporting
Training Sandbox Mode
Cyberpunk Animated CLI Interface

Installation

git clone https://github.com/zayarlin/zql.git cd zql python3 zql.py 

Requirements

Python 3.10+
Linux / macOS / Windows
Internet Connection

Usage

Interactive Mode
python3 zql.py 

Full Scan
python3 zql.py scan http://localhost/sqli-labs/Less-1/?id=1 

Header Inspection
python3 zql.py headers https://example.com 

Cookie Analysis
python3 zql.py cookies https://example.com 

WAF Detection
python3 zql.py waf-detect https://example.com 

DBMS Fingerprinting
python3 zql.py fingerprint https://example.com 

Sandbox Mode
python3 zql.py sandbox 

Report Formats

ZQL supports:
TXT
JSON
HTML
Markdown
Generate reports:
python3 zql.py report --format html 

Supported Databases

MySQL
PostgreSQL
MSSQL
SQLite
Oracle
MariaDB

Ethical Use Warning

ZQL is strictly intended for:
Authorized security testing
Educational labs
Capture The Flag (CTF) environments
Research purposes
Unauthorized usage against systems you do not own or have permission to test is illegal.

Developer - Zayar Lin
Version - ZQL 1.0

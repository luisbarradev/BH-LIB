from __future__ import annotations
import re
from datetime import datetime, timedelta
from http.cookiejar import Cookie

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


_JS_REDIRECT_RE = re.compile(r'location.replace(["\\]["\\][^"]+["\\]["\\])', re.I)

def set_cookie(
    session: requests.Session,
    name: str,
    value: str,
    domain: str = ".sii.cl",
    path: str = "/",
    secure: bool = True,
    max_age_hours: int = 2,
) -> None:
    expires = datetime.utcnow() + timedelta(hours=max_age_hours)
    c = Cookie(
        version=0, name=name, value=value, port=None, port_specified=False,
        domain=domain, domain_specified=True, domain_initial_dot=domain.startswith("."),
        path=path, path_specified=True, secure=secure, expires=int(expires.timestamp()),
        discard=False, comment=None, comment_url=None, rest={}, rfc2109=False,
    )
    session.cookies.set_cookie(c)


def format_rut(rut_num: str, dv: str) -> str:
    digits = re.sub(r"\D", "", rut_num)
    parts = []
    while digits:
        parts.append(digits[-3:])
        digits = digits[:-3]
    formatted = ".".join(reversed(parts))
    return f"{formatted}-{dv.upper()}"


def follow_js_redirect_or_home(
    resp: requests.Response,
    session: requests.Session,
    fallback_home: str = "https://misiir.sii.cl/cgi_misii/siihome.cgi",
) -> requests.Response:
    text = resp.text or ""
    m = _JS_REDIRECT_RE.search(text)
    if m:
        js_url = m.group(1)
        set_cookie(
            session,
            "NETSCAPE_LIVEWIRE.locexp",
            (datetime.utcnow() + timedelta(hours=2)).strftime("%a, %d %b %Y %H:%M:%S GMT"),
        )
        return session.get(js_url, timeout=15)
    return session.get(fallback_home, timeout=15)

def looks_like_home(resp: requests.Response) -> bool:
    if "siihome.cgi" in (resp.url or ""):
        return True
    text = (resp.text or "").lower()
    markers = ("mi sii", "servicios online", "situación tributaria", "clave tributaria")
    return any(m in text for m in markers)

def build_session_with_retries() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=3, backoff_factor=0.6, status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "HEAD"]),
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

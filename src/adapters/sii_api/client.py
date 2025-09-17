
from __future__ import annotations
import re
from typing import Dict

import requests

from application.ports.auth_port import AuthenticationPort
from domain.exceptions import AuthError
from domain.models import Credentials
from adapters.sii_api.utils import (
    follow_js_redirect_or_home,
    format_rut,
    looks_like_home,
)


class SiiPasswordAuthAdapter(AuthenticationPort):
    """
    Adapter that implements authentication by RUT and password in the SII.
    """
    POST_URL: str = "https://zeusr.sii.cl/cgi_AUT2000/CAutInicio.cgi"
    REFERER: str = (
        "https://zeusr.sii.cl//AUT2000/InicioAutenticacion/"
        "IngresoRutClave.html?https://misiir.sii.cl/cgi_misii/siihome.cgi"
    )

    def __init__(self, creds: Credentials):
        self._creds = creds
        self._validate_credentials()

    def _validate_credentials(self) -> None:
        if not (self._creds.rut_num and re.match(r"^[0-9]+$", self._creds.rut_num)):
            raise AuthError("Invalid numeric RUT.")
        if not (self._creds.dv and self._creds.dv.strip()):
            raise AuthError("DV (check digit) cannot be empty.")
        if not self._creds.password:
            raise AuthError("Password cannot be empty.")
        self._creds.dv = self._creds.dv.strip().upper()

    def _payload(self) -> Dict[str, str]:
        return {
            "rut": self._creds.rut_num,
            "dv": self._creds.dv,
            "referencia": "https://misiir.sii.cl/cgi_misii/siihome.cgi",
            "411": "",
            "rutcntr": format_rut(self._creds.rut_num, self._creds.dv),
            "clave": self._creds.password,
        }

    def _prepare_session(self, session: requests.Session) -> None:
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es-CL;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://zeusr.sii.cl",
            "Referer": self.REFERER,
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "DNT": "1", "Sec-GPC": "1", "Priority": "u=0, i",
        })
        if self._creds.initial_cookies:
            session.cookies.update(self._creds.initial_cookies)

    def login(self, session: requests.Session) -> None:
        self._prepare_session(session)

        try:
            session.get(self.REFERER, timeout=15)
        except requests.RequestException:
            pass  # Not fatal

        data = self._payload()
        try:
            resp = session.post(
                self.POST_URL, data=data, timeout=20, allow_redirects=True
            )
        except requests.RequestException as e:
            raise AuthError(f"Network error during SII authentication: {e}") from e

        if not resp.ok:
            raise AuthError(f"SII login failed with status {resp.status_code}")

        try:
            final = follow_js_redirect_or_home(resp, session)
        except requests.RequestException as e:
            raise AuthError(f"Error following redirect to home: {e}") from e

        if not final.ok:
            raise AuthError(f"Could not load Mi SII home page (status {final.status_code}).")

        if not looks_like_home(final):
            snippet = (final.text or "")[:600].replace("\n", " ")
            raise AuthError(
                "Could not validate session in SII after login (unexpected home page). "
                f"URL={final.url!r} HTML={snippet!r}"
            )

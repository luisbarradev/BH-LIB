
from __future__ import annotations
from typing import TYPE_CHECKING

from domain.exceptions import AuthError

if TYPE_CHECKING:
    import requests
    from application.ports.auth_port import AuthenticationPort
    from domain.models import Credentials


class SiiService:
    """Application service to orchestrate operations with the SII."""

    def __init__(self, auth_adapter: AuthenticationPort, session: requests.Session, creds: Credentials):
        self._auth_adapter = auth_adapter
        self._session = session
        self._creds = creds

    def login(self) -> None:
        """Performs login using the authentication adapter."""
        self._auth_adapter.login(self._session)

    def get_home_html(self) -> str:
        """Gets the HTML of the Mi SII home page. Requires prior login."""
        if not self._session:
            raise AuthError("Login is required to get the home page.")

        try:
            resp = self._session.get("https://misiir.sii.cl/cgi_misii/siihome.cgi", timeout=15)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            raise AuthError(f"Error getting home HTML: {e}") from e

    def get_annual_report_html(self, year: int) -> str:
        """Gets the annual report of issued fee invoices."""
        if not self._session:
            raise AuthError("Login is required to get the invoices.")

        url = "https://loa.sii.cl/cgi_IMT/TMBCOC_InformeAnualBhe.cgi"
        params = {
            "rut_arrastre": self._creds.rut_num,
            "dv_arrastre": self._creds.dv,
            "cbanoinformeanual": year,
        }

        try:
            resp = self._session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            raise AuthError(f"Error getting the annual report: {e}") from e

    def get_monthly_report_html(self, year: int, month: int) -> str:
        """Gets the monthly report of issued fee invoices."""
        if not self._session:
            raise AuthError("Login is required to get the invoices.")

        url = "https://loa.sii.cl/cgi_IMT/TMBCOC_InformeMensualBhe.cgi"
        params = {
            "cbanoinformemensual": year,
            "cbmesinformemensual": f"{month:02d}",
            "dv_arrastre": self._creds.dv,
            "pagina_solicitada": 0,
            "rut_arrastre": self._creds.rut_num,
        }

        try:
            resp = self._session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            raise AuthError(f"Error getting the monthly report: {e}") from e

    def download_invoice_pdf(self, barcode: str) -> bytes:
        """Downloads the PDF of a specific invoice."""
        if not self._session:
            raise AuthError("Login is required to download the invoice.")

        url = "https://loa.sii.cl/cgi_IMT/TMBCOT_ConsultaBoletaPdf.cgi"
        params = {
            "txt_codigobarras": barcode,
            "veroriginal": "si",
            "origen": "PROPIOS",
            "enviar": "si",
        }

        try:
            resp = self._session.get(url, params=params, timeout=20)
            resp.raise_for_status()
            if 'application/pdf' not in resp.headers.get('Content-Type', ''):
                raise AuthError("The response is not a PDF. The session may have expired.")
            return resp.content
        except Exception as e:
            raise AuthError(f"Error downloading the invoice PDF: {e}") from e

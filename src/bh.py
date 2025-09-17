
from typing import Optional, Union
import requests
from adapters.sii_api.client import SiiPasswordAuthAdapter
from adapters.sii_api.utils import build_session_with_retries
from application.services.js_parsing_service import JsParsingService
from application.services.parsing_service import ParsingService
from application.services.sii_service import SiiService
from domain.models import Credentials, AnnualReport, MonthlyReport

class BH:
    """Facade to interact with the SII Fee Invoices services."""

    def __init__(self, rut: str, password: str, session: Optional[requests.Session] = None):
        """
        Initializes the Facade, performs login, and configures the services.

        Args:
            rut: Taxpayer RUT (e.g., "12345678-9").
            password: Tax password.
            session: (Optional) Requests session to reuse.
        """
        rut_num, dv = self._normalize_rut(rut)
        self._credentials = Credentials(rut_num=rut_num, dv=dv, password=password)
        self._session = session or build_session_with_retries()
        
        # Service composition
        auth_adapter = SiiPasswordAuthAdapter(creds=self._credentials)
        js_parser = JsParsingService()
        self._parsing_service = ParsingService(js_parser=js_parser)
        self._sii_service = SiiService(
            auth_adapter=auth_adapter, 
            session=self._session, 
            creds=self._credentials
        )

        # Inject the service into the parser so models can use it
        self._parsing_service.set_sii_service(self._sii_service)

        # Perform login on initialization
        self._sii_service.login()

    def _normalize_rut(self, rut: str) -> tuple[str, str]:
        """Normalizes and validates a RUT string to (number, dv)."""
        if '-' not in rut:
            raise ValueError("RUT must be in the format 12345678-9")
        num, dv = rut.rsplit('-', 1)
        num = num.replace('.', '')
        if not num.isdigit() or not dv:
            raise ValueError("Invalid RUT.")
        return num, dv

    def get_issued_invoices(self, year: int, month: Optional[int] = None) -> Union[AnnualReport, MonthlyReport]:
        """
        Gets the report of issued invoices, either annual or monthly.

        Args:
            year: Year to consult.
            month: (Optional) Month to consult. If omitted, returns the annual report.

        Returns:
            AnnualReport if month is None, otherwise MonthlyReport.
        """
        if month:
            html = self._sii_service.get_monthly_report_html(year, month)
            return self._parsing_service.parse_monthly_report_from_html(html)
        else:
            html = self._sii_service.get_annual_report_html(year)
            return self._parsing_service.parse_annual_report_from_html(html)

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List, TYPE_CHECKING
import base64

if TYPE_CHECKING:
    from application.services.sii_service import SiiService

@dataclass
class Credentials:
    """Authentication credentials container."""
    rut_num: str
    dv: str
    password: str
    initial_cookies: Optional[Dict[str, str]] = None

@dataclass
class MonthlyInvoiceSummary:
    """Represents the summary of invoices for a specific month."""
    month: str
    gross_fee: int = 0
    third_party_withholding: int = 0
    taxpayer_withholding: int = 0
    start_folio: Optional[int] = None
    end_folio: Optional[int] = None
    issued_count: int = 0
    voided_count: int = 0
    net_amount: int = 0

@dataclass
class AnnualTotals:
    """Represents the annual totals of the report."""
    gross_fee: int = 0
    third_party_withholding: int = 0
    taxpayer_withholding: int = 0
    start_folio_annual: Optional[int] = None
    end_folio_annual: Optional[int] = None
    issued_count: int = 0
    voided_count: int = 0
    net_amount: int = 0

@dataclass
class AnnualReport:
    """Contains the complete annual report of fee invoices."""
    taxpayer_name: str
    rut: str
    year: int
    is_professional_partnership: bool
    totals: AnnualTotals
    months: List[MonthlyInvoiceSummary] = field(default_factory=list)

@dataclass
class PDF:
    """Container for a downloaded PDF file."""
    _content: bytes

    def get_bytes(self) -> bytes:
        """Returns the PDF content in bytes."""
        return self._content

    def get_base64(self) -> str:
        """Returns the PDF content in base64 format."""
        return base64.b64encode(self._content).decode('ascii')

    def save(self, filepath: str) -> None:
        """Saves the PDF to a file."""
        with open(filepath, 'wb') as f:
            f.write(self._content)

@dataclass
class InvoiceDetail:
    """Represents the details of an issued fee invoice."""
    number: int
    issuer: str
    issue_date: str
    recipient_rut: str
    recipient_name: str
    total_fee: int
    issuer_withholding: int
    recipient_withholding: int
    net_amount: int
    status: str
    barcode: str
    void_date: Optional[str] = None
    _sii_service: Optional[SiiService] = field(default=None, repr=False, compare=False)

    def get_pdf(self) -> PDF:
        """Downloads the PDF of this invoice."""
        if not self._sii_service:
            raise RuntimeError("SII service is not available to download the PDF.")
        pdf_bytes = self._sii_service.download_invoice_pdf(self.barcode)
        return PDF(pdf_bytes)

@dataclass
class MonthlyReport:
    """Contains the detailed monthly report of invoices."""
    taxpayer_name: str
    rut: str
    year: int
    month: int
    total_invoices: int
    total_fees: int
    total_issuer_withholding: int
    total_recipient_withholding: int
    total_net_amount: int
    invoices: List[InvoiceDetail] = field(default_factory=list)
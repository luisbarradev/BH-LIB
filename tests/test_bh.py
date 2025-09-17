
import pytest
from unittest.mock import MagicMock, patch
from src.bh import BH
from src.domain.models import AnnualReport, MonthlyReport, InvoiceDetail, PDF, AnnualTotals

@pytest.fixture
def mock_sii_service():
    """Pytest fixture for a mocked SiiService."""
    return MagicMock()

@pytest.fixture
def mock_parsing_service():
    """Pytest fixture for a mocked ParsingService."""
    return MagicMock()

@patch('src.bh.build_session_with_retries')
@patch('src.bh.SiiPasswordAuthAdapter')
@patch('src.bh.JsParsingService')
@patch('src.bh.ParsingService')
@patch('src.bh.SiiService')
def test_bh_facade(
    MockSiiService, MockParsingService, MockJsParsingService, 
    MockSiiPasswordAuthAdapter, mock_build_session
):
    """Tests the BH facade."""
    # Arrange
    mock_sii_service_instance = MockSiiService.return_value
    mock_parsing_service_instance = MockParsingService.return_value

    bh = BH(rut="12345678-9", password="password")
    bh._sii_service = mock_sii_service_instance
    bh._parsing_service = mock_parsing_service_instance

    # Test get_issued_invoices (annual)
    mock_sii_service_instance.get_annual_report_html.return_value = "<html></html>"
    mock_parsing_service_instance.parse_annual_report_from_html.return_value = AnnualReport(
        taxpayer_name="Test User", rut="12345678-9", year=2025, 
        is_professional_partnership=False, totals=AnnualTotals(), months=[]
    )

    annual_report = bh.get_issued_invoices(year=2025)

    assert isinstance(annual_report, AnnualReport)
    mock_sii_service_instance.get_annual_report_html.assert_called_once_with(2025)
    mock_parsing_service_instance.parse_annual_report_from_html.assert_called_once_with("<html></html>")

    # Test get_issued_invoices (monthly)
    mock_sii_service_instance.get_monthly_report_html.return_value = "<html></html>"
    mock_parsing_service_instance.parse_monthly_report_from_html.return_value = MonthlyReport(
        taxpayer_name="Test User", rut="12345678-9", year=2025, month=1, 
        total_invoices=1, total_fees=1000, total_issuer_withholding=100, 
        total_recipient_withholding=0, total_net_amount=900, invoices=[]
    )

    monthly_report = bh.get_issued_invoices(year=2025, month=1)

    assert isinstance(monthly_report, MonthlyReport)
    mock_sii_service_instance.get_monthly_report_html.assert_called_once_with(2025, 1)
    mock_parsing_service_instance.parse_monthly_report_from_html.assert_called_once_with("<html></html>")

    # Test get_pdf on InvoiceDetail
    invoice = InvoiceDetail(
        number=1, issuer="Test User", issue_date="01/01/2025", recipient_rut="98765432-1",
        recipient_name="Test Recipient", total_fee=1000, issuer_withholding=100, 
        recipient_withholding=0, net_amount=900, status="Vigente", barcode="barcode",
        _sii_service=mock_sii_service_instance
    )
    mock_sii_service_instance.download_invoice_pdf.return_value = b"pdf_content"

    pdf = invoice.get_pdf()

    assert isinstance(pdf, PDF)
    assert pdf.get_bytes() == b"pdf_content"
    mock_sii_service_instance.download_invoice_pdf.assert_called_once_with("barcode")

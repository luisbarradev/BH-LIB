
import pytest
from unittest.mock import MagicMock
from src.application.services.sii_service import SiiService
from src.domain.models import Credentials

@pytest.fixture
def mock_session():
    """Pytest fixture for a mocked requests.Session."""
    return MagicMock()

@pytest.fixture
def sii_service(mock_session):
    """Pytest fixture for a SiiService instance with a mocked session."""
    credentials = Credentials(rut_num="12345678", dv="9", password="password")
    auth_adapter = MagicMock()
    return SiiService(auth_adapter, mock_session, credentials)

def test_get_annual_report_html(sii_service: SiiService, mock_session):
    """Tests the get_annual_report_html method."""
    mock_session.get.return_value.ok = True
    mock_session.get.return_value.text = "<html></html>"

    html = sii_service.get_annual_report_html(2025)

    assert html == "<html></html>"
    mock_session.get.assert_called_once()

def test_get_monthly_report_html(sii_service: SiiService, mock_session):
    """Tests the get_monthly_report_html method."""
    mock_session.get.return_value.ok = True
    mock_session.get.return_value.text = "<html></html>"

    html = sii_service.get_monthly_report_html(2025, 1)

    assert html == "<html></html>"
    mock_session.get.assert_called_once()

def test_download_invoice_pdf(sii_service: SiiService, mock_session):
    """Tests the download_invoice_pdf method."""
    mock_session.get.return_value.ok = True
    mock_session.get.return_value.headers = {'Content-Type': 'application/pdf'}
    mock_session.get.return_value.content = b"pdf_content"

    pdf_content = sii_service.download_invoice_pdf("barcode")

    assert pdf_content == b"pdf_content"
    mock_session.get.assert_called_once()

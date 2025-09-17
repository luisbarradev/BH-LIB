
import pytest
from src.application.services.js_parsing_service import JsParsingService
from src.application.services.parsing_service import ParsingService

@pytest.fixture
def parsing_service():
    """Pytest fixture to provide a ParsingService instance."""
    js_parser = JsParsingService()
    return ParsingService(js_parser)


def test_parse_annual_report(parsing_service: ParsingService):
    """Tests parsing of the annual report from a local HTML file."""
    with open("tests/fixtures/anual.html", "r", encoding="iso-8859-1") as f:
        html = f.read()

    report = parsing_service.parse_annual_report_from_html(html)

    assert report.taxpayer_name == "LUIS FRANCISCO BARRA SANDOVAL"
    assert report.year == 2025
    assert not report.is_professional_partnership
    assert report.totals.issued_count == 8
    assert report.months[0].issued_count == 1

def test_parse_monthly_report(parsing_service: ParsingService):
    """Tests parsing of the monthly report from a local HTML file."""
    with open("tests/fixtures/mensual.html", "r", encoding="iso-8859-1") as f:
        html = f.read()

    report = parsing_service.parse_monthly_report_from_html(html)

    assert report.taxpayer_name == "LUIS FRANCISCO BARRA SANDOVAL"
    assert report.year == 2025
    assert report.month == 1
    assert report.total_invoices == 1
    assert len(report.invoices) == 1

    invoice = report.invoices[0]
    assert invoice.number == 3
    assert invoice.recipient_name == "EMPRESA SPA"
    assert invoice.total_fee == 123244
    assert invoice.barcode == "12345678AAAAAAAAABB"

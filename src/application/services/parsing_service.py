
from __future__ import annotations
from typing import TYPE_CHECKING
from domain.models import (
    InvoiceDetail,
    MonthlyInvoiceSummary,
    AnnualReport,
    MonthlyReport,
    AnnualTotals
)
from application.services.js_parsing_service import JsParsingService

if TYPE_CHECKING:
    from application.services.sii_service import SiiService

class ParsingService:
    """Service to parse and transform invoice data."""

    def __init__(self, js_parser: JsParsingService):
        self._js_parser = js_parser
        self._sii_service: SiiService | None = None

    def set_sii_service(self, sii_service: SiiService) -> None:
        """Injects the SiiService so models can use it."""
        self._sii_service = sii_service

    def _safe_int(self, value: any, default: int = 0) -> int:
        """Safely converts a value to an integer."""
        if value is None or value == '':
            return default
        try:
            return int(str(value).replace('.', ''))
        except (ValueError, TypeError):
            return default

    def parse_annual_report_from_html(self, html: str) -> AnnualReport:
        """Parses the HTML to extract the complete annual report."""
        data = self._js_parser.parse_xml_values(html)
        
        totals = AnnualTotals(
            gross_fee=self._safe_int(data.get('tot1')),
            third_party_withholding=self._safe_int(data.get('tot2')),
            taxpayer_withholding=self._safe_int(data.get('tot3')),
            start_folio_annual=self._safe_int(data.get('tot4')) if data.get('tot4') else None,
            end_folio_annual=self._safe_int(data.get('tot5')) if data.get('tot5') else None,
            issued_count=self._safe_int(data.get('tot6')),
            voided_count=self._safe_int(data.get('tot7')),
            net_amount=self._safe_int(data.get('sumtot'))
        )

        months = []
        month_map = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
        for month_abbr in month_map:
            months.append(MonthlyInvoiceSummary(
                month=month_abbr.capitalize(),
                gross_fee=self._safe_int(data.get(f'{month_abbr}1')),
                third_party_withholding=self._safe_int(data.get(f'{month_abbr}2')),
                taxpayer_withholding=self._safe_int(data.get(f'{month_abbr}3')),
                start_folio=self._safe_int(data.get(f'{month_abbr}4')) if data.get(f'{month_abbr}4') else None,
                end_folio=self._safe_int(data.get(f'{month_abbr}5')) if data.get(f'{month_abbr}5') else None,
                issued_count=self._safe_int(data.get(f'{month_abbr}6')),
                voided_count=self._safe_int(data.get(f'{month_abbr}7')),
                net_amount=self._safe_int(data.get(f'sum{month_abbr}'))
            ))

        return AnnualReport(
            taxpayer_name=data.get('nombre_contribuyente', '').strip(),
            rut=f"{data.get('rut_arrastre', '')}-{data.get('dv_arrastre', '')}",
            year=self._safe_int(data.get('anio_consulta')),
            is_professional_partnership=data.get('es_sociedad_profesionales') == 'SI',
            totals=totals,
            months=months
        )

    def parse_monthly_report_from_html(self, html: str) -> MonthlyReport:
        """Parses the HTML to extract the detailed monthly report."""
        globals_data = self._js_parser.parse_informe_mensual_globals(html)
        invoices_data = self._js_parser.parse_arr_informe_mensual(html)

        invoices = []
        total_invoices = self._safe_int(globals_data.get('total_boletas'))
        for i in range(1, total_invoices + 1):
            invoices.append(InvoiceDetail(
                number=self._safe_int(invoices_data.get(f'nroboleta_{i}')),
                issuer=invoices_data.get(f'usuemisor_{i}', '').strip(),
                issue_date=invoices_data.get(f'fechaemision_{i}', ''),
                recipient_rut=f"{invoices_data.get(f'rutreceptor_{i}', '')}-{invoices_data.get(f'dvreceptor_{i}', '')}",
                recipient_name=invoices_data.get(f'nombrereceptor_{i}', '').strip(),
                total_fee=self._safe_int(invoices_data.get(f'totalhonorarios_{i}')),
                issuer_withholding=self._safe_int(invoices_data.get(f'retencion_emisor_{i}')),
                recipient_withholding=self._safe_int(invoices_data.get(f'retencion_receptor_{i}')),
                net_amount=self._safe_int(invoices_data.get(f'honorariosliquidos_{i}')),
                status=invoices_data.get(f'estado_{i}', ''),
                barcode=invoices_data.get(f'codigobarras_{i}', ''),
                void_date=invoices_data.get(f'fechaanulacion_{i}') if invoices_data.get(f'fechaanulacion_{i}', ' ').strip() else None,
                _sii_service=self._sii_service
            ))

        return MonthlyReport(
            taxpayer_name=globals_data.get('nombre_contribuyente', '').strip(),
            rut=f"{globals_data.get('rut_arrastre', '')}-{globals_data.get('dv_arrastre', '')}",
            year=self._safe_int(globals_data.get('anio_consulta')),
            month=self._safe_int(globals_data.get('mes_consulta')),
            total_invoices=total_invoices,
            total_fees=self._safe_int(globals_data.get('suma_honorarios')),
            total_issuer_withholding=self._safe_int(globals_data.get('suma_retencion_emisor')),
            total_recipient_withholding=self._safe_int(globals_data.get('suma_retencion_receptor')),
            total_net_amount=self._safe_int(globals_data.get('suma_liquido')),
            invoices=invoices
        )

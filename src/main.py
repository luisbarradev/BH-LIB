import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import json
from dataclasses import is_dataclass, asdict
from bh import BH
from domain.exceptions import AuthError

def json_default(obj):
    if is_dataclass(obj):
        return asdict(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def main() -> None:
    """
    Entry point and demonstration of the BH library.
    """
    load_dotenv()  # Load environment variables from .env

    rut_num = os.getenv("SII_RUT_NUM", "").strip()
    rut_dv = os.getenv("SII_RUT_DV", "").strip()
    password = os.getenv("SII_CLAVE", "").strip()

    rut_completo = f"{rut_num}-{rut_dv}"

    if not (rut_num and rut_dv and password):
        print("Error: Missing environment variables: SII_RUT_NUM, SII_RUT_DV, SII_CLAVE", file=sys.stderr)
        sys.exit(1)

    try:
        # 1. Initialize the Facade (performs login automatically)
        print(f"Logging in for RUT {rut_completo}...")
        bh = BH(rut=rut_completo, password=password)
        print("✅ Login successful.")

        # 2. Get the annual report of issued invoices
        year = datetime.now().year
        print(f"\nGetting annual report for the year {year}...")
        annual_report = bh.get_issued_invoices(year=year)
        # print(f"-> Found {annual_report.totals.issued_count} issued invoices in the year.")
        print("Annual Report (JSON):")
        print(json.dumps(annual_report, indent=2, default=json_default))

        # 3. Get the monthly report for a specific month (e.g., January)
        month_to_check = 1
        print(f"\nGetting details for month {month_to_check}/{year}...")
        monthly_report = bh.get_issued_invoices(year=year, month=month_to_check)
        # print(f"-> Found {monthly_report.total_invoices} invoices in the month.")
        print("Monthly Report (JSON):")
        print(json.dumps(monthly_report, indent=2, default=json_default))

        # 4. Download the PDF of the first invoice of the month (if it exists)
        if monthly_report.invoices:
            first_invoice = monthly_report.invoices[0]
            print(f"\nDownloading PDF for invoice N°{first_invoice.number}...")
            
            pdf = first_invoice.get_pdf()
            
            # Save the PDF to a file
            filename = f"invoice_{first_invoice.number}.pdf"
            pdf.save(filename)
            print(f"✅ PDF saved as '{filename}'")

            # Optional: Get the content in other formats
            pdf_bytes = pdf.get_bytes()
            pdf_base64 = pdf.get_base64()
            # print(f"-> The PDF is also available in bytes (len: {len(pdf_bytes)}) and base64 (len: {len(pdf_base64)}).")
        else:
            print(f"\nNo invoices in month {month_to_check} to download.")

    except AuthError as e:
        print(f"❌ Authentication or service error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

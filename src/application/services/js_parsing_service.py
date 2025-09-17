
import re
import json
import quickjs
from bs4 import BeautifulSoup

class JsParsingService:
    """Servicio para parsear y ejecutar JavaScript extraído del HTML."""

    def _execute_js(self, html: str, array_name: str) -> dict:
        """Motor de ejecución de JS para extraer un objeto desde el HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        scripts = soup.find_all('script')
        js_code = None
        for s in scripts:
            if s.string and f'var {array_name} = new Array();' in s.string:
                js_code = s.string
                break

        if not js_code:
            raise ValueError(f"No se encontró el script con `{array_name}` en el HTML.")

        # Reemplaza la creación del Array por un objeto literal de JS
        js_code = js_code.replace(f'var {array_name} = new Array();', f'var {array_name} = {{}};')
        js_code = re.sub(r'formatMiles\(([^,]+),[^)]+\)', r'\1', js_code)

        js_to_execute = f"{js_code}\nJSON.stringify({array_name});"

        context = quickjs.Context()
        result_json = context.eval(js_to_execute)
        return json.loads(result_json)

    def parse_xml_values(self, html: str) -> dict:
        """Extrae el objeto `xml_values` del HTML del informe anual."""
        return self._execute_js(html, 'xml_values')

    def parse_arr_informe_mensual(self, html: str) -> dict:
        """Extrae el objeto `arr_informe_mensual` del HTML del informe mensual."""
        return self._execute_js(html, 'arr_informe_mensual')

    def parse_informe_mensual_globals(self, html: str) -> dict:
        """Extrae `xml_values` del informe mensual, que contiene los totales."""
        return self._execute_js(html, 'xml_values')

import base64
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class OseResponse:
    accepted: bool
    cdr_content: str
    response_code: str
    description: str


class OseClientInterface(ABC):
    @abstractmethod
    def send_document(
        self, ruc: str, full_number: str, xml_content: str
    ) -> OseResponse: ...


class MockOseClient(OseClientInterface):
    """Used in development and tests — always returns accepted."""

    def send_document(
        self, ruc: str, full_number: str, xml_content: str
    ) -> OseResponse:
        fake_cdr = base64.b64encode(f"CDR-MOCK-{full_number}".encode()).decode()
        return OseResponse(
            accepted=True,
            cdr_content=fake_cdr,
            response_code="0",
            description=f"La Factura numero {full_number}, ha sido aceptada",
        )


class NubefactOseClient(OseClientInterface):
    """
    Stub for Nubefact homologation/production OSE integration.
    Nubefact free homologation: https://www.nubefact.com/integracion-sunat/
    """

    def __init__(self, token: str, homologation: bool = True):
        self.token = token
        self.base_url = (
            "https://demo.factura.com.pe/api/v1"
            if homologation
            else "https://www.factura.com.pe/api/v1"
        )

    def send_document(
        self, ruc: str, full_number: str, xml_content: str
    ) -> OseResponse:
        import requests

        xml_bytes = xml_content.encode("utf-8")
        xml_b64 = base64.b64encode(xml_bytes).decode()
        payload = {
            "operacion": "generar_comprobante",
            "tipo_de_comprobante": 1,
            "serie": full_number.split("-")[0],
            "numero": int(full_number.split("-")[1]),
            "archivo_xml": xml_b64,
        }
        headers = {
            "Authorization": f'Token token="{self.token}"',
            "Content-Type": "application/json",
        }
        resp = requests.post(
            f"{self.base_url}/invoices",
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        accepted = data.get("aceptada_por_sunat", False)
        return OseResponse(
            accepted=accepted,
            cdr_content=data.get("cdr", ""),
            response_code=str(data.get("sunat_description_code", "")),
            description=data.get("sunat_description", ""),
        )


def get_ose_client() -> OseClientInterface:
    from django.conf import settings

    provider = getattr(settings, "OSE_PROVIDER", "mock")
    if provider == "nubefact":
        token = getattr(settings, "NUBEFACT_TOKEN", "")
        homologation = getattr(settings, "NUBEFACT_HOMOLOGATION", True)
        return NubefactOseClient(token=token, homologation=homologation)
    return MockOseClient()

import xml.etree.ElementTree as ET
from xml.dom import minidom
from decimal import Decimal

# UBL 2.1 namespace URIs
NS_INV = 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
NS_CAC = 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
NS_CBC = 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
NS_EXT = 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2'

# SUNAT document type codes
DOC_TYPE_CODES = {
    'boleta': '03',
    'factura': '01',
}

# Customer document scheme IDs
CUSTOMER_SCHEME_IDS = {
    'DNI': '1',
    'RUC': '6',
    'CE': '4',
}


def _register_namespaces():
    ET.register_namespace('', NS_INV)
    ET.register_namespace('cac', NS_CAC)
    ET.register_namespace('cbc', NS_CBC)
    ET.register_namespace('ext', NS_EXT)


def _sub(parent, ns, tag, text=None, **attribs):
    elem = ET.SubElement(parent, f'{{{ns}}}{tag}', attribs)
    if text is not None:
        elem.text = str(text)
    return elem


def build_invoice_xml(
    full_number: str,
    document_type: str,
    issue_date: str,
    company_ruc: str,
    company_name: str,
    company_address: str,
    customer_name: str,
    customer_document_type: str,
    customer_document_number: str,
    subtotal: Decimal,
    tax: Decimal,
    discount: Decimal,
    total: Decimal,
    items: list[dict],
) -> str:
    """
    Builds a UBL 2.1 Invoice XML compliant with SUNAT Peru specifications.
    items: list of dicts with keys: description, quantity, unit_price, subtotal, tax
    """
    _register_namespaces()

    root = ET.Element(f'{{{NS_INV}}}Invoice')

    # UBL Extensions (placeholder for digital signature)
    ext_exts = _sub(root, NS_EXT, 'UBLExtensions')
    ext_ext = _sub(ext_exts, NS_EXT, 'UBLExtension')
    _sub(ext_ext, NS_EXT, 'ExtensionContent')

    _sub(root, NS_CBC, 'UBLVersionID', '2.1')
    _sub(root, NS_CBC, 'CustomizationID', '2.0')
    _sub(root, NS_CBC, 'ID', full_number)
    _sub(root, NS_CBC, 'IssueDate', issue_date)
    _sub(root, NS_CBC, 'InvoiceTypeCode', DOC_TYPE_CODES[document_type], listID='0101')
    _sub(root, NS_CBC, 'DocumentCurrencyCode', 'PEN')

    # Signature reference
    sig = _sub(root, NS_CAC, 'Signature')
    _sub(sig, NS_CBC, 'ID', 'SignatureSP')
    sig_party = _sub(sig, NS_CAC, 'SignatoryParty')
    sig_party_id = _sub(sig_party, NS_CAC, 'PartyIdentification')
    _sub(sig_party_id, NS_CBC, 'ID', company_ruc)

    # Supplier (company)
    supplier = _sub(root, NS_CAC, 'AccountingSupplierParty')
    supplier_party = _sub(supplier, NS_CAC, 'Party')
    supplier_id_block = _sub(supplier_party, NS_CAC, 'PartyIdentification')
    _sub(supplier_id_block, NS_CBC, 'ID', company_ruc, schemeID='6')
    supplier_name_block = _sub(supplier_party, NS_CAC, 'PartyName')
    _sub(supplier_name_block, NS_CBC, 'Name', company_name)
    supplier_legal = _sub(supplier_party, NS_CAC, 'PartyLegalEntity')
    _sub(supplier_legal, NS_CBC, 'RegistrationName', company_name)
    supplier_addr = _sub(supplier_legal, NS_CAC, 'RegistrationAddress')
    _sub(supplier_addr, NS_CBC, 'AddressLine')
    _sub(supplier_addr, NS_CBC, 'Line', company_address)

    # Customer
    customer = _sub(root, NS_CAC, 'AccountingCustomerParty')
    customer_party = _sub(customer, NS_CAC, 'Party')
    customer_id_block = _sub(customer_party, NS_CAC, 'PartyIdentification')
    scheme_id = CUSTOMER_SCHEME_IDS.get(customer_document_type, '1')
    _sub(customer_id_block, NS_CBC, 'ID', customer_document_number, schemeID=scheme_id)
    customer_legal = _sub(customer_party, NS_CAC, 'PartyLegalEntity')
    _sub(customer_legal, NS_CBC, 'RegistrationName', customer_name)

    # Tax total
    tax_total = _sub(root, NS_CAC, 'TaxTotal')
    _sub(tax_total, NS_CBC, 'TaxAmount', str(tax), currencyID='PEN')
    tax_sub = _sub(tax_total, NS_CAC, 'TaxSubtotal')
    _sub(tax_sub, NS_CBC, 'TaxableAmount', str(subtotal), currencyID='PEN')
    _sub(tax_sub, NS_CBC, 'TaxAmount', str(tax), currencyID='PEN')
    tax_cat = _sub(tax_sub, NS_CAC, 'TaxCategory')
    tax_scheme = _sub(tax_cat, NS_CAC, 'TaxScheme')
    _sub(tax_scheme, NS_CBC, 'ID', '1000')
    _sub(tax_scheme, NS_CBC, 'Name', 'IGV')
    _sub(tax_scheme, NS_CBC, 'TaxTypeCode', 'VAT')

    # Monetary totals
    monetary = _sub(root, NS_CAC, 'LegalMonetaryTotal')
    _sub(monetary, NS_CBC, 'LineExtensionAmount', str(subtotal), currencyID='PEN')
    _sub(monetary, NS_CBC, 'TaxExclusiveAmount', str(subtotal), currencyID='PEN')
    _sub(monetary, NS_CBC, 'TaxInclusiveAmount', str(subtotal + tax), currencyID='PEN')
    _sub(monetary, NS_CBC, 'AllowanceTotalAmount', str(discount), currencyID='PEN')
    _sub(monetary, NS_CBC, 'PayableAmount', str(total), currencyID='PEN')

    # Invoice lines
    for i, item in enumerate(items, start=1):
        line = _sub(root, NS_CAC, 'InvoiceLine')
        _sub(line, NS_CBC, 'ID', str(i))
        _sub(line, NS_CBC, 'InvoicedQuantity', str(item['quantity']), unitCode='NIU')
        _sub(line, NS_CBC, 'LineExtensionAmount', str(item['subtotal']), currencyID='PEN')

        line_tax = _sub(line, NS_CAC, 'TaxTotal')
        _sub(line_tax, NS_CBC, 'TaxAmount', str(item['tax']), currencyID='PEN')
        line_tax_sub = _sub(line_tax, NS_CAC, 'TaxSubtotal')
        _sub(line_tax_sub, NS_CBC, 'TaxableAmount', str(item['subtotal']), currencyID='PEN')
        _sub(line_tax_sub, NS_CBC, 'TaxAmount', str(item['tax']), currencyID='PEN')
        line_tax_cat = _sub(line_tax_sub, NS_CAC, 'TaxCategory')
        _sub(line_tax_cat, NS_CBC, 'Percent', '18.00')
        _sub(line_tax_cat, NS_CBC, 'TaxExemptionReasonCode', '10')
        line_tax_scheme = _sub(line_tax_cat, NS_CAC, 'TaxScheme')
        _sub(line_tax_scheme, NS_CBC, 'ID', '1000')
        _sub(line_tax_scheme, NS_CBC, 'Name', 'IGV')
        _sub(line_tax_scheme, NS_CBC, 'TaxTypeCode', 'VAT')

        line_item = _sub(line, NS_CAC, 'Item')
        _sub(line_item, NS_CBC, 'Description', item['description'])

        line_price = _sub(line, NS_CAC, 'Price')
        _sub(line_price, NS_CBC, 'PriceAmount', str(item['unit_price']), currencyID='PEN')

    raw_xml = ET.tostring(root, encoding='unicode', xml_declaration=False)
    pretty = minidom.parseString(raw_xml).toprettyxml(indent='  ', encoding=None)
    # Remove the XML declaration added by toprettyxml (we add our own)
    lines = pretty.split('\n')
    if lines[0].startswith('<?xml'):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return '\n'.join(lines)

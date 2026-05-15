import io
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_receipt_pdf(
    full_number: str,
    document_type: str,
    issue_date: str,
    company_name: str,
    company_ruc: str,
    company_address: str,
    customer_name: str,
    customer_document_type: str,
    customer_document_number: str,
    items: list[dict],
    subtotal: Decimal,
    tax: Decimal,
    discount: Decimal,
    total: Decimal,
) -> bytes:
    """Returns a PDF receipt as bytes using ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Heading1"], alignment=TA_CENTER, fontSize=14
    )
    center_style = ParagraphStyle(
        "center", parent=styles["Normal"], alignment=TA_CENTER
    )
    _right_style = ParagraphStyle("right", parent=styles["Normal"], alignment=TA_RIGHT)
    normal = styles["Normal"]

    doc_type_label = (
        "BOLETA DE VENTA ELECTRÓNICA"
        if document_type == "boleta"
        else "FACTURA ELECTRÓNICA"
    )

    story = []

    # Header
    story.append(Paragraph(company_name, title_style))
    story.append(Paragraph(f"RUC: {company_ruc}", center_style))
    story.append(Paragraph(company_address, center_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(doc_type_label, title_style))
    story.append(Paragraph(full_number, center_style))
    story.append(Paragraph(f"Fecha: {issue_date}", center_style))
    story.append(Spacer(1, 0.4 * cm))

    # Customer
    story.append(Paragraph(f"Cliente: {customer_name}", normal))
    story.append(
        Paragraph(f"{customer_document_type}: {customer_document_number}", normal)
    )
    story.append(Spacer(1, 0.4 * cm))

    # Items table
    header = [["Descripción", "Cant.", "P. Unit.", "Subtotal"]]
    rows = [
        [
            item["description"],
            str(item["quantity"]),
            f"S/ {item['unit_price']:.2f}",
            f"S/ {item['subtotal']:.2f}",
        ]
        for item in items
    ]
    table_data = header + rows
    table = Table(table_data, colWidths=[9 * cm, 2 * cm, 3 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#F1F5F9")],
                ),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.4 * cm))

    # Totals
    totals_data = [
        ["Subtotal (sin IGV):", f"S/ {subtotal:.2f}"],
        ["IGV (18%):", f"S/ {tax:.2f}"],
    ]
    if discount > Decimal("0"):
        totals_data.append(["Descuento:", f"- S/ {discount:.2f}"])
    totals_data.append(["TOTAL:", f"S/ {total:.2f}"])

    totals_table = Table(totals_data, colWidths=[13 * cm, 4 * cm])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(totals_table)
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Gracias por su compra.", center_style))

    doc.build(story)
    return buffer.getvalue()

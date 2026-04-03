#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(frozen=True)
class LineItem:
    name: str
    qty: int
    unit_price_mxn: Decimal
    link: str
    note: str = ""

    @property
    def total(self) -> Decimal:
        return self.unit_price_mxn * Decimal(self.qty)


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def _money(amount: Decimal) -> str:
    s = f"{amount:,.2f}"
    return f"${s} MXN"


def _link(label: str, url: str) -> str:
    safe_label = (
        label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").strip()
    )
    safe_url = url.replace("&", "&amp;").replace("<", "%3C").replace(">", "%3E").strip()
    return f'<link href="{safe_url}">{safe_label}</link>'


def _items_table(items: list[LineItem], styles) -> Table:
    body = styles["BodyText"]
    header = ParagraphStyle(
        "Header",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.white,
    )
    cell = ParagraphStyle(
        "Cell",
        parent=body,
        fontName="Helvetica",
        fontSize=9.5,
        leading=12,
    )
    cell_small = ParagraphStyle(
        "CellSmall",
        parent=cell,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#374151"),
    )

    rows = [
        [
            _p("Producto", header),
            _p("Cant.", header),
            _p("Precio", header),
            _p("Total", header),
        ]
    ]

    for it in items:
        title = _link(it.name, it.link)
        if it.note:
            title += "<br/>" + _p(it.note, cell_small).text
        rows.append(
            [
                _p(title, cell),
                _p(str(it.qty), cell),
                _p(_money(it.unit_price_mxn), cell),
                _p(_money(it.total), cell),
            ]
        )

    table = Table(rows, colWidths=[4.9 * inch, 0.55 * inch, 1.2 * inch, 1.2 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _sum(items: list[LineItem]) -> Decimal:
    return sum((it.total for it in items), Decimal("0"))


def build_pdf(output_pdf: Path) -> None:
    styles = getSampleStyleSheet()
    styles["Title"].fontName = "Helvetica-Bold"
    styles["Title"].fontSize = 18
    styles["Title"].leading = 22

    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
    )
    small = ParagraphStyle(
        "Small",
        parent=body,
        fontSize=8.8,
        leading=12,
        textColor=colors.HexColor("#374151"),
    )

    today = dt.date.today().strftime("%d/%m/%Y")

    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=LETTER,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Cotizacion Homelab (Cityshop)",
        author="SMARTCFO-AI",
    )

    infra: list[LineItem] = [
        LineItem(
            name="WD Red Pro 8TB (2do disco para RAID1 en QNAP)",
            qty=1,
            unit_price_mxn=Decimal("6359.00"),
            link="https://cityshop.mx/producto/disco-duro-interno-wd-red-pro-8tb-35-escritorio-sata3-6gbs-512mb-7200rpm-24x7-hotplug-nas-1-24-bahias",
            note="Clave para redundancia (con 1 disco NO hay espejo).",
        ),
        LineItem(
            name="Switch TP-Link SG3210X-M2 (8 puertos 2.5GbE + 2 SFP+ 10G)",
            qty=1,
            unit_price_mxn=Decimal("4159.00"),
            link="https://cityshop.mx/producto/switch-tp-link-sg3210x-m2-switch-administrable-8-puertos-25-gps-2-puerto-sfp-10gps-omada-sdn-puertos",
            note="Te deja listo para 2.5GbE (NAS) y crecer.",
        ),
        LineItem(
            name="PDU CyberPower CPS1215RM (1U, 10 salidas)",
            qty=1,
            unit_price_mxn=Decimal("1329.00"),
            link="https://cityshop.mx/producto/pdu-cyberpower-cps1215rm-120-v",
            note="Se conecta a la UPS y distribuye energia en el rack.",
        ),
        LineItem(
            name="Panel de parcheo Cat6 24 puertos 1U (Intellinet 520959)",
            qty=1,
            unit_price_mxn=Decimal("729.00"),
            link="https://cityshop.mx/producto/520959-panel-de-parcheo-cat6-24-puertos-1u-soporta-cable-trenzado-solido-y-multifilar-de-calibres",
            note="Ordena el cableado del rack.",
        ),
        LineItem(
            name="Organizador horizontal 1U (Intellinet 169950)",
            qty=1,
            unit_price_mxn=Decimal("179.00"),
            link="https://cityshop.mx/producto/169950-organizador-horizontal-19-pulgadas-1u-metalico",
        ),
        LineItem(
            name="Tornilleria M6 para rack (Intellinet 713658, kit)",
            qty=1,
            unit_price_mxn=Decimal("469.00"),
            link="https://cityshop.mx/producto/tornilleria-m6-intellinet-713658-plata-kit-de-montaje",
        ),
        LineItem(
            name="Charola cantilever 1U para rack 19 (Intellinet 715072)",
            qty=1,
            unit_price_mxn=Decimal("459.00"),
            link="https://cityshop.mx/producto/charola-rack-intellinet-715072-charola-fija-cantilever-de-19-pulgadas-1u",
            note="Para montar NAS/mini equipos en rack de 2 postes.",
        ),
        LineItem(
            name="Cable patchcord Cat6 1m (Saxxon, P61UA)",
            qty=10,
            unit_price_mxn=Decimal("39.00"),
            link="https://cityshop.mx/producto/cable-patchcord-utp-saxxon-1-metro-cat6-azul",
            note="Para patch panel <-> switch <-> equipos.",
        ),
        LineItem(
            name="Cable Cat6 25m (Xcase, CAUTP625)",
            qty=1,
            unit_price_mxn=Decimal("189.00"),
            link="https://cityshop.mx/producto/cable-patch-cord-x-case-cat-6-25-metros-azul",
            note="Solo si el rack queda lejos del router.",
        ),
        LineItem(
            name="Adaptador USB-C a 2.5GbE (StarTech US2GC30)",
            qty=1,
            unit_price_mxn=Decimal("909.00"),
            link="https://cityshop.mx/producto/adaptador-de-red-ethernet-usb-c-adaptador-de-red-lan-nic-ethernet-rj45-nbase-t-usb-tipo-c-usb-30",
            note="Para que tu laptop/PC pueda probar 2.5GbE.",
        ),
    ]

    story: list = []
    story.append(_p("Cotizacion (Cityshop) - Compras vitales (previo a workstation)", styles["Title"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        _p(
            f"<b>Fecha:</b> {today}<br/>"
            "<b>Objetivo:</b> comprar lo vital para dejar el rack ordenado y listo: energia + red + backups.",
            body,
        )
    )
    story.append(Spacer(1, 0.1 * inch))
    story.append(
        _p(
            "<b>Notas:</b> precios/stock en Cityshop pueden cambiar. No incluye envio. "
            "Si un producto aparece como agotado al abrir, sustituyelo por uno equivalente.",
            small,
        )
    )

    story.append(Spacer(1, 0.18 * inch))
    story.append(_p("Lista de compra (prioridad alta)", h1))
    story.append(_items_table(infra, styles))
    story.append(Spacer(1, 0.08 * inch))
    story.append(_p(f"<b>Subtotal:</b> {_money(_sum(infra))}", body))
    story.append(Spacer(1, 0.12 * inch))
    story.append(
        _p(
            "<b>Siguiente paso despues de esto:</b> un nodo de computo (mini PC o workstation con GPU) "
            "para correr agentes + LLMs 24/7. Esa compra depende del presupuesto y del tamano de modelo que quieras.",
            body,
        )
    )

    def on_page(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawRightString(7.7 * inch, 0.55 * inch, f"Pagina {_doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    output_pdf = repo_root / "output" / "pdf" / "cotizacion_cityshop_vital_pre_ws_20k.pdf"
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(output_pdf)
    print(str(output_pdf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

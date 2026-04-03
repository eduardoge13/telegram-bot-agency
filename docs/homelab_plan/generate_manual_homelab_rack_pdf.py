#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def _link(label: str, url: str) -> str:
    safe_label = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_url = url.replace("&", "&amp;").replace("<", "%3C").replace(">", "%3E")
    return f'<link href="{safe_url}">{safe_label}</link>'


def _box(text: str, styles, width: float, bg: str = "#F3F4F6") -> Table:
    cell = _p(f"<b>{text}</b>", styles["BodyText"])
    t = Table([[cell]], colWidths=[width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
                ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#9CA3AF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def _arrow(styles) -> Paragraph:
    return _p("<b>&rarr;</b>", styles["BodyText"])


def _checklist(rows: list[list[str]], styles, col_widths) -> Table:
    body = styles["BodyText"]
    header = ParagraphStyle(
        "TblHeader",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.white,
    )
    cell = ParagraphStyle(
        "TblCell",
        parent=body,
        fontName="Helvetica",
        fontSize=9.7,
        leading=12,
    )

    cooked = []
    for r_i, row in enumerate(rows):
        style = header if r_i == 0 else cell
        cooked.append([_p(c, style) for c in row])

    t = Table(cooked, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ]
        )
    )
    return t


def build_pdf(output_pdf: Path) -> None:
    styles = getSampleStyleSheet()
    styles["Title"].fontName = "Helvetica-Bold"
    styles["Title"].fontSize = 18
    styles["Title"].leading = 22

    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=13.5,
        leading=17,
        spaceBefore=10,
        spaceAfter=6,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        spaceBefore=8,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.2,
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
        title="Manual Homelab Rack (UPS + NAS + Red)",
        author="SMARTCFO-AI",
    )

    story: list = []
    story.append(_p("Manual de Homelab Rack (UPS + NAS + Red) - Paso a paso", styles["Title"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(
        _p(
            f"<b>Fecha:</b> {today}<br/>"
            "<b>Objetivo:</b> montar tu rack, dejar el NAS en RAID1, y tener red lista para un futuro nodo de cómputo "
            "(workstation/servidor con GPU) para agentes + LLMs 24/7.",
            body,
        )
    )
    story.append(Spacer(1, 0.1 * inch))
    story.append(
        _p(
            "<b>Reglas para no estropear equipo:</b><br/>"
            "• No tapes rejillas de ventilación.<br/>"
            "• No apagues durante actualizaciones.<br/>"
            "• No muevas la UPS energizada.<br/>"
            "• Mantén cables de energía separados de cables de red.<br/>"
            "• RAID1 no es backup: aun con RAID, necesitas copias externas.",
            body,
        )
    )

    story.append(Spacer(1, 0.18 * inch))
    story.append(_p("Lo que ya compraste (lista 20k, sin precios)", h1))
    story.append(
        _p(
            "• 2x WD Red Pro 8TB (para RAID1 en tu QNAP)<br/>"
            "• Switch TP-Link SG3210X-M2 (2.5GbE)<br/>"
            "• PDU CyberPower CPS1215RM (1U)<br/>"
            "• Patch panel Cat6 24 puertos (1U) + Organizador 1U<br/>"
            "• Tornillería M6 + Charola 1U (para rack de 2 postes)<br/>"
            "• Patchcords Cat6 1m (x10) + cable Cat6 25m (si hace falta)<br/>"
            "• Adaptador USB‑C a 2.5GbE (para tu laptop/PC)",
            body,
        )
    )
    story.append(
        _p(
            "<b>Links (Cityshop):</b><br/>"
            "• 2do disco: "
            + _link(
                "WD Red Pro 8TB",
                "https://cityshop.mx/producto/disco-duro-interno-wd-red-pro-8tb-35-escritorio-sata3-6gbs-512mb-7200rpm-24x7-hotplug-nas-1-24-bahias",
            )
            + "<br/>"
            "• Switch: "
            + _link(
                "TP-Link SG3210X-M2",
                "https://cityshop.mx/producto/switch-tp-link-sg3210x-m2-switch-administrable-8-puertos-25-gps-2-puerto-sfp-10gps-omada-sdn-puertos",
            )
            + "<br/>"
            "• PDU: "
            + _link("CPS1215RM", "https://cityshop.mx/producto/pdu-cyberpower-cps1215rm-120-v")
            + "<br/>"
            "• Patch panel: "
            + _link(
                "Intellinet 520959",
                "https://cityshop.mx/producto/520959-panel-de-parcheo-cat6-24-puertos-1u-soporta-cable-trenzado-solido-y-multifilar-de-calibres",
            )
            + "<br/>"
            "• Organizador 1U: "
            + _link(
                "Intellinet 169950",
                "https://cityshop.mx/producto/169950-organizador-horizontal-19-pulgadas-1u-metalico",
            )
            + "<br/>"
            "• Tornillería: "
            + _link(
                "Intellinet 713658",
                "https://cityshop.mx/producto/tornilleria-m6-intellinet-713658-plata-kit-de-montaje",
            )
            + "<br/>"
            "• Charola 1U: "
            + _link(
                "Intellinet 715072",
                "https://cityshop.mx/producto/charola-rack-intellinet-715072-charola-fija-cantilever-de-19-pulgadas-1u",
            )
            + "<br/>"
            "• Patchcord 1m: "
            + _link(
                "Saxxon Cat6 1m",
                "https://cityshop.mx/producto/cable-patchcord-utp-saxxon-1-metro-cat6-azul",
            )
            + "<br/>"
            "• Cable 25m: "
            + _link(
                "Xcase Cat6 25m",
                "https://cityshop.mx/producto/cable-patch-cord-x-case-cat-6-25-metros-azul",
            )
            + "<br/>"
            "• USB‑C a 2.5GbE: "
            + _link(
                "StarTech US2GC30",
                "https://cityshop.mx/producto/adaptador-de-red-ethernet-usb-c-adaptador-de-red-lan-nic-ethernet-rj45-nbase-t-usb-tipo-c-usb-30",
            ),
            small,
        )
    )

    story.append(Spacer(1, 0.2 * inch))
    story.append(_p("Diagramas rápidos", h1))
    box_w = 2.1 * inch

    # Power diagram
    power = Table(
        [
            [
                _box("Pared", styles, box_w),
                _arrow(styles),
                _box("UPS (en piso)", styles, box_w, bg="#FEF3C7"),
                _arrow(styles),
                _box("PDU (en rack)", styles, box_w),
            ],
            ["", "", _p("<b>Luego:</b> PDU -> Switch y NAS", small)],
        ],
        colWidths=[box_w, 0.35 * inch, box_w, 0.35 * inch, box_w],
    )
    power.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("SPAN", (2, 1), (4, 1)),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(power)
    story.append(Spacer(1, 0.1 * inch))

    # Network diagram
    net = Table(
        [
            [
                _box("Router", styles, box_w),
                _arrow(styles),
                _box("Switch 2.5GbE", styles, box_w),
                _arrow(styles),
                _box("NAS QNAP", styles, box_w),
            ],
            ["", "", _p("Tu laptop entra al switch (ideal) para configurar y probar.", small)],
        ],
        colWidths=[box_w, 0.35 * inch, box_w, 0.35 * inch, box_w],
    )
    net.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("SPAN", (2, 1), (4, 1)),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(net)

    story.append(PageBreak())
    story.append(_p("Paso a paso (montaje físico + seguridad)", h1))
    story.append(
        _p(
            "<b>Paso 1: Lee los manuales (10 minutos)</b><br/>"
            "• UPS SIGNAL: "
            + _link("Manual (PDF)", "https://www.complet.mx/downloads/ups/UPS_SIGNAL.pdf")
            + "<br/>"
            "• PDU CyberPower: "
            + _link("Manual", "https://www.cyberpowersystems.com/resources/cps1215rm-user-manual/")
            + "<br/>"
            "• NAS QNAP TS‑x53E: "
            + _link("Guía (PDF)", "https://download.qnap.com/TechnicalDocument/Storage/SMB%20NAS/ts-x53e/ts-x53e-ug-en-us.pdf"),
            body,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    story.append(_p("Paso 2: UPS (cargar y probar primero)", h2))
    story.append(
        _p(
            "1) Coloca la UPS en piso firme (vertical) con ventilación. No la tapes.<br/>"
            "2) Si venía de un lugar frío a uno caliente, espera 2 horas (condensación).<br/>"
            "3) Conecta a contacto con tierra física y enciende.<br/>"
            "4) Primera carga: deja cargar 6 horas (el manual indica 4–6 horas).<br/>"
            "5) Prueba con carga ligera (router/modem) y confirma sin alarmas.",
            body,
        )
    )

    story.append(Spacer(1, 0.12 * inch))
    story.append(_p("Paso 3: Montaje en rack (sin shelves extra)", h2))
    story.append(
        _p(
            "Orden recomendado en el rack (de arriba hacia abajo):<br/>"
            "1) Patch panel (1U)<br/>"
            "2) Organizador horizontal (1U)<br/>"
            "3) Switch 2.5GbE<br/>"
            "4) PDU (1U)<br/>"
            "5) Charola 1U (para el NAS si cabe).<br/><br/>"
            "<b>Tips:</b> aprieta tornillos M6 firmes, pero sin barrer la rosca. No dejes equipo “colgando”.",
            body,
        )
    )

    story.append(Spacer(1, 0.16 * inch))
    story.append(_p("Checklist de montaje", h2))
    story.append(
        _checklist(
            [
                ["Elemento", "Validación", "OK si..."],
                ["Rack", "Estabilidad", "No se mueve; ideal anclado"],
                ["UPS", "Ubicación", "En piso firme, ventilada"],
                ["PDU", "Montaje", "Fija, sin tensión en cables"],
                ["Switch", "Ventilación", "Sin rejillas tapadas"],
                ["Cables", "Orden", "Energía por un lado, red por otro"],
            ],
            styles,
            [1.05 * inch, 3.85 * inch, 2.3 * inch],
        )
    )

    story.append(PageBreak())
    story.append(_p("Paso a paso (red + NAS + RAID1)", h1))
    story.append(_p("Paso 4: Cableado de red (Ethernet)", h2))
    story.append(
        _p(
            "<b>Ethernet</b> es el cable de red con conector transparente (RJ45).<br/>"
            "1) Conecta Router -> Switch (un cable).<br/>"
            "2) Conecta NAS -> Switch (un cable).<br/>"
            "3) Conecta tu laptop/PC -> Switch (ideal) para configurar.<br/>"
            "4) Si tu laptop no tiene puerto de red: usa el adaptador USB‑C a 2.5GbE.",
            body,
        )
    )
    story.append(Spacer(1, 0.1 * inch))
    story.append(_p("Paso 5: 2.5GbE (cómo identificarlo y confirmarlo)", h2))
    story.append(
        _p(
            "• Para que sea 2.5GbE, <b>los dos lados</b> deben soportar 2.5GbE (NAS y switch/PC).<br/>"
            "• El NAS TS‑253E tiene 2 puertos 2.5GbE.<br/>"
            "• Confirma en QTS: Configuración -> Red -> ver “velocidad de enlace” (1.0 Gbps o 2.5 Gbps).",
            body,
        )
    )

    story.append(Spacer(1, 0.12 * inch))
    story.append(_p("Paso 6: Configuración inicial del NAS (QTS)", h2))
    story.append(
        _p(
            "Opción recomendada: Qfinder Pro (oficial).<br/>"
            "1) Descarga Qfinder Pro: " + _link("QNAP Utilities", "https://www.qnap.com/en/utilities/essentials") + "<br/>"
            "2) Instala y abre Qfinder; detecta el NAS; abre el asistente.<br/>"
            "3) Crea usuario administrador y contraseña fuerte.<br/>"
            "4) Actualiza firmware (no apagar durante el proceso).",
            body,
        )
    )

    story.append(Spacer(1, 0.12 * inch))
    story.append(_p("Paso 7: RAID1 con 2 discos (muy importante)", h2))
    story.append(
        _p(
            "<b>Recomendado:</b> RAID1 (espejo) para tolerar falla de 1 disco.<br/>"
            "<b>Importante:</b> RAID1 NO sustituye backups.<br/><br/>"
            "<b>Si el NAS está nuevo (sin datos):</b><br/>"
            "• Crea el almacenamiento como RAID1 desde el asistente/Storage &amp; Snapshots.<br/><br/>"
            "<b>Si ya usabas 1 disco con datos (migración a RAID1):</b><br/>"
            "1) Haz backup de tus datos importantes antes de migrar.<br/>"
            "2) Inserta el 2º disco (del mismo tamaño).<br/>"
            "3) En QTS: Storage &amp; Snapshots -> Storage/Snapshots -> selecciona el RAID Group -> Manage -> Migrate -> RAID1.<br/>"
            "4) Espera a que termine la sincronización (puede tardar horas). No apagues.<br/><br/>"
            "Referencia oficial QNAP (migración Single -> RAID1): "
            + _link("QNAP Docs", "https://docs.qnap.com/operating-system/qts/4.4.x/en-us/GUID-65CE6D6C-4BDD-411A-B856-4D6CAC2B255C.html"),
            body,
        )
    )

    story.append(Spacer(1, 0.12 * inch))
    story.append(_p("Paso 8: Carpetas compartidas + backups", h2))
    story.append(
        _p(
            "1) Crea carpetas: Backups, Proyectos, Documentos.<br/>"
            "2) Activa SMB (Windows/Mac) si te lo pide el asistente.<br/>"
            "3) Programa un backup semanal mínimo desde tu PC al NAS.<br/>"
            "4) En el futuro: agrega backup externo (otro disco o nube) para protegerte contra borrado/ransomware.",
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
    output_pdf = repo_root / "output" / "pdf" / "manual_homelab_rack_paso_a_paso.pdf"
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(output_pdf)
    print(str(output_pdf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


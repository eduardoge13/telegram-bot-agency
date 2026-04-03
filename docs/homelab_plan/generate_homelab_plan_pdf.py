#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def _link(label: str, url: str) -> str:
    safe_label = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_url = url.replace("&", "&amp;").replace("<", "%3C").replace(">", "%3E")
    return f'<link href="{safe_url}">{safe_label}</link>'


def _box(text: str, styles, width: float) -> Table:
    cell = _p(f"<b>{text}</b>", styles["BodyText"])
    t = Table([[cell]], colWidths=[width])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
                ("BOX", (0, 0), (-1, -1), 1.0, colors.HexColor("#9CA3AF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def _arrow(styles) -> Paragraph:
    return _p("<b>&rarr;</b>", styles["BodyText"])


def build_pdf(output_pdf: Path) -> None:
    styles = getSampleStyleSheet()
    styles["Title"].fontName = "Helvetica-Bold"
    styles["Title"].fontSize = 20
    styles["Title"].leading = 24

    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
    )
    small = ParagraphStyle(
        "Small",
        parent=body,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#374151"),
    )

    today = dt.date.today().strftime("%B %d, %Y")
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=LETTER,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Guia de instalacion segura: UPS + NAS",
        author="SMARTCFO-AI",
    )

    story: list = []

    story.append(_p("Guia de instalacion segura: UPS + NAS (Paso a paso)", styles["Title"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        _p(
            f"<b>Fecha:</b> {today}<br/>"
            "<b>Objetivo:</b> dejar funcionando tu NAS como servidor de backups (seguro) y, si quieres, "
            "preparar el camino para correr LLMs (normalmente en otra PC/servidor).",
            body,
        )
    )
    story.append(Spacer(1, 0.2 * inch))
    story.append(
        _p(
            "<b>Regla de oro:</b> primero leemos el manual. "
            "No conectes nada a la UPS/NAS hasta terminar los pasos de verificacion.",
            body,
        )
    )

    story.append(Spacer(1, 0.25 * inch))
    story.append(_p("Equipo comprado (segun tus links)", h1))
    story.append(
        _p(
            "• UPS SIGNAL 3KT220M: "
            + _link(
                "cityshop.mx",
                "https://cityshop.mx/producto/ups-3000va3000w-modelo-3kt220m-on-line-senoidal-doble-conversion-alta-frecuencia-signal-gabinete",
            )
            + "<br/>"
            "• NAS QNAP TS-253E-8G (2 bahias): "
            + _link(
                "cityshop.mx",
                "https://cityshop.mx/producto/nas-qnap-ts-253e-8g-2-bahias-torre-intel-celeron-4nucleos-26ghz-8gb-ram-ddr4-lan-25gbe2-wake-on",
            )
            + "<br/>"
            "• 1 disco WD Red Pro 8TB (por ahora): "
            + _link(
                "cityshop.mx",
                "https://cityshop.mx/producto/disco-duro-interno-wd-red-pro-8tb-35-escritorio-sata3-6gbs-512mb-7200rpm-24x7-hotplug-nas-1-24-bahias",
            )
            + "<br/>"
            "• Rack 2 postes 45U: "
            + _link(
                "cityshop.mx",
                "https://cityshop.mx/producto/rack-de-2-postes-45u-intellinet-715997-45u",
            ),
            body,
        )
    )

    story.append(Spacer(1, 0.18 * inch))
    story.append(_p("Advertencia importante (1 solo disco)", h1))
    story.append(
        _p(
            "<b>Hoy tienes 1 disco.</b> Eso significa: <b>NO hay redundancia</b>.<br/>"
            "Si ese disco falla, puedes perder toda la informacion.<br/>"
            "<b>Recomendacion:</b> compra un segundo disco igual y configura RAID1 (espejo) cuando lo tengas.",
            body,
        )
    )

    story.append(Spacer(1, 0.18 * inch))
    story.append(_p("Diagramas (electricidad y red)", h1))
    story.append(Spacer(1, 0.05 * inch))

    box_w = 2.15 * inch
    diagram_power = Table(
        [
            [
                _box("Pared (corriente)", styles, box_w),
                _arrow(styles),
                _box("UPS", styles, box_w),
                _arrow(styles),
                _box("NAS", styles, box_w),
            ],
            ["", "", _p("El NAS va a un contacto con bateria de la UPS.", small)],
        ],
        colWidths=[box_w, 0.35 * inch, box_w, 0.35 * inch, box_w],
    )
    diagram_power.setStyle(
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
    story.append(diagram_power)

    diagram_net = Table(
        [
            [
                _box("Tu laptop", styles, box_w),
                _arrow(styles),
                _box("Router / Switch", styles, box_w),
                _arrow(styles),
                _box("NAS", styles, box_w),
            ],
            [
                "",
                "",
                _p("<b>Esto usa un cable Ethernet</b> (el cable de red con conector transparente).", small),
            ],
        ],
        colWidths=[box_w, 0.35 * inch, box_w, 0.35 * inch, box_w],
    )
    diagram_net.setStyle(
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
    story.append(diagram_net)

    story.append(Spacer(1, 0.25 * inch))
    story.append(_p("Paso 1: UPS (leer manual, cargar y probar)", h1))
    story.append(
        _p(
            "Antes de hacer nada, descarga el manual oficial de la UPS (SIGNAL 3KT220M):<br/>"
            "• Manual UPS SIGNAL (PDF): "
            + _link("complet.mx", "https://www.complet.mx/downloads/ups/UPS_SIGNAL.pdf")
            + "<br/><br/>"
            "<b>1A) Preparar el lugar (segun manual):</b><br/>"
            "1) Si la UPS viene de un lugar frio a uno caliente: espera <b>2 horas</b> antes de encender (para evitar condensacion).<br/>"
            "2) Coloca la UPS <b>vertical</b> y en piso firme (por ahora, porque faltan shelves).<br/>"
            "3) No pongas objetos encima y <b>no tapes</b> las rejillas de ventilacion.<br/>"
            "4) Mantener lejos de agua/humedad y sol directo.<br/><br/>"
            "<b>1B) Inspeccion y encendido:</b><br/>"
            "1) Revisa golpes/daños. Si esta golpeada: <b>no la energices</b>.<br/>"
            "2) Conectala a un contacto con <b>tierra fisica</b> (ground).<br/>"
            "3) Enciende la UPS (como indique el manual).<br/><br/>"
            "<b>1C) Carga inicial (muy importante):</b><br/>"
            "• El manual indica: <b>Tiempo de recarga de baterias incluidas: 4-6 horas</b>.<br/>"
            "• Para primera carga, usa <b>6 horas</b> para ir a la segura.<br/><br/>"
            "<b>1D) Prueba rapida sin riesgos:</b><br/>"
            "1) Con la UPS encendida, conecta una carga pequena (modem o router).<br/>"
            "2) Verifica que no haya alarmas y que todo siga estable por 5-10 minutos.<br/><br/>"
            "<b>NO conectar a la salida del UPS:</b> impresoras laser, microondas, motores o aparatos que sobrecarguen la UPS.",
            body,
        )
    )
    story.append(Spacer(1, 0.18 * inch))

    checklist_rows = [
        ["Prueba", "Que validar", "OK si..."],
        ["UPS", "Ventilacion", "No hay rejillas tapadas"],
        ["UPS", "Tierra fisica", "Usa contacto con tierra"],
        ["UPS", "Carga 6 horas", "Sin alarmas y bateria cargada"],
        ["UPS", "Prueba ligera", "Router/modem no se apaga"],
    ]
    checklist = Table(
        [[_p(c, styles["BodyText"]) for c in row] for row in checklist_rows],
        colWidths=[0.6 * inch, 5.7 * inch, 0.9 * inch],
        repeatRows=1,
    )
    checklist.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(checklist)

    story.append(Spacer(1, 0.22 * inch))
    story.append(_p("Paso 2: NAS (leer manual, revisar caja, instalar disco)", h1))
    story.append(
        _p(
            "<b>Antes de conectar el NAS a la UPS:</b> saca el NAS, abre la caja y revisa el contenido.<br/>"
            "<b>Documentacion oficial QNAP:</b><br/>"
            "• Producto TS-253E (oficial): "
            + _link("qnap.com", "https://www.qnap.com/en/product/ts-253e")
            + "<br/>"
            "• Guia de usuario TS-x53E (PDF oficial): "
            + _link("download.qnap.com", "https://download.qnap.com/TechnicalDocument/Storage/SMB%20NAS/ts-x53e/ts-x53e-ug-en-us.pdf")
            + "<br/>"
            "• Inicializar QTS con Qfinder Pro (oficial): "
            + _link(
                "docs.qnap.com",
                "https://docs.qnap.com/operating-system/qts/5.1.x/en-us/initializing-qts-using-qfinder-pro-F069A693.html",
            )
            + "<br/>"
            "• Descargar Qfinder Pro (oficial, utilidades): "
            + _link("qnap.com/utilities", "https://www.qnap.com/en/utilities/essentials")
            + "<br/><br/>"
            "<b>Instalar 1 disco (hoy):</b><br/>"
            "1) Asegurate de que el NAS este <b>apagado</b> y desconectado.<br/>"
            "2) Toca una parte metalica (para descargar estatica) antes de tocar el disco.<br/>"
            "3) Abre la bahia, monta el disco WD Red Pro en la charola (como indica el manual) y cierrala bien.<br/>"
            "4) Coloca el NAS con espacio para aire (minimo 10 cm alrededor).",
            body,
        )
    )

    story.append(Spacer(1, 0.22 * inch))
    story.append(_p("Paso 3: Conectar NAS a la UPS (solo despues de los pasos 1 y 2)", h1))
    story.append(
        _p(
            "1) Conecta el NAS a un contacto de salida de la UPS (preferir salida con bateria).<br/>"
            "2) Enciende el NAS y espera a que termine de arrancar (puede tardar varios minutos).<br/>"
            "3) No conectes otros equipos pesados a la UPS hasta que todo este estable.",
            body,
        )
    )

    story.append(Spacer(1, 0.22 * inch))
    story.append(_p("Paso 4: Red (cable Ethernet y 2.5GbE explicado)", h1))
    story.append(
        _p(
            "<b>Que es el cable Ethernet:</b> es el cable de red con conector transparente (tipo RJ45). "
            "Va del NAS al router/switch.<br/><br/>"
            "<b>Conectar red:</b><br/>"
            "1) Conecta un extremo del cable Ethernet al NAS.<br/>"
            "2) Conecta el otro extremo al router o al switch (puerto libre).<br/><br/>"
            "<b>2.5GbE (que significa y como tenerlo):</b><br/>"
            "• El NAS tiene <b>2 puertos 2.5GbE</b>. Eso solo se aprovecha si el otro lado tambien es 2.5GbE.<br/>"
            "• Para tener 2.5GbE necesitas: (A) switch/router 2.5GbE o (B) PC con puerto 2.5GbE.<br/>"
            "• Con 1GbE funciona bien por ahora; solo sera mas lento (pero estable).<br/>"
            "• Si tu equipo/switch dice “2.5G” en el puerto o en el modelo, es probable que sea 2.5GbE.<br/><br/>"
            "<b>Como confirmas la velocidad:</b><br/>"
            "• En QTS (pantalla del NAS): revisa la velocidad de enlace en configuracion de red.<br/>"
            "• En tu PC: el adaptador de red normalmente muestra “Velocidad: 1.0 Gbps” o “2.5 Gbps”.",
            body,
        )
    )

    story.append(Spacer(1, 0.22 * inch))
    story.append(_p("Paso 5: Configuracion inicial (QNAP QTS) - super guiado", h1))
    story.append(
        _p(
            "<b>Opcion A (recomendada): Qfinder Pro</b><br/>"
            "1) Descarga Qfinder Pro desde QNAP (oficial): " + _link("QNAP Utilities", "https://www.qnap.com/en/utilities/essentials") + "<br/>"
            "2) Instala y abre Qfinder Pro en tu computadora.<br/>"
            "3) Qfinder debe encontrar el NAS automaticamente. Haz doble clic para abrir la pagina de configuracion.<br/><br/>"
            "<b>Opcion B: encontrar la IP en el router</b><br/>"
            "1) Entra al panel de tu router (normalmente desde el navegador).<br/>"
            "2) Busca “Dispositivos conectados / DHCP / Clientes”.<br/>"
            "3) Encuentra el NAS (QNAP) y anota su IP (ejemplo: 192.168.1.50).<br/>"
            "4) Abre el navegador y entra a esa IP.<br/><br/>"
            "<b>En el asistente de QTS:</b><br/>"
            "1) Crea el usuario administrador y una contraseña fuerte (anotala en un lugar seguro).<br/>"
            "2) Actualiza firmware (si lo pide). No apagues el NAS durante la actualizacion.<br/>"
            "3) Crea el almacenamiento con 1 disco: selecciona modo de 1 disco (sin RAID).",
            body,
        )
    )

    story.append(Spacer(1, 0.22 * inch))
    story.append(_p("Paso 6: Carpetas compartidas y backups (Paso 7 mejorado)", h1))
    story.append(
        _p(
            "<b>Objetivo:</b> que tus archivos importantes vivan en el NAS y/o se copien al NAS con un calendario.<br/><br/>"
            "<b>Crear carpetas en QTS:</b><br/>"
            "1) Crea carpetas tipo: <b>Backups</b>, <b>Proyectos</b>, <b>Documentos</b>.<br/>"
            "2) Activa el servicio de archivos (SMB) para Windows/Mac si el asistente lo pregunta.<br/><br/>"
            "<b>Conectar desde Windows:</b><br/>"
            "• Abre Explorador -> escribe <b>\\\\IP_DEL_NAS</b> (ej: \\\\192.168.1.50) -> inicia sesion.<br/><br/>"
            "<b>Conectar desde macOS:</b><br/>"
            "• Finder -> Ir -> Conectarse al servidor -> <b>smb://IP_DEL_NAS</b>.<br/><br/>"
            "<b>Backups semanales (minimo):</b><br/>"
            "• Cada semana copia tus carpetas criticas (proyectos, docs, llaves) a la carpeta <b>Backups</b> del NAS.<br/>"
            "• Cuando compres el 2do disco: configura RAID1 y vuelve a validar tu plan de backup.<br/><br/>"
            "<b>Nota sobre LLMs (por ahora):</b> puedes guardar modelos/datos en el NAS, pero correr modelos en el NAS "
            "puede ser lento. Lo normal es correr el LLM en una PC/servidor dedicado y usar el NAS para almacenamiento y backups.",
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
    output_pdf = repo_root / "output" / "pdf" / "guia_ups_nas_paso_a_paso.pdf"
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(output_pdf)
    print(str(output_pdf))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

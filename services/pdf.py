# Generation de la fiche PDF d'un rendez-vous
import io
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from utils import format_id


def _safe_xml(text: str) -> str:
    """Échappe les caractères réservés XML pour les Paragraphs ReportLab."""
    if not text:
        return ""
    return xml_escape(str(text))


def generer_pdf_brief(rdv):
    """Genere une fiche PDF propre et adaptee au rendez-vous."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontSize=14, textColor=colors.HexColor('#1E3A8A'), alignment=0)
    heading_style = ParagraphStyle('HeadStyle', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#1E3A8A'), spaceAfter=6)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, leading=13)

    story = [
        Paragraph("LAMINA GESTION DES AUDIENCES", title_style),
        Paragraph(f"FICHE DE BRIEF D'AUDIENCE EXECUTIF {format_id(rdv.id)}", heading_style),
        Spacer(1, 10)
    ]

    data = [
        [Paragraph("Identifiant", body_style), Paragraph(format_id(rdv.id), body_style)],
        [Paragraph("Objet du RDV", body_style), Paragraph(_safe_xml(rdv.titre), body_style)],
        [Paragraph("Intervenant", body_style), Paragraph(_safe_xml(rdv.intervenant), body_style)],
        [Paragraph("E-mail", body_style), Paragraph(_safe_xml(rdv.email_intervenant or "Non renseigné"), body_style)],
        [Paragraph("Téléphone", body_style), Paragraph(_safe_xml(rdv.telephone or "Non renseigné"), body_style)],
        [Paragraph("Organisme", body_style), Paragraph(_safe_xml(rdv.organisme or "Non renseigné"), body_style)],
        [Paragraph("Date et Heure", body_style), Paragraph(rdv.date_heure.strftime('%d/%m/%Y à %H:%M'), body_style)],
        [Paragraph("Durée prévue", body_style), Paragraph(f"{rdv.duree_minutes} minutes", body_style)],
        [Paragraph("Priorité", body_style), Paragraph(_safe_xml(rdv.priorite), body_style)],
    ]

    t = Table(data, colWidths=[120, 390])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.extend([t, Spacer(1, 10), Paragraph("CONTEXTE ET POINTS CLÉS À ABORDER", heading_style)])

    notes_texte = _safe_xml(rdv.contexte_notes or "Aucune note saisie.")
    story.extend([Paragraph(notes_texte.replace('\n', '<br/>'), body_style), Spacer(1, 10)])

    doc.build(story)
    buffer.seek(0)
    return buffer
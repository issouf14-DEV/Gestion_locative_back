"""
Générateur de rapports PDF pour les factures
Utilise reportlab pour générer les PDFs
"""
from decimal import Decimal
from io import BytesIO
from typing import Optional
from datetime import datetime
from django.http import HttpResponse

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from .models import Facture, FactureCollective


class FacturePDFGenerator:
    """
    Génère des rapports PDF pour les factures
    """
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab n'est pas installé. "
                "Installez-le avec: pip install reportlab"
            )
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Configure les styles personnalisés"""
        self.styles.add(ParagraphStyle(
            name='TitreFacture',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='SousTitre',
            parent=self.styles['Heading2'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='InfoClient',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='MontantTotal',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=TA_RIGHT,
            textColor=colors.HexColor('#1a73e8')
        ))
    
    def generer_facture_individuelle(self, facture: Facture) -> BytesIO:
        """
        Génère un PDF pour une facture individuelle
        
        Returns:
            BytesIO contenant le PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        locataire = facture.locataire
        
        # Helper pour get_*_display methods
        def get_display(obj: object, field: str, default: str) -> str:
            return getattr(obj, f'get_{field}_display', lambda: default)()
        
        # En-tête
        elements.append(Paragraph("FACTURE", self.styles['TitreFacture']))
        elements.append(Spacer(1, 10*mm))
        
        # Informations de la facture
        info_facture = [
            ['Référence:', facture.reference],
            ['Type:', get_display(facture, 'type_facture', facture.type_facture)],
            ['Période:', f"{facture.mois}/{facture.annee}"],
            ['Date d\'émission:', facture.date_emission.strftime('%d/%m/%Y')],
            ['Échéance:', facture.date_echeance.strftime('%d/%m/%Y')],
        ]
        
        table_info = Table(info_facture, colWidths=[4*cm, 6*cm])
        table_info.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table_info)
        elements.append(Spacer(1, 10*mm))
        
        # Informations du locataire
        elements.append(Paragraph("Destinataire", self.styles['SousTitre']))
        elements.append(Paragraph(f"<b>{locataire.prenoms} {locataire.nom}</b>", self.styles['InfoClient']))
        elements.append(Paragraph(f"Email: {locataire.email}", self.styles['InfoClient']))
        elements.append(Paragraph(f"Tél: {locataire.telephone}", self.styles['InfoClient']))
        if locataire.adresse:
            elements.append(Paragraph(f"Adresse: {locataire.adresse}", self.styles['InfoClient']))
        elements.append(Spacer(1, 10*mm))
        
        # Détails de la facture
        elements.append(Paragraph("Détails", self.styles['SousTitre']))
        
        if facture.type_facture in ['SODECI', 'CIE']:
            # Facture SODECI/CIE avec détails de consommation
            details_data = [
                ['Description', 'Valeur'],
                ['Index ancien', f"{facture.index_ancien}"],
                ['Index nouveau', f"{facture.index_nouveau}"],
                ['Consommation', f"{facture.consommation} unités"],
                ['Votre part', f"{facture.pourcentage}%"],
                ['', ''],
                ['MONTANT À PAYER', f"{facture.montant:,.0f} FCFA"],
            ]
        else:
            # Facture loyer ou autre
            type_display = get_display(facture, 'type_facture', facture.type_facture)
            details_data = [
                ['Description', 'Montant'],
                [f'{type_display} - {facture.mois}/{facture.annee}', f"{facture.montant:,.0f} FCFA"],
                ['', ''],
                ['TOTAL À PAYER', f"{facture.montant:,.0f} FCFA"],
            ]
        
        table_details = Table(details_data, colWidths=[10*cm, 5*cm])
        table_details.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_details)
        elements.append(Spacer(1, 15*mm))
        
        # Statut
        statut_color = {
            'EN_ATTENTE': colors.orange,
            'PAYEE': colors.green,
            'EN_RETARD': colors.red,
            'ANNULEE': colors.grey,
        }.get(facture.statut, colors.black)
        
        statut_display = get_display(facture, 'statut', facture.statut)
        elements.append(Paragraph(
            f"<b>Statut:</b> <font color='{statut_color}'>{statut_display}</font>",
            self.styles['Normal']
        ))
        
        # Pied de page
        elements.append(Spacer(1, 20*mm))
        elements.append(Paragraph(
            "Merci de régler cette facture avant la date d'échéance.",
            self.styles['InfoClient']
        ))
        elements.append(Paragraph(
            f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.styles['InfoClient']
        ))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generer_rapport_mensuel(self, mois: int, annee: int, type_facture: Optional[str] = None) -> BytesIO:
        """
        Génère un rapport PDF de toutes les factures d'un mois
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # Filtrer les factures
        queryset = Facture.objects.filter(mois=mois, annee=annee)
        if type_facture:
            queryset = queryset.filter(type_facture=type_facture)
        factures = queryset.select_related('locataire').order_by('type_facture', 'locataire__nom')
        
        # Titre
        titre = f"RAPPORT FACTURATION - {mois:02d}/{annee}"
        if type_facture:
            titre += f" ({type_facture})"
        elements.append(Paragraph(titre, self.styles['TitreFacture']))
        elements.append(Spacer(1, 10*mm))
        
        # Résumé
        total_montant = sum(f.montant for f in factures)
        payees = len([f for f in factures if f.statut == 'PAYEE'])
        en_attente = len([f for f in factures if f.statut == 'EN_ATTENTE'])
        en_retard = len([f for f in factures if f.statut == 'EN_RETARD'])
        
        resume_data = [
            ['RÉSUMÉ', ''],
            ['Nombre de factures', str(len(factures))],
            ['Montant total', f"{total_montant:,.0f} FCFA"],
            ['Payées', str(payees)],
            ['En attente', str(en_attente)],
            ['En retard', str(en_retard)],
        ]
        
        table_resume = Table(resume_data, colWidths=[8*cm, 6*cm])
        table_resume.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table_resume)
        elements.append(Spacer(1, 15*mm))
        
        # Liste des factures
        elements.append(Paragraph("DÉTAIL DES FACTURES", self.styles['SousTitre']))
        
        factures_data = [['Locataire', 'Type', 'Montant', 'Statut']]
        for f in factures:
            type_disp = getattr(f, 'get_type_facture_display', lambda: f.type_facture)()
            statut_disp = getattr(f, 'get_statut_display', lambda: f.statut)()
            factures_data.append([
                f.locataire.get_full_name(),
                type_disp,
                f"{f.montant:,.0f} FCFA",
                statut_disp
            ])
        
        table_factures = Table(factures_data, colWidths=[6*cm, 3*cm, 4*cm, 3*cm])
        table_factures.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ]))
        elements.append(table_factures)
        
        # Pied
        elements.append(Spacer(1, 15*mm))
        elements.append(Paragraph(
            f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.styles['InfoClient']
        ))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    def generer_rapport_repartition(self, facture_collective_id: str) -> BytesIO:
        """
        Génère un rapport PDF de la répartition d'une facture collective SODECI/CIE
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        fc = FactureCollective.objects.get(id=facture_collective_id)
        factures = Facture.objects.filter(
            type_facture=fc.type_facture,
            mois=fc.mois,
            annee=fc.annee
        ).select_related('locataire').order_by('-consommation')
        
        # Titre
        type_fc_display = getattr(fc, 'get_type_facture_display', lambda: fc.type_facture)()
        elements.append(Paragraph(
            f"RÉPARTITION {type_fc_display} - {fc.mois:02d}/{fc.annee}",
            self.styles['TitreFacture']
        ))
        elements.append(Spacer(1, 10*mm))
        
        # Infos facture collective
        info_data = [
            ['Montant total facture:', f"{fc.montant_total:,.0f} FCFA"],
            ['Consommation totale:', f"{fc.consommation_totale} unités"],
            ['Nombre de locataires:', str(factures.count())],
            ['Date de répartition:', fc.date_repartition.strftime('%d/%m/%Y') if fc.date_repartition else '-'],
        ]
        
        table_info = Table(info_data, colWidths=[6*cm, 8*cm])
        table_info.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table_info)
        elements.append(Spacer(1, 15*mm))
        
        # Tableau de répartition
        elements.append(Paragraph("DÉTAIL PAR LOCATAIRE", self.styles['SousTitre']))
        
        repartition_data = [['Locataire', 'Index Ancien', 'Index Nouveau', 'Conso.', '%', 'Montant']]
        for f in factures:
            repartition_data.append([
                f.locataire.get_full_name(),
                str(f.index_ancien or '-'),
                str(f.index_nouveau or '-'),
                str(f.consommation or '-'),
                f"{f.pourcentage:.1f}%" if f.pourcentage else '-',
                f"{f.montant:,.0f} FCFA"
            ])
        
        # Ligne de total
        total_conso = sum(f.consommation or Decimal('0') for f in factures)
        total_montant = sum(f.montant for f in factures)
        repartition_data.append(['TOTAL', '', '', str(total_conso), '100%', f"{total_montant:,.0f} FCFA"])
        
        table_rep = Table(repartition_data, colWidths=[4.5*cm, 2.5*cm, 2.5*cm, 2*cm, 2*cm, 3*cm])
        table_rep.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f4f8')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#fafafa')]),
        ]))
        elements.append(table_rep)
        
        # Formule utilisée
        elements.append(Spacer(1, 15*mm))
        elements.append(Paragraph("FORMULE DE CALCUL", self.styles['SousTitre']))
        elements.append(Paragraph(
            "Montant_locataire = (Consommation_locataire / Consommation_totale) × Montant_facture",
            self.styles['InfoClient']
        ))
        
        # Pied
        elements.append(Spacer(1, 15*mm))
        elements.append(Paragraph(
            f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.styles['InfoClient']
        ))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer


def telecharger_facture_pdf(facture_id: str) -> HttpResponse:
    """
    Vue helper pour télécharger une facture en PDF
    """
    facture = Facture.objects.get(id=facture_id)
    generator = FacturePDFGenerator()
    pdf_buffer = generator.generer_facture_individuelle(facture)
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{facture.reference}.pdf"'
    return response


def telecharger_rapport_mensuel_pdf(mois: int, annee: int, type_facture: Optional[str] = None) -> HttpResponse:
    """
    Vue helper pour télécharger un rapport mensuel en PDF
    """
    generator = FacturePDFGenerator()
    pdf_buffer = generator.generer_rapport_mensuel(mois, annee, type_facture)
    
    filename = f"rapport_facturation_{mois:02d}_{annee}"
    if type_facture:
        filename += f"_{type_facture}"
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response


def telecharger_rapport_repartition_pdf(facture_collective_id: str) -> HttpResponse:
    """
    Vue helper pour télécharger un rapport de répartition en PDF
    """
    generator = FacturePDFGenerator()
    pdf_buffer = generator.generer_rapport_repartition(facture_collective_id)
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="repartition_{facture_collective_id[:8]}.pdf"'
    return response

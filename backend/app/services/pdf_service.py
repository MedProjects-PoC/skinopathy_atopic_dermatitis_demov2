"""
PDF generation service for user and HCP reports
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas
from loguru import logger
from typing import Dict, Any, Optional


class PDFGenerator:
    """Generate professional PDF reports for user and HCP"""

    # Color scheme
    PRIMARY_COLOR = HexColor("#1E88E5")  # Blue
    SECONDARY_COLOR = HexColor("#43A047")  # Green
    WARNING_COLOR = HexColor("#FB8C00")  # Orange
    DANGER_COLOR = HexColor("#E53935")  # Red
    LIGHT_GRAY = HexColor("#F5F5F5")
    DARK_GRAY = HexColor("#424242")

    @staticmethod
    def _get_custom_styles():
        """Get custom paragraph styles"""
        styles = getSampleStyleSheet()

        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=PDFGenerator.PRIMARY_COLOR,
            spaceAfter=30,
            fontName='Helvetica-Bold'
        ))

        # Heading style
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=PDFGenerator.PRIMARY_COLOR,
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderColor=PDFGenerator.PRIMARY_COLOR,
            borderWidth=1,
            borderPadding=8,
            backColor=PDFGenerator.LIGHT_GRAY
        ))

        # Body style
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=16,
            alignment=0,  # Left align
        ))

        return styles

    @staticmethod
    def generate_user_report_pdf(
        session_id: str,
        report_data: Dict[str, Any],
        questionnaire_data: Optional[Dict[str, Any]] = None
    ) -> BytesIO:
        """
        Generate user-friendly PDF report

        Args:
            session_id: Session identifier
            report_data: Report content dictionary
            questionnaire_data: Optional questionnaire responses

        Returns:
            BytesIO object containing PDF
        """
        try:
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )

            story = []
            styles = PDFGenerator._get_custom_styles()

            # Header
            story.append(Paragraph("Atopic Dermatitis Assessment Report", styles['CustomTitle']))
            story.append(Paragraph(f"<b>Session ID:</b> {session_id}", styles['Normal']))
            story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            # Severity Assessment
            severity = report_data.get('severity', 'Unknown')
            severity_color = PDFGenerator._get_severity_color_hex(severity)

            story.append(Paragraph("Severity Assessment", styles['CustomHeading']))

            severity_table = Table(
                [[
                    Paragraph(f"<b>Severity Level:</b>", styles['Normal']),
                    Paragraph(f"<font color='{severity_color}'><b>{severity}</b></font>", styles['Normal'])
                ]],
                colWidths=[2*inch, 2*inch]
            )
            severity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), PDFGenerator.LIGHT_GRAY),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BORDER', (0, 0), (-1, -1), 1, PDFGenerator.PRIMARY_COLOR),
            ]))
            story.append(severity_table)
            story.append(Spacer(1, 0.2*inch))

            # Summary
            summary = report_data.get('summary', '')
            if summary:
                story.append(Paragraph("Summary", styles['CustomHeading']))
                story.append(Paragraph(summary, styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))

            # Key Findings
            key_findings = report_data.get('key_findings', [])
            if key_findings:
                story.append(Paragraph("Key Findings", styles['CustomHeading']))
                findings_text = '<br/>'.join([f"• {finding}" for finding in key_findings])
                story.append(Paragraph(findings_text, styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))

            # Recommendations
            recommendations = report_data.get('recommendations', [])
            if recommendations:
                story.append(Paragraph("Recommendations", styles['CustomHeading']))
                recs_text = '<br/>'.join([f"✓ {rec}" for rec in recommendations])
                story.append(Paragraph(recs_text, styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))

            # AI Insights
            ai_insights = report_data.get('ai_insights', {})
            if ai_insights:
                story.append(Paragraph("AI Analysis Metrics", styles['CustomHeading']))

                insights_data = [['Metric', 'Value']]
                if 'severity_score' in ai_insights:
                    insights_data.append(['Severity Score', f"{ai_insights['severity_score']}/100"])
                if 'affected_area_pct' in ai_insights:
                    insights_data.append(['Affected Area', f"{ai_insights['affected_area_pct']}%"])
                if 'flare_status' in ai_insights:
                    insights_data.append(['Flare Status', ai_insights['flare_status']])

                if len(insights_data) > 1:
                    insights_table = Table(insights_data, colWidths=[2*inch, 2*inch])
                    insights_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), PDFGenerator.PRIMARY_COLOR),
                        ('TEXTCOLOR', (0, 0), (-1, 0), white),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 11),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, PDFGenerator.LIGHT_GRAY]),
                        ('BORDER', (0, 0), (-1, -1), 1, PDFGenerator.PRIMARY_COLOR),
                    ]))
                    story.append(insights_table)
                    story.append(Spacer(1, 0.2*inch))

            # When to Seek Help
            seek_help = report_data.get('when_to_seek_help', '')
            if seek_help:
                story.append(Paragraph("When to Seek Medical Help", styles['CustomHeading']))
                story.append(Paragraph(seek_help, styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))

            # Disclaimer
            story.append(Spacer(1, 0.2*inch))
            disclaimer = "⚠ DISCLAIMER: This assessment is generated by an AI system and is NOT a substitute for professional medical diagnosis or treatment. Please consult a licensed healthcare provider for proper evaluation and management of your condition."
            story.append(Paragraph(disclaimer, ParagraphStyle(
                name='Disclaimer',
                parent=styles['Normal'],
                fontSize=10,
                textColor=PDFGenerator.WARNING_COLOR,
                borderColor=PDFGenerator.WARNING_COLOR,
                borderWidth=1,
                borderPadding=10,
                backColor=HexColor("#FFF3E0")
            )))

            # Build PDF
            doc.build(story)
            pdf_buffer.seek(0)
            logger.info(f"User PDF generated successfully for session {session_id}")
            return pdf_buffer

        except Exception as e:
            logger.error(f"Error generating user PDF: {e}")
            raise

    @staticmethod
    def generate_hcp_report_pdf(
        session_id: str,
        report_data: Dict[str, Any],
        questionnaire_data: Optional[Dict[str, Any]] = None
    ) -> BytesIO:
        """
        Generate clinical HCP PDF report

        Args:
            session_id: Session identifier
            report_data: Report content dictionary
            questionnaire_data: Optional questionnaire responses

        Returns:
            BytesIO object containing PDF
        """
        try:
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )

            story = []
            styles = PDFGenerator._get_custom_styles()

            # Header
            story.append(Paragraph("Atopic Dermatitis - Clinical HCP Report", styles['CustomTitle']))
            story.append(Paragraph(f"<b>Session ID:</b> {session_id}", styles['Normal']))
            story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))

            # Severity Assessment
            severity_data = report_data.get('severity_assessment', {})
            if severity_data:
                story.append(Paragraph("Severity Assessment", styles['CustomHeading']))

                severity_info = [['Assessment Parameter', 'Value']]
                for key, value in severity_data.items():
                    formatted_key = key.replace('_', ' ').title()
                    severity_info.append([formatted_key, str(value)])

                if len(severity_info) > 1:
                    severity_table = Table(severity_info, colWidths=[2.5*inch, 1.5*inch])
                    severity_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), PDFGenerator.PRIMARY_COLOR),
                        ('TEXTCOLOR', (0, 0), (-1, 0), white),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, PDFGenerator.LIGHT_GRAY]),
                        ('BORDER', (0, 0), (-1, -1), 1, PDFGenerator.PRIMARY_COLOR),
                    ]))
                    story.append(severity_table)
                    story.append(Spacer(1, 0.2*inch))

            # SOAP Note
            soap_note = report_data.get('soap_note', {})
            if soap_note:
                story.append(Paragraph("Clinical Note (SOAP)", styles['CustomHeading']))

                for section_name in ['subjective', 'objective', 'assessment', 'plan']:
                    content = soap_note.get(section_name, '')
                    if content:
                        section_title = section_name.upper()
                        story.append(Paragraph(f"<b>{section_title}:</b>", styles['Normal']))
                        story.append(Paragraph(content, styles['CustomBody']))
                        story.append(Spacer(1, 0.1*inch))

                story.append(Spacer(1, 0.2*inch))

            # CNN Analysis
            cnn_analysis = report_data.get('cnn_analysis', {})
            if cnn_analysis:
                story.append(Paragraph("CNN Model Analysis", styles['CustomHeading']))

                cnn_data = [['CNN Metric', 'Value']]
                for key, value in cnn_analysis.items():
                    if key != 'body_region_distribution':
                        formatted_key = key.replace('_', ' ').title()
                        cnn_data.append([formatted_key, str(value)])

                if len(cnn_data) > 1:
                    cnn_table = Table(cnn_data, colWidths=[2.5*inch, 1.5*inch])
                    cnn_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), PDFGenerator.SECONDARY_COLOR),
                        ('TEXTCOLOR', (0, 0), (-1, 0), white),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor("#E8F5E9")]),
                        ('BORDER', (0, 0), (-1, -1), 1, PDFGenerator.SECONDARY_COLOR),
                    ]))
                    story.append(cnn_table)
                    story.append(Spacer(1, 0.2*inch))

            # Vision Agent Findings
            vision_findings = report_data.get('vision_agent_findings', {})
            if vision_findings:
                story.append(Paragraph("Vision AI Clinical Analysis", styles['CustomHeading']))

                if 'clinical_assessment' in vision_findings:
                    story.append(Paragraph("<b>Clinical Assessment:</b>", styles['Normal']))
                    story.append(Paragraph(vision_findings['clinical_assessment'], styles['CustomBody']))
                    story.append(Spacer(1, 0.1*inch))

                if 'differential_diagnosis' in vision_findings:
                    story.append(Paragraph("<b>Differential Diagnosis:</b>", styles['Normal']))
                    story.append(Paragraph(vision_findings['differential_diagnosis'], styles['CustomBody']))
                    story.append(Spacer(1, 0.1*inch))

                if 'key_features' in vision_findings:
                    story.append(Paragraph("<b>Key Features:</b>", styles['Normal']))
                    features_text = '<br/>'.join([f"• {feat}" for feat in vision_findings['key_features']])
                    story.append(Paragraph(features_text, styles['CustomBody']))
                    story.append(Spacer(1, 0.2*inch))

            # Treatment Recommendations
            treatment_recs = report_data.get('treatment_recommendations', [])
            if treatment_recs:
                story.append(Paragraph("Treatment Recommendations", styles['CustomHeading']))
                recs_text = '<br/>'.join([f"• {rec}" for rec in treatment_recs])
                story.append(Paragraph(recs_text, styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))

            # Differential Considerations
            differential = report_data.get('differential_considerations', [])
            if differential:
                story.append(Paragraph("Differential Considerations", styles['CustomHeading']))
                diff_text = '<br/>'.join([f"• {item}" for item in differential])
                story.append(Paragraph(diff_text, styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))

            # Prognosis
            prognosis = report_data.get('prognosis', '')
            if prognosis:
                story.append(Paragraph("Prognosis", styles['CustomHeading']))
                story.append(Paragraph(prognosis, styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))

            # Next Assessment
            next_assess = report_data.get('next_assessment_recommended', '')
            if next_assess:
                story.append(Paragraph("Recommended Follow-up", styles['CustomHeading']))
                story.append(Paragraph(next_assess, styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))

            # Disclaimer
            story.append(Spacer(1, 0.3*inch))
            disclaimer = "This report is generated by an AI-assisted analysis system and should be reviewed and validated by a licensed healthcare provider before clinical use. AI findings supplement but do not replace professional clinical judgment."
            story.append(Paragraph(disclaimer, ParagraphStyle(
                name='Disclaimer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=PDFGenerator.DARK_GRAY,
                borderColor=PDFGenerator.DARK_GRAY,
                borderWidth=1,
                borderPadding=10,
                backColor=PDFGenerator.LIGHT_GRAY
            )))

            # Build PDF
            doc.build(story)
            pdf_buffer.seek(0)
            logger.info(f"HCP PDF generated successfully for session {session_id}")
            return pdf_buffer

        except Exception as e:
            logger.error(f"Error generating HCP PDF: {e}")
            raise

    @staticmethod
    def _get_severity_color_hex(severity: str) -> str:
        """Get hex color for severity level"""
        severity_lower = severity.lower()
        if severity_lower == 'mild':
            return '#43A047'  # Green
        elif severity_lower == 'moderate':
            return '#FB8C00'  # Orange
        elif severity_lower == 'severe':
            return '#E53935'  # Red
        else:
            return '#1E88E5'  # Blue (default)

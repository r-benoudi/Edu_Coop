from io import BytesIO
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import date


def generate_invoice(payment):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    elements = []
    
    elements.append(Paragraph("Educational Cooperative", title_style))
    elements.append(Paragraph("INVOICE", header_style))
    elements.append(Spacer(1, 20))
    
    invoice_info = [
        ['Invoice Number:', f'INV-{payment.pk:05d}'],
        ['Date:', date.today().strftime('%d/%m/%Y')],
        ['Billing Period:', payment.month.strftime('%B %Y')],
    ]
    
    info_table = Table(invoice_info, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    if payment.student:
        elements.append(Paragraph(f"<b>Bill To:</b>", styles['Normal']))
        elements.append(Paragraph(f"{payment.student.full_name}", styles['Normal']))
        if payment.student.email:
            elements.append(Paragraph(f"{payment.student.email}", styles['Normal']))
        if payment.student.phone:
            elements.append(Paragraph(f"{payment.student.phone}", styles['Normal']))
    
    elements.append(Spacer(1, 30))
    
    items = [['Description', 'Amount (DH)']]
    items.append([f'Monthly Fee - {payment.month.strftime("%B %Y")}', f'{payment.amount:.2f}'])
    
    items_table = Table(items, colWidths=[4*inch, 1.5*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    totals = [
        ['Total Amount:', f'{payment.amount:.2f} DH'],
        ['Amount Paid:', f'{payment.amount_paid:.2f} DH'],
        ['Balance Due:', f'{payment.remaining_amount:.2f} DH'],
    ]
    
    totals_table = Table(totals, colWidths=[4*inch, 1.5*inch])
    totals_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1e3a5f')),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 40))
    
    elements.append(Paragraph(f"<b>Payment Status:</b> {payment.get_status_display()}", styles['Normal']))
    
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("Thank you for choosing our educational services!", 
                             ParagraphStyle('Thanks', parent=styles['Normal'], alignment=TA_CENTER)))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{payment.pk}.pdf"'
    return response


def generate_contract(instructor, course=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    elements = []
    
    elements.append(Paragraph("Educational Cooperative", title_style))
    elements.append(Paragraph("INSTRUCTOR CONTRACT", 
                             ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)))
    elements.append(Spacer(1, 30))
    
    elements.append(Paragraph(f"<b>Contract Date:</b> {date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>PARTIES</b>", styles['Heading3']))
    elements.append(Paragraph("This contract is entered into between:", styles['Normal']))
    elements.append(Paragraph("<b>1. Educational Cooperative</b> (hereinafter referred to as 'The Cooperative')", styles['Normal']))
    elements.append(Paragraph(f"<b>2. {instructor.full_name}</b> (hereinafter referred to as 'The Instructor')", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>INSTRUCTOR INFORMATION</b>", styles['Heading3']))
    info = [
        ['Name:', instructor.full_name],
        ['Email:', instructor.email or 'N/A'],
        ['Phone:', instructor.phone or 'N/A'],
        ['Specialization:', instructor.specialization],
    ]
    
    info_table = Table(info, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>COMPENSATION</b>", styles['Heading3']))
    
    if course:
        if course.course_type == 'tutoring':
            comp_text = f"For tutoring services in {course.name}: 100 DH per student per month"
        else:
            comp_text = f"For IT course {course.name}: 120 DH per hour (maximum 8 hours per month)"
        elements.append(Paragraph(comp_text, styles['Normal']))
    else:
        elements.append(Paragraph("Tutoring: 100 DH per student per month", styles['Normal']))
        elements.append(Paragraph("IT Courses: 120 DH per hour (maximum 8 hours per month)", styles['Normal']))
    
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>TERMS AND CONDITIONS</b>", styles['Heading3']))
    terms = [
        "1. The Instructor agrees to provide educational services as assigned by The Cooperative.",
        "2. Payment will be made monthly based on the compensation structure outlined above.",
        "3. The Instructor must maintain accurate attendance records for all sessions.",
        "4. Either party may terminate this contract with 30 days written notice.",
        "5. The Instructor agrees to comply with all Cooperative policies and regulations.",
    ]
    for term in terms:
        elements.append(Paragraph(term, styles['Normal']))
        elements.append(Spacer(1, 5))
    
    elements.append(Spacer(1, 40))
    
    sig_table = Table([
        ['_' * 30, '_' * 30],
        ['Cooperative Representative', 'Instructor Signature'],
        ['', ''],
        ['Date: _______________', 'Date: _______________'],
    ], colWidths=[3*inch, 3*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(sig_table)
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="contract_{instructor.pk}.pdf"'
    return response


def generate_financial_report(report):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    elements = []
    
    elements.append(Paragraph("Educational Cooperative", title_style))
    elements.append(Paragraph(f"Financial Report - {report.month.strftime('%B %Y')}", 
                             ParagraphStyle('Subtitle', parent=styles['Heading2'], alignment=TA_CENTER)))
    elements.append(Spacer(1, 30))
    
    elements.append(Paragraph(f"<b>Report Generated:</b> {date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("<b>FINANCIAL SUMMARY</b>", styles['Heading3']))
    
    summary = [
        ['Category', 'Amount (DH)'],
        ['Total Revenue (Student Fees)', f'{report.total_revenue:,.2f}'],
        ['Total Instructor Payments', f'{report.total_instructor_payments:,.2f}'],
        ['Gross Profit', f'{report.gross_profit:,.2f}'],
        ['Net Profit', f'{report.net_profit:,.2f}'],
    ]
    
    summary_table = Table(summary, colWidths=[3.5*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e6f3ff')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    distributions = report.distributions.select_related('member').all()
    if distributions.exists():
        elements.append(Paragraph("<b>PROFIT DISTRIBUTION</b>", styles['Heading3']))
        
        dist_data = [['Member', 'Capital Share (%)', 'Amount (DH)']]
        for dist in distributions:
            dist_data.append([
                dist.member.full_name,
                f'{dist.share_percentage:.2f}%',
                f'{dist.amount:,.2f}'
            ])
        
        dist_table = Table(dist_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
        dist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
        ]))
        elements.append(dist_table)
    
    elements.append(Spacer(1, 40))
    
    status = "FINALIZED" if report.is_finalized else "DRAFT"
    elements.append(Paragraph(f"<b>Report Status:</b> {status}", styles['Normal']))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="financial_report_{report.month.strftime("%Y_%m")}.pdf"'
    return response

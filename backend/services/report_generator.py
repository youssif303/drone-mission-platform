import io
from typing import List
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime
from backend.models.mission import MissionDB
from backend.models.track import TrackDB
from backend.models.alert import AlertDB

class ReportGenerator:
    def generate_pdf(self, mission: MissionDB, tracks: List[TrackDB], alerts: List[AlertDB]) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        elements.append(Paragraph(f"Mission Report: {mission.name}", styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Mission Info
        status_val = getattr(mission.status, 'value', str(mission.status))
        created_str = mission.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(mission.created_at, 'strftime') else str(mission.created_at)
        elements.append(Paragraph(f"<b>Status:</b> {status_val.upper()}", styles['Normal']))
        elements.append(Paragraph(f"<b>Created:</b> {created_str}", styles['Normal']))
        if mission.description:
            elements.append(Paragraph(f"<b>Description:</b> {mission.description}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Tracks Summary
        elements.append(Paragraph("Tracked Objects Summary", styles['Heading2']))
        elements.append(Spacer(1, 6))
        
        track_data = [["Track ID", "Class", "Total Detections", "Status"]]
        for t in tracks:
            track_data.append([str(t.track_id), t.class_name, str(t.total_detections), t.status])
            
        if len(track_data) > 1:
            t_table = Table(track_data)
            t_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(t_table)
        else:
            elements.append(Paragraph("No objects tracked during this mission.", styles['Normal']))
            
        elements.append(Spacer(1, 12))
        
        # Alerts Summary
        elements.append(Paragraph("Alerts Summary", styles['Heading2']))
        elements.append(Spacer(1, 6))
        
        alert_data = [["Time", "Severity", "Type", "Message"]]
        for a in alerts:
            alert_data.append([
                a.timestamp.strftime('%H:%M:%S'), 
                a.severity, 
                a.alert_type, 
                a.message
            ])
            
        if len(alert_data) > 1:
            a_table = Table(alert_data, colWidths=[60, 60, 100, 240])
            a_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(a_table)
        else:
            elements.append(Paragraph("No alerts generated during this mission.", styles['Normal']))
            
        elements.append(Spacer(1, 24))
        elements.append(Paragraph(f"Generated at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", styles['Italic']))
        
        doc.build(elements)
        return buffer.getvalue()

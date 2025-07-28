"""
Report generation module for the Examination Seating System
"""
import os
import io
import csv
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import pandas as pd
from backend.database import db_manager

class ReportGenerator:
    """Generate various reports for the examination system"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.reports_dir = 'reports'
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_seating_arrangement_report(self, exam_date, session_time, format='pdf'):
        """Generate seating arrangement report"""
        try:
            # Get seating data
            query = '''
                SELECT sa.*, s.name as student_name, s.department, s.semester,
                       sub.subject_name, r.name as room_name, r.building, r.floor
                FROM seating_arrangements sa
                JOIN students s ON sa.student_id = s.student_id
                JOIN subjects sub ON sa.subject_code = sub.subject_code
                JOIN rooms r ON sa.room_id = r.room_id
                WHERE sa.exam_date = ? AND sa.session_time = ? AND sa.is_active = 1
                ORDER BY r.name, sa.seat_row, sa.seat_col
            '''
            data = db_manager.execute_query(query, (exam_date, session_time))
            
            if not data:
                return {'success': False, 'message': 'No seating arrangements found'}
            
            if format.lower() == 'pdf':
                return self._generate_seating_pdf(data, exam_date, session_time)
            elif format.lower() == 'excel':
                return self._generate_seating_excel(data, exam_date, session_time)
            elif format.lower() == 'csv':
                return self._generate_seating_csv(data, exam_date, session_time)
            else:
                return {'success': False, 'message': 'Unsupported format'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error generating report: {str(e)}'}
    
    def _generate_seating_pdf(self, data, exam_date, session_time):
        """Generate PDF seating arrangement report"""
        filename = f'seating_arrangement_{exam_date}_{session_time.replace(":", "")}.pdf'
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        story.append(Paragraph(f'Seating Arrangement Report', title_style))
        story.append(Paragraph(f'Date: {exam_date} | Session: {session_time}', self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Group by room
        rooms = {}
        for row in data:
            room_name = row['room_name']
            if room_name not in rooms:
                rooms[room_name] = []
            rooms[room_name].append(dict(row))
        
        # Generate room-wise reports
        for room_name, room_data in rooms.items():
            # Room header
            room_style = ParagraphStyle(
                'RoomHeader',
                parent=self.styles['Heading2'],
                fontSize=14,
                spaceAfter=10
            )
            story.append(Paragraph(f'Room: {room_name}', room_style))
            
            # Room statistics
            building = room_data[0]['building'] if room_data[0]['building'] else 'N/A'
            floor = room_data[0]['floor'] if room_data[0]['floor'] else 'N/A'
            story.append(Paragraph(f'Building: {building} | Floor: {floor} | Students: {len(room_data)}', 
                                 self.styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Create table data
            table_data = [['Seat', 'Student ID', 'Student Name', 'Department', 'Subject']]
            for student in sorted(room_data, key=lambda x: (x['seat_row'], x['seat_col'])):
                table_data.append([
                    f"{student['seat_row']}-{student['seat_col']}",
                    student['student_id'],
                    student['student_name'],
                    student['department'],
                    student['subject_code']
                ])
            
            # Create table
            table = Table(table_data, colWidths=[1*inch, 1.5*inch, 2*inch, 1.5*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(PageBreak())
        
        # Build PDF
        doc.build(story)
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'message': 'PDF report generated successfully'
        }
    
    def _generate_seating_excel(self, data, exam_date, session_time):
        """Generate Excel seating arrangement report"""
        filename = f'seating_arrangement_{exam_date}_{session_time.replace(":", "")}.xlsx'
        filepath = os.path.join(self.reports_dir, filename)
        
        # Convert to DataFrame
        df_data = []
        for row in data:
            df_data.append({
                'Room': row['room_name'],
                'Building': row['building'] or 'N/A',
                'Floor': row['floor'] or 'N/A',
                'Seat Position': f"{row['seat_row']}-{row['seat_col']}",
                'Student ID': row['student_id'],
                'Student Name': row['student_name'],
                'Department': row['department'],
                'Semester': row['semester'],
                'Subject Code': row['subject_code'],
                'Subject Name': row['subject_name']
            })
        
        df = pd.DataFrame(df_data)
        
        # Create Excel writer
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Total Students', 'Total Rooms', 'Exam Date', 'Session Time'],
                'Value': [len(data), len(set(row['room_name'] for row in data)), exam_date, session_time]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Main data sheet
            df.to_excel(writer, sheet_name='Seating Arrangement', index=False)
            
            # Room-wise sheets
            for room_name in df['Room'].unique():
                room_df = df[df['Room'] == room_name].copy()
                safe_room_name = room_name.replace('/', '_').replace('\\', '_')[:31]  # Excel sheet name limit
                room_df.to_excel(writer, sheet_name=safe_room_name, index=False)
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'message': 'Excel report generated successfully'
        }
    
    def _generate_seating_csv(self, data, exam_date, session_time):
        """Generate CSV seating arrangement report"""
        filename = f'seating_arrangement_{exam_date}_{session_time.replace(":", "")}.csv'
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['room_name', 'building', 'floor', 'seat_position', 'student_id', 
                         'student_name', 'department', 'semester', 'subject_code', 'subject_name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow({
                    'room_name': row['room_name'],
                    'building': row['building'] or 'N/A',
                    'floor': row['floor'] or 'N/A',
                    'seat_position': f"{row['seat_row']}-{row['seat_col']}",
                    'student_id': row['student_id'],
                    'student_name': row['student_name'],
                    'department': row['department'],
                    'semester': row['semester'],
                    'subject_code': row['subject_code'],
                    'subject_name': row['subject_name']
                })
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'message': 'CSV report generated successfully'
        }
    
    def generate_student_admit_cards(self, exam_date, session_time, format='pdf'):
        """Generate individual admit cards for students"""
        try:
            # Get student seating data
            query = '''
                SELECT sa.*, s.name as student_name, s.department, s.semester, s.email,
                       sub.subject_name, r.name as room_name, r.building, r.floor
                FROM seating_arrangements sa
                JOIN students s ON sa.student_id = s.student_id
                JOIN subjects sub ON sa.subject_code = sub.subject_code
                JOIN rooms r ON sa.room_id = r.room_id
                WHERE sa.exam_date = ? AND sa.session_time = ? AND sa.is_active = 1
                ORDER BY s.name
            '''
            data = db_manager.execute_query(query, (exam_date, session_time))
            
            if not data:
                return {'success': False, 'message': 'No seating arrangements found'}
            
            filename = f'admit_cards_{exam_date}_{session_time.replace(":", "")}.pdf'
            filepath = os.path.join(self.reports_dir, filename)
            
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            story = []
            
            for i, student in enumerate(data):
                # Admit card for each student
                story.append(self._create_admit_card(student, exam_date, session_time))
                
                # Add page break except for last student
                if i < len(data) - 1:
                    story.append(PageBreak())
            
            doc.build(story)
            
            return {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'message': f'Admit cards generated for {len(data)} students'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error generating admit cards: {str(e)}'}
    
    def _create_admit_card(self, student, exam_date, session_time):
        """Create individual admit card"""
        # Create a table for the admit card layout
        card_data = [
            ['EXAMINATION ADMIT CARD', ''],
            ['', ''],
            ['Student ID:', student['student_id']],
            ['Student Name:', student['student_name']],
            ['Department:', student['department']],
            ['Semester:', str(student['semester'])],
            ['', ''],
            ['Subject Code:', student['subject_code']],
            ['Subject Name:', student['subject_name']],
            ['', ''],
            ['Exam Date:', exam_date],
            ['Session Time:', session_time],
            ['', ''],
            ['Room:', student['room_name']],
            ['Building:', student['building'] or 'N/A'],
            ['Floor:', str(student['floor']) if student['floor'] else 'N/A'],
            ['Seat Number:', f"{student['seat_row']}-{student['seat_col']}"],
            ['', ''],
            ['Instructions:', ''],
            ['1. Arrive 30 minutes before exam time', ''],
            ['2. Bring valid ID and this admit card', ''],
            ['3. No electronic devices allowed', ''],
            ['4. Follow all examination rules', '']
        ]
        
        table = Table(card_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('SPAN', (0, 0), (1, 0)),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 2), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        return table
    
    def generate_room_utilization_report(self, date_from=None, date_to=None, format='pdf'):
        """Generate room utilization report"""
        try:
            # Build query based on date range
            if date_from and date_to:
                query = '''
                    SELECT r.room_id, r.name as room_name, r.capacity, r.building, r.floor,
                           COUNT(sa.id) as total_allocations,
                           COUNT(DISTINCT sa.exam_date || sa.session_time) as sessions_used,
                           ROUND(AVG(CAST(COUNT(sa.id) AS FLOAT) / r.capacity * 100), 2) as avg_occupancy
                    FROM rooms r
                    LEFT JOIN seating_arrangements sa ON r.room_id = sa.room_id 
                        AND sa.exam_date BETWEEN ? AND ? AND sa.is_active = 1
                    WHERE r.is_active = 1
                    GROUP BY r.room_id, r.name, r.capacity, r.building, r.floor
                    ORDER BY total_allocations DESC
                '''
                data = db_manager.execute_query(query, (date_from, date_to))
            else:
                query = '''
                    SELECT r.room_id, r.name as room_name, r.capacity, r.building, r.floor,
                           COUNT(sa.id) as total_allocations,
                           COUNT(DISTINCT sa.exam_date || sa.session_time) as sessions_used,
                           ROUND(AVG(CAST(COUNT(sa.id) AS FLOAT) / r.capacity * 100), 2) as avg_occupancy
                    FROM rooms r
                    LEFT JOIN seating_arrangements sa ON r.room_id = sa.room_id AND sa.is_active = 1
                    WHERE r.is_active = 1
                    GROUP BY r.room_id, r.name, r.capacity, r.building, r.floor
                    ORDER BY total_allocations DESC
                '''
                data = db_manager.execute_query(query)
            
            if format.lower() == 'pdf':
                return self._generate_utilization_pdf(data, date_from, date_to)
            elif format.lower() == 'excel':
                return self._generate_utilization_excel(data, date_from, date_to)
            else:
                return {'success': False, 'message': 'Unsupported format'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error generating report: {str(e)}'}
    
    def _generate_utilization_pdf(self, data, date_from, date_to):
        """Generate PDF room utilization report"""
        date_range = f"{date_from}_to_{date_to}" if date_from and date_to else "all_time"
        filename = f'room_utilization_{date_range}.pdf'
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph('Room Utilization Report', title_style))
        
        if date_from and date_to:
            story.append(Paragraph(f'Period: {date_from} to {date_to}', self.styles['Normal']))
        else:
            story.append(Paragraph('Period: All Time', self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Summary statistics
        total_rooms = len(data)
        total_allocations = sum(row['total_allocations'] for row in data)
        avg_utilization = sum(row['avg_occupancy'] or 0 for row in data) / total_rooms if total_rooms > 0 else 0
        
        summary_data = [
            ['Total Rooms', str(total_rooms)],
            ['Total Allocations', str(total_allocations)],
            ['Average Utilization', f"{avg_utilization:.1f}%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Detailed table
        table_data = [['Room', 'Building', 'Capacity', 'Allocations', 'Sessions', 'Avg Occupancy']]
        for row in data:
            table_data.append([
                row['room_name'],
                row['building'] or 'N/A',
                str(row['capacity']),
                str(row['total_allocations']),
                str(row['sessions_used']),
                f"{row['avg_occupancy'] or 0:.1f}%"
            ])
        
        detail_table = Table(table_data, colWidths=[1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(detail_table)
        doc.build(story)
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'message': 'Room utilization report generated successfully'
        }
    
    def _generate_utilization_excel(self, data, date_from, date_to):
        """Generate Excel room utilization report"""
        date_range = f"{date_from}_to_{date_to}" if date_from and date_to else "all_time"
        filename = f'room_utilization_{date_range}.xlsx'
        filepath = os.path.join(self.reports_dir, filename)
        
        # Convert to DataFrame
        df_data = []
        for row in data:
            df_data.append({
                'Room ID': row['room_id'],
                'Room Name': row['room_name'],
                'Building': row['building'] or 'N/A',
                'Floor': row['floor'] or 'N/A',
                'Capacity': row['capacity'],
                'Total Allocations': row['total_allocations'],
                'Sessions Used': row['sessions_used'],
                'Average Occupancy (%)': row['avg_occupancy'] or 0
            })
        
        df = pd.DataFrame(df_data)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Room Utilization', index=False)
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'message': 'Excel utilization report generated successfully'
        }
    
    def generate_invigilator_duty_roster(self, date_from=None, date_to=None, format='pdf'):
        """Generate invigilator duty roster"""
        try:
            # Build query
            if date_from and date_to:
                query = '''
                    SELECT ia.*, i.name as invigilator_name, i.department, i.phone,
                           r.name as room_name, r.building, s.subject_name
                    FROM invigilator_assignments ia
                    JOIN invigilators i ON ia.staff_id = i.staff_id
                    JOIN rooms r ON ia.room_id = r.room_id
                    JOIN subjects s ON ia.subject_code = s.subject_code
                    WHERE ia.exam_date BETWEEN ? AND ? AND ia.is_active = 1
                    ORDER BY ia.exam_date, ia.session_time, i.name
                '''
                data = db_manager.execute_query(query, (date_from, date_to))
            else:
                query = '''
                    SELECT ia.*, i.name as invigilator_name, i.department, i.phone,
                           r.name as room_name, r.building, s.subject_name
                    FROM invigilator_assignments ia
                    JOIN invigilators i ON ia.staff_id = i.staff_id
                    JOIN rooms r ON ia.room_id = r.room_id
                    JOIN subjects s ON ia.subject_code = s.subject_code
                    WHERE ia.is_active = 1
                    ORDER BY ia.exam_date, ia.session_time, i.name
                '''
                data = db_manager.execute_query(query)
            
            if not data:
                return {'success': False, 'message': 'No invigilator assignments found'}
            
            if format.lower() == 'pdf':
                return self._generate_duty_roster_pdf(data, date_from, date_to)
            elif format.lower() == 'excel':
                return self._generate_duty_roster_excel(data, date_from, date_to)
            else:
                return {'success': False, 'message': 'Unsupported format'}
                
        except Exception as e:
            return {'success': False, 'message': f'Error generating duty roster: {str(e)}'}
    
    def _generate_duty_roster_pdf(self, data, date_from, date_to):
        """Generate PDF duty roster"""
        date_range = f"{date_from}_to_{date_to}" if date_from and date_to else "all_time"
        filename = f'duty_roster_{date_range}.pdf'
        filepath = os.path.join(self.reports_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph('Invigilator Duty Roster', title_style))
        
        if date_from and date_to:
            story.append(Paragraph(f'Period: {date_from} to {date_to}', self.styles['Normal']))
        else:
            story.append(Paragraph('Period: All Scheduled Duties', self.styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Create table
        table_data = [['Date', 'Time', 'Invigilator', 'Department', 'Room', 'Subject', 'Contact']]
        for row in data:
            table_data.append([
                row['exam_date'],
                row['session_time'],
                row['invigilator_name'],
                row['department'] or 'N/A',
                row['room_name'],
                row['subject_name'],
                row['phone'] or 'N/A'
            ])
        
        table = Table(table_data, colWidths=[0.8*inch, 0.6*inch, 1.2*inch, 0.8*inch, 1*inch, 1.2*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'message': 'Duty roster generated successfully'
        }
    
    def _generate_duty_roster_excel(self, data, date_from, date_to):
        """Generate Excel duty roster"""
        date_range = f"{date_from}_to_{date_to}" if date_from and date_to else "all_time"
        filename = f'duty_roster_{date_range}.xlsx'
        filepath = os.path.join(self.reports_dir, filename)
        
        # Convert to DataFrame
        df_data = []
        for row in data:
            df_data.append({
                'Date': row['exam_date'],
                'Session Time': row['session_time'],
                'Staff ID': row['staff_id'],
                'Invigilator Name': row['invigilator_name'],
                'Department': row['department'] or 'N/A',
                'Room': row['room_name'],
                'Building': row['building'] or 'N/A',
                'Subject': row['subject_name'],
                'Contact': row['phone'] or 'N/A',
                'Assignment Type': row['assignment_type']
            })
        
        df = pd.DataFrame(df_data)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Duty Roster', index=False)
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'message': 'Excel duty roster generated successfully'
        }

# Global report generator instance
report_generator = ReportGenerator()
"""
Utility functions for the Examination Seating System
"""
import os
import csv
import json
import pandas as pd
from datetime import datetime, timedelta
import uuid
import hashlib
from werkzeug.utils import secure_filename
from backend.database import db_manager
from backend.models import Student, Subject, Room, Exam, Invigilator

class DataImporter:
    """Handle data import operations"""
    
    def __init__(self):
        self.allowed_extensions = {'csv', 'xlsx', 'xls'}
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def import_students_from_csv(self, file_path):
        """Import students from CSV file"""
        results = {
            'success': 0,
            'errors': [],
            'duplicates': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Validate required fields
                        if not row.get('student_id') or not row.get('name'):
                            results['errors'].append(f'Row {row_num}: Student ID and Name are required')
                            continue
                        
                        # Check for duplicate
                        existing = Student.get_by_id(row['student_id'].strip())
                        if existing:
                            results['duplicates'] += 1
                            continue
                        
                        # Create student
                        student = Student(
                            student_id=row['student_id'].strip(),
                            name=row['name'].strip(),
                            department=row.get('department', '').strip(),
                            semester=int(row.get('semester', 1)),
                            email=row.get('email', '').strip(),
                            phone=row.get('phone', '').strip(),
                            address=row.get('address', '').strip(),
                            guardian_name=row.get('guardian_name', '').strip(),
                            guardian_phone=row.get('guardian_phone', '').strip()
                        )
                        
                        student.save()
                        
                        # Handle subject enrollments
                        subjects = row.get('subjects', '').strip()
                        if subjects:
                            subject_codes = [s.strip() for s in subjects.split(',')]
                            for subject_code in subject_codes:
                                if subject_code:
                                    student.enroll_subject(subject_code)
                        
                        results['success'] += 1
                        
                    except Exception as e:
                        results['errors'].append(f'Row {row_num}: {str(e)}')
        
        except Exception as e:
            results['errors'].append(f'File error: {str(e)}')
        
        return results
    
    def import_subjects_from_csv(self, file_path):
        """Import subjects from CSV file"""
        results = {
            'success': 0,
            'errors': [],
            'duplicates': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Validate required fields
                        if not row.get('subject_code') or not row.get('subject_name'):
                            results['errors'].append(f'Row {row_num}: Subject Code and Name are required')
                            continue
                        
                        # Check for duplicate
                        existing = Subject.get_by_code(row['subject_code'].strip())
                        if existing:
                            results['duplicates'] += 1
                            continue
                        
                        # Create subject
                        subject = Subject(
                            subject_code=row['subject_code'].strip(),
                            subject_name=row['subject_name'].strip(),
                            department=row.get('department', '').strip(),
                            semester=int(row.get('semester', 1)),
                            credits=int(row.get('credits', 3)),
                            subject_type=row.get('subject_type', 'theory').strip()
                        )
                        
                        subject.save()
                        results['success'] += 1
                        
                    except Exception as e:
                        results['errors'].append(f'Row {row_num}: {str(e)}')
        
        except Exception as e:
            results['errors'].append(f'File error: {str(e)}')
        
        return results
    
    def import_rooms_from_csv(self, file_path):
        """Import rooms from CSV file"""
        results = {
            'success': 0,
            'errors': [],
            'duplicates': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Validate required fields
                        if not row.get('room_id') or not row.get('name'):
                            results['errors'].append(f'Row {row_num}: Room ID and Name are required')
                            continue
                        
                        # Check for duplicate
                        existing = Room.get_by_id(row['room_id'].strip())
                        if existing:
                            results['duplicates'] += 1
                            continue
                        
                        # Create room
                        room = Room(
                            room_id=row['room_id'].strip(),
                            name=row['name'].strip(),
                            rows=int(row.get('rows', 10)),
                            cols=int(row.get('cols', 10)),
                            capacity=int(row.get('capacity', 100)),
                            building=row.get('building', '').strip(),
                            floor=int(row.get('floor', 1)) if row.get('floor') else None,
                            room_type=row.get('room_type', 'classroom').strip(),
                            facilities=row.get('facilities', '').strip()
                        )
                        
                        room.save()
                        results['success'] += 1
                        
                    except Exception as e:
                        results['errors'].append(f'Row {row_num}: {str(e)}')
        
        except Exception as e:
            results['errors'].append(f'File error: {str(e)}')
        
        return results

class DataExporter:
    """Handle data export operations"""
    
    def __init__(self):
        self.export_dir = 'exports'
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_students_to_csv(self, filters=None):
        """Export students to CSV"""
        filename = f'students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join(self.export_dir, filename)
        
        # Get students based on filters
        students = Student.get_all(
            department=filters.get('department') if filters else None,
            semester=filters.get('semester') if filters else None,
            search=filters.get('search') if filters else None
        )
        
        with open(filepath, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['student_id', 'name', 'department', 'semester', 'email', 'phone', 
                         'address', 'guardian_name', 'guardian_phone', 'subjects']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for student in students:
                # Get enrolled subjects
                subjects = student.get_subjects()
                subject_codes = ','.join([s['subject_code'] for s in subjects])
                
                writer.writerow({
                    'student_id': student.student_id,
                    'name': student.name,
                    'department': student.department,
                    'semester': student.semester,
                    'email': student.email or '',
                    'phone': student.phone or '',
                    'address': student.address or '',
                    'guardian_name': student.guardian_name or '',
                    'guardian_phone': student.guardian_phone or '',
                    'subjects': subject_codes
                })
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'count': len(students)
        }
    
    def export_subjects_to_csv(self, filters=None):
        """Export subjects to CSV"""
        filename = f'subjects_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        filepath = os.path.join(self.export_dir, filename)
        
        subjects = Subject.get_all(
            department=filters.get('department') if filters else None,
            semester=filters.get('semester') if filters else None,
            search=filters.get('search') if filters else None
        )
        
        with open(filepath, 'w', newline='', encoding='utf-8') as file:
            fieldnames = ['subject_code', 'subject_name', 'department', 'semester', 
                         'credits', 'subject_type', 'enrolled_students']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            writer.writeheader()
            for subject in subjects:
                # Get enrolled students count
                enrolled = subject.get_enrolled_students()
                
                writer.writerow({
                    'subject_code': subject.subject_code,
                    'subject_name': subject.subject_name,
                    'department': subject.department,
                    'semester': subject.semester,
                    'credits': subject.credits,
                    'subject_type': subject.subject_type,
                    'enrolled_students': len(enrolled)
                })
        
        return {
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'count': len(subjects)
        }

class ValidationUtils:
    """Utility functions for data validation"""
    
    @staticmethod
    def validate_student_id(student_id):
        """Validate student ID format"""
        if not student_id or len(student_id) < 3:
            return False, "Student ID must be at least 3 characters long"
        
        # Check for alphanumeric characters
        if not student_id.replace('-', '').replace('_', '').isalnum():
            return False, "Student ID can only contain letters, numbers, hyphens, and underscores"
        
        return True, ""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email:
            return True, ""  # Email is optional
        
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        if not phone:
            return True, ""  # Phone is optional
        
        import re
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        if len(digits_only) < 10 or len(digits_only) > 15:
            return False, "Phone number must be between 10 and 15 digits"
        
        return True, ""
    
    @staticmethod
    def validate_room_capacity(rows, cols, capacity):
        """Validate room capacity against dimensions"""
        calculated_capacity = rows * cols
        
        if capacity > calculated_capacity:
            return False, f"Capacity ({capacity}) cannot exceed rows × cols ({calculated_capacity})"
        
        if capacity < calculated_capacity * 0.5:
            return False, f"Capacity ({capacity}) seems too low for room dimensions"
        
        return True, ""

class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def generate_secure_filename(filename):
        """Generate a secure filename"""
        filename = secure_filename(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name, ext = os.path.splitext(filename)
        return f"{name}_{timestamp}{ext}"
    
    @staticmethod
    def generate_api_key():
        """Generate a secure API key"""
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
    
    @staticmethod
    def hash_password(password):
        """Hash a password securely"""
        from werkzeug.security import generate_password_hash
        return generate_password_hash(password)
    
    @staticmethod
    def verify_password(password, hash):
        """Verify a password against its hash"""
        from werkzeug.security import check_password_hash
        return check_password_hash(hash, password)

class DateTimeUtils:
    """Date and time utility functions"""
    
    @staticmethod
    def get_academic_year():
        """Get current academic year"""
        now = datetime.now()
        if now.month >= 7:  # July onwards is new academic year
            return f"{now.year}-{now.year + 1}"
        else:
            return f"{now.year - 1}-{now.year}"
    
    @staticmethod
    def get_semester_from_date(date):
        """Determine semester from date"""
        month = date.month
        if month in [7, 8, 9, 10, 11, 12]:
            return "Odd"  # July to December
        else:
            return "Even"  # January to June
    
    @staticmethod
    def format_duration(minutes):
        """Format duration in minutes to human readable format"""
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0:
            return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
        else:
            return f"{mins}m"
    
    @staticmethod
    def get_exam_sessions():
        """Get standard exam session times"""
        return [
            {'value': '09:00', 'label': '9:00 AM - 12:00 PM (Morning)'},
            {'value': '14:00', 'label': '2:00 PM - 5:00 PM (Afternoon)'},
            {'value': '10:00', 'label': '10:00 AM - 1:00 PM (Late Morning)'},
            {'value': '15:00', 'label': '3:00 PM - 6:00 PM (Late Afternoon)'}
        ]

# Global utility instances
data_importer = DataImporter()
data_exporter = DataExporter()
validation_utils = ValidationUtils()
security_utils = SecurityUtils()
datetime_utils = DateTimeUtils()
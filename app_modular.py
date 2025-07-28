"""
Modular Flask Application for Examination Seating System
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
import os
from datetime import datetime, timedelta

# Import backend modules
from backend.database import db_manager
from backend.models import Student, Subject, Room, Exam, Invigilator
from backend.seating_algorithm import seating_algorithm
from backend.reports import report_generator

# Import frontend modules
from frontend.routes import register_blueprints

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = 'your-secret-key-change-this-in-production'
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    register_blueprints(app)
    
    # Template filters
    @app.template_filter('moment')
    def moment_filter(date_string):
        """Format date using moment.js style"""
        if not date_string:
            return ''
        try:
            if isinstance(date_string, str):
                dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            else:
                dt = date_string
            return dt
        except:
            return date_string
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    # Context processors
    @app.context_processor
    def inject_user():
        """Inject user information into all templates"""
        return {
            'current_user': {
                'id': session.get('admin_id'),
                'name': session.get('admin_name'),
                'email': session.get('admin_email'),
                'role': session.get('admin_role')
            } if 'admin_id' in session else None
        }
    
    @app.context_processor
    def inject_stats():
        """Inject system statistics into all templates"""
        try:
            stats = db_manager.get_statistics()
            return {'system_stats': stats}
        except:
            return {'system_stats': {}}
    
    # API Routes for AJAX calls
    @app.route('/api/students/search')
    def api_search_students():
        """API endpoint for student search"""
        query = request.args.get('q', '')
        department = request.args.get('department', '')
        semester = request.args.get('semester', '')
        
        students = Student.get_all(
            department=department if department else None,
            semester=int(semester) if semester else None,
            search=query if query else None
        )
        
        return jsonify([{
            'id': s.student_id,
            'name': s.name,
            'department': s.department,
            'semester': s.semester
        } for s in students[:20]])  # Limit to 20 results
    
    @app.route('/api/subjects/search')
    def api_search_subjects():
        """API endpoint for subject search"""
        query = request.args.get('q', '')
        department = request.args.get('department', '')
        
        subjects = Subject.get_all(
            department=department if department else None,
            search=query if query else None
        )
        
        return jsonify([{
            'code': s.subject_code,
            'name': s.subject_name,
            'department': s.department,
            'semester': s.semester
        } for s in subjects[:20]])
    
    @app.route('/api/rooms/availability')
    def api_room_availability():
        """API endpoint for room availability"""
        exam_date = request.args.get('date')
        session_time = request.args.get('session')
        
        if not exam_date or not session_time:
            return jsonify({'error': 'Date and session time required'}), 400
        
        rooms = Room.get_all()
        availability = []
        
        for room in rooms:
            occupancy = room.get_occupancy(exam_date, session_time)
            availability.append({
                'room_id': room.room_id,
                'name': room.name,
                'capacity': room.capacity,
                'occupied': occupancy['occupied'],
                'available': room.capacity - occupancy['occupied'],
                'occupancy_rate': occupancy['occupancy_rate']
            })
        
        return jsonify(availability)
    
    @app.route('/api/seating/validate')
    def api_validate_seating():
        """API endpoint for seating validation"""
        exam_date = request.args.get('date')
        session_time = request.args.get('session')
        
        if not exam_date or not session_time:
            return jsonify({'error': 'Date and session time required'}), 400
        
        conflicts = seating_algorithm.validate_arrangement(exam_date, session_time)
        
        return jsonify({
            'valid': len(conflicts) == 0,
            'conflicts': conflicts,
            'conflict_count': len(conflicts)
        })
    
    @app.route('/api/reports/preview')
    def api_report_preview():
        """API endpoint for report preview"""
        report_type = request.args.get('type')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Generate preview data based on report type
        preview_data = {
            'report_type': report_type,
            'estimated_size': '2.5 MB',
            'estimated_pages': 15,
            'records_count': 150
        }
        
        return jsonify(preview_data)
    
    # Utility routes
    @app.route('/api/export/students')
    def export_students():
        """Export students data"""
        try:
            format_type = request.args.get('format', 'csv')
            department = request.args.get('department', '')
            semester = request.args.get('semester', '')
            
            students = Student.get_all(
                department=department if department else None,
                semester=int(semester) if semester else None
            )
            
            if format_type == 'csv':
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['Student ID', 'Name', 'Department', 'Semester', 'Email', 'Phone'])
                
                # Write data
                for student in students:
                    writer.writerow([
                        student.student_id, student.name, student.department,
                        student.semester, student.email or '', student.phone or ''
                    ])
                
                # Create response
                from flask import Response
                response = Response(
                    output.getvalue(),
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=students.csv'}
                )
                return response
            
            else:
                return jsonify({'error': 'Unsupported format'}), 400
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/import/students', methods=['POST'])
    def import_students():
        """Import students from CSV file"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if not file.filename.endswith('.csv'):
                return jsonify({'error': 'Only CSV files are supported'}), 400
            
            # Process CSV file
            import csv
            import io
            
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            
            imported_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_input, start=2):
                try:
                    student = Student(
                        student_id=row.get('Student ID', '').strip(),
                        name=row.get('Name', '').strip(),
                        department=row.get('Department', '').strip(),
                        semester=int(row.get('Semester', 0)),
                        email=row.get('Email', '').strip(),
                        phone=row.get('Phone', '').strip()
                    )
                    
                    if not student.student_id or not student.name:
                        errors.append(f'Row {row_num}: Student ID and Name are required')
                        continue
                    
                    # Check if student already exists
                    existing = Student.get_by_id(student.student_id)
                    if existing:
                        errors.append(f'Row {row_num}: Student ID {student.student_id} already exists')
                        continue
                    
                    student.save()
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f'Row {row_num}: {str(e)}')
            
            return jsonify({
                'success': True,
                'imported_count': imported_count,
                'errors': errors
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            stats = db_manager.get_statistics()
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'database': 'connected',
                'version': '1.0.0',
                'stats': stats
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    return app

# Create the application
app = create_app()

if __name__ == '__main__':
    # Initialize database
    db_manager.init_database()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
"""
Frontend routes for the Examination Seating System
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from werkzeug.security import check_password_hash
from functools import wraps
import os
from backend.database import db_manager
from backend.models import Student, Subject, Room, Exam, Invigilator
from backend.seating_algorithm import seating_algorithm
from backend.reports import report_generator

# Create blueprints for different modules
auth_bp = Blueprint('auth', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
students_bp = Blueprint('students', __name__, url_prefix='/students')
subjects_bp = Blueprint('subjects', __name__, url_prefix='/subjects')
rooms_bp = Blueprint('rooms', __name__, url_prefix='/rooms')
exams_bp = Blueprint('exams', __name__, url_prefix='/exams')
seating_bp = Blueprint('seating', __name__, url_prefix='/seating')
invigilators_bp = Blueprint('invigilators', __name__, url_prefix='/invigilators')
reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@auth_bp.route('/')
def index():
    if 'admin_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        query = 'SELECT * FROM admins WHERE email = ? AND is_active = 1'
        admin = db_manager.execute_query(query, (email,), fetch_one=True)
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['name']
            session['admin_email'] = admin['email']
            session['admin_role'] = admin['role']
            
            # Log login action
            db_manager.log_action(admin['id'], 'login', ip_address=request.remote_addr, 
                                user_agent=request.headers.get('User-Agent'))
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    if 'admin_id' in session:
        # Log logout action
        db_manager.log_action(session['admin_id'], 'logout', ip_address=request.remote_addr)
    
    session.clear()
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('auth.login'))

# Dashboard Routes
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    stats = db_manager.get_statistics()
    
    # Get recent activities
    recent_students = db_manager.execute_query(
        'SELECT * FROM students WHERE is_active = 1 ORDER BY created_at DESC LIMIT 5'
    )
    
    recent_exams = db_manager.execute_query('''
        SELECT e.*, s.subject_name 
        FROM exams e 
        JOIN subjects s ON e.subject_code = s.subject_code 
        WHERE e.is_active = 1
        ORDER BY e.exam_date DESC, e.start_time DESC 
        LIMIT 5
    ''')
    
    return render_template('dashboard.html', stats=stats, 
                         recent_students=recent_students, recent_exams=recent_exams)

# Student Routes
@students_bp.route('/')
@login_required
def list_students():
    department = request.args.get('department', '')
    semester = request.args.get('semester', '')
    search = request.args.get('search', '')
    
    students = Student.get_all(department=department if department else None,
                              semester=int(semester) if semester else None,
                              search=search if search else None)
    
    # Get filter options
    departments = db_manager.execute_query('SELECT DISTINCT department FROM students WHERE is_active = 1 ORDER BY department')
    semesters = db_manager.execute_query('SELECT DISTINCT semester FROM students WHERE is_active = 1 ORDER BY semester')
    
    return render_template('students/list.html', 
                         students=students, 
                         departments=departments,
                         semesters=semesters,
                         current_department=department,
                         current_semester=semester,
                         current_search=search)

@students_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        try:
            student = Student(
                student_id=request.form['student_id'],
                name=request.form['name'],
                department=request.form['department'],
                semester=int(request.form['semester']),
                email=request.form.get('email', ''),
                phone=request.form.get('phone', ''),
                address=request.form.get('address', ''),
                guardian_name=request.form.get('guardian_name', ''),
                guardian_phone=request.form.get('guardian_phone', '')
            )
            
            # Check if student ID already exists
            existing = Student.get_by_id(student.student_id)
            if existing:
                flash('Student ID already exists!', 'error')
                return render_template('students/add.html', subjects=Subject.get_all())
            
            student.save()
            
            # Enroll in subjects
            subjects = request.form.getlist('subjects')
            for subject_code in subjects:
                if subject_code:
                    student.enroll_subject(subject_code)
            
            # Log action
            db_manager.log_action(session['admin_id'], 'create', 'students', student.student_id)
            
            flash('Student added successfully!', 'success')
            return redirect(url_for('students.list_students'))
            
        except Exception as e:
            flash(f'Error adding student: {str(e)}', 'error')
    
    subjects = Subject.get_all()
    return render_template('students/add.html', subjects=subjects)

@students_bp.route('/edit/<student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.get_by_id(student_id)
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('students.list_students'))
    
    if request.method == 'POST':
        try:
            student.name = request.form['name']
            student.department = request.form['department']
            student.semester = int(request.form['semester'])
            student.email = request.form.get('email', '')
            student.phone = request.form.get('phone', '')
            student.address = request.form.get('address', '')
            student.guardian_name = request.form.get('guardian_name', '')
            student.guardian_phone = request.form.get('guardian_phone', '')
            
            student.save()
            
            # Update subject enrollments
            current_subjects = [s['subject_code'] for s in student.get_subjects()]
            new_subjects = request.form.getlist('subjects')
            
            # Unenroll from removed subjects
            for subject_code in current_subjects:
                if subject_code not in new_subjects:
                    student.unenroll_subject(subject_code)
            
            # Enroll in new subjects
            for subject_code in new_subjects:
                if subject_code and subject_code not in current_subjects:
                    student.enroll_subject(subject_code)
            
            # Log action
            db_manager.log_action(session['admin_id'], 'update', 'students', student_id)
            
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students.list_students'))
            
        except Exception as e:
            flash(f'Error updating student: {str(e)}', 'error')
    
    subjects = Subject.get_all()
    student_subjects = [s['subject_code'] for s in student.get_subjects()]
    
    return render_template('students/edit.html', student=student, subjects=subjects, 
                         student_subjects=student_subjects)

@students_bp.route('/delete/<student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    try:
        student = Student.get_by_id(student_id)
        if student:
            student.delete()
            
            # Log action
            db_manager.log_action(session['admin_id'], 'delete', 'students', student_id)
            
            flash('Student deleted successfully!', 'success')
        else:
            flash('Student not found!', 'error')
    except Exception as e:
        flash(f'Error deleting student: {str(e)}', 'error')
    
    return redirect(url_for('students.list_students'))

# Subject Routes
@subjects_bp.route('/')
@login_required
def list_subjects():
    department = request.args.get('department', '')
    semester = request.args.get('semester', '')
    search = request.args.get('search', '')
    
    subjects = Subject.get_all(department=department if department else None,
                              semester=int(semester) if semester else None,
                              search=search if search else None)
    
    # Get filter options
    departments = db_manager.execute_query('SELECT DISTINCT department FROM subjects WHERE is_active = 1 ORDER BY department')
    semesters = db_manager.execute_query('SELECT DISTINCT semester FROM subjects WHERE is_active = 1 ORDER BY semester')
    
    return render_template('subjects/list.html', 
                         subjects=subjects, 
                         departments=departments,
                         semesters=semesters,
                         current_department=department,
                         current_semester=semester,
                         current_search=search)

@subjects_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_subject():
    if request.method == 'POST':
        try:
            subject = Subject(
                subject_code=request.form['subject_code'],
                subject_name=request.form['subject_name'],
                department=request.form['department'],
                semester=int(request.form['semester']),
                credits=int(request.form.get('credits', 3)),
                subject_type=request.form.get('subject_type', 'theory')
            )
            
            # Check if subject code already exists
            existing = Subject.get_by_code(subject.subject_code)
            if existing:
                flash('Subject code already exists!', 'error')
                return render_template('subjects/add.html')
            
            subject.save()
            
            # Log action
            db_manager.log_action(session['admin_id'], 'create', 'subjects', subject.subject_code)
            
            flash('Subject added successfully!', 'success')
            return redirect(url_for('subjects.list_subjects'))
            
        except Exception as e:
            flash(f'Error adding subject: {str(e)}', 'error')
    
    return render_template('subjects/add.html')

@subjects_bp.route('/edit/<subject_code>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_code):
    subject = Subject.get_by_code(subject_code)
    if not subject:
        flash('Subject not found!', 'error')
        return redirect(url_for('subjects.list_subjects'))
    
    if request.method == 'POST':
        try:
            subject.subject_name = request.form['subject_name']
            subject.department = request.form['department']
            subject.semester = int(request.form['semester'])
            subject.credits = int(request.form.get('credits', 3))
            subject.subject_type = request.form.get('subject_type', 'theory')
            
            subject.save()
            
            # Log action
            db_manager.log_action(session['admin_id'], 'update', 'subjects', subject_code)
            
            flash('Subject updated successfully!', 'success')
            return redirect(url_for('subjects.list_subjects'))
            
        except Exception as e:
            flash(f'Error updating subject: {str(e)}', 'error')
    
    return render_template('subjects/edit.html', subject=subject)

@subjects_bp.route('/delete/<subject_code>', methods=['POST'])
@login_required
def delete_subject(subject_code):
    try:
        subject = Subject.get_by_code(subject_code)
        if subject:
            subject.delete()
            
            # Log action
            db_manager.log_action(session['admin_id'], 'delete', 'subjects', subject_code)
            
            flash('Subject deleted successfully!', 'success')
        else:
            flash('Subject not found!', 'error')
    except Exception as e:
        flash(f'Error deleting subject: {str(e)}', 'error')
    
    return redirect(url_for('subjects.list_subjects'))

# Room Routes
@rooms_bp.route('/')
@login_required
def list_rooms():
    building = request.args.get('building', '')
    floor = request.args.get('floor', '')
    
    rooms = Room.get_all(building=building if building else None,
                        floor=int(floor) if floor else None)
    
    # Get filter options
    buildings = db_manager.execute_query('SELECT DISTINCT building FROM rooms WHERE is_active = 1 AND building IS NOT NULL ORDER BY building')
    floors = db_manager.execute_query('SELECT DISTINCT floor FROM rooms WHERE is_active = 1 AND floor IS NOT NULL ORDER BY floor')
    
    return render_template('rooms/list.html', 
                         rooms=rooms, 
                         buildings=buildings,
                         floors=floors,
                         current_building=building,
                         current_floor=floor)

@rooms_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_room():
    if request.method == 'POST':
        try:
            room = Room(
                room_id=request.form['room_id'],
                name=request.form['name'],
                rows=int(request.form['rows']),
                cols=int(request.form['cols']),
                capacity=int(request.form['capacity']),
                building=request.form.get('building', ''),
                floor=int(request.form['floor']) if request.form.get('floor') else None,
                room_type=request.form.get('room_type', 'classroom'),
                facilities=request.form.get('facilities', '')
            )
            
            # Check if room ID already exists
            existing = Room.get_by_id(room.room_id)
            if existing:
                flash('Room ID already exists!', 'error')
                return render_template('rooms/add.html')
            
            room.save()
            
            # Log action
            db_manager.log_action(session['admin_id'], 'create', 'rooms', room.room_id)
            
            flash('Room added successfully!', 'success')
            return redirect(url_for('rooms.list_rooms'))
            
        except Exception as e:
            flash(f'Error adding room: {str(e)}', 'error')
    
    return render_template('rooms/add.html')

@rooms_bp.route('/edit/<room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    room = Room.get_by_id(room_id)
    if not room:
        flash('Room not found!', 'error')
        return redirect(url_for('rooms.list_rooms'))
    
    if request.method == 'POST':
        try:
            room.name = request.form['name']
            room.rows = int(request.form['rows'])
            room.cols = int(request.form['cols'])
            room.capacity = int(request.form['capacity'])
            room.building = request.form.get('building', '')
            room.floor = int(request.form['floor']) if request.form.get('floor') else None
            room.room_type = request.form.get('room_type', 'classroom')
            room.facilities = request.form.get('facilities', '')
            
            room.save()
            
            # Log action
            db_manager.log_action(session['admin_id'], 'update', 'rooms', room_id)
            
            flash('Room updated successfully!', 'success')
            return redirect(url_for('rooms.list_rooms'))
            
        except Exception as e:
            flash(f'Error updating room: {str(e)}', 'error')
    
    return render_template('rooms/edit.html', room=room)

@rooms_bp.route('/delete/<room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    try:
        room = Room.get_by_id(room_id)
        if room:
            room.delete()
            
            # Log action
            db_manager.log_action(session['admin_id'], 'delete', 'rooms', room_id)
            
            flash('Room deleted successfully!', 'success')
        else:
            flash('Room not found!', 'error')
    except Exception as e:
        flash(f'Error deleting room: {str(e)}', 'error')
    
    return redirect(url_for('rooms.list_rooms'))

# Exam Routes
@exams_bp.route('/')
@login_required
def list_exams():
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    exams = Exam.get_all(date_from=date_from if date_from else None,
                        date_to=date_to if date_to else None)
    
    # Filter by search if provided
    if search:
        exams = [e for e in exams if search.lower() in e.subject_code.lower()]
    
    # Get subject names
    exam_data = []
    for exam in exams:
        subject = Subject.get_by_code(exam.subject_code)
        exam_dict = exam.to_dict()
        exam_dict['subject_name'] = subject.subject_name if subject else 'Unknown'
        exam_data.append(exam_dict)
    
    return render_template('exams/list.html', 
                         exams=exam_data,
                         current_date_from=date_from,
                         current_date_to=date_to,
                         current_search=search)

@exams_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_exam():
    if request.method == 'POST':
        try:
            exam = Exam(
                subject_code=request.form['subject_code'],
                exam_date=request.form['exam_date'],
                start_time=request.form['start_time'],
                end_time=request.form['end_time'],
                duration=int(request.form['duration']),
                session_type=request.form.get('session_type', 'regular'),
                exam_type=request.form.get('exam_type', 'written'),
                instructions=request.form.get('instructions', '')
            )
            
            exam.save()
            
            # Log action
            db_manager.log_action(session['admin_id'], 'create', 'exams', str(exam.id) if hasattr(exam, 'id') else 'new')
            
            flash('Exam scheduled successfully!', 'success')
            return redirect(url_for('exams.list_exams'))
            
        except Exception as e:
            flash(f'Error scheduling exam: {str(e)}', 'error')
    
    subjects = Subject.get_all()
    return render_template('exams/add.html', subjects=subjects)

# Seating Routes
@seating_bp.route('/')
@login_required
def seating_index():
    # Get exams with seating status
    query = '''
        SELECT e.*, s.subject_name,
               COUNT(sa.id) as student_count,
               CASE WHEN COUNT(sa.id) > 0 THEN 1 ELSE 0 END as seating_generated
        FROM exams e 
        JOIN subjects s ON e.subject_code = s.subject_code 
        LEFT JOIN seating_arrangements sa ON e.exam_date = sa.exam_date 
            AND e.start_time = sa.session_time AND sa.is_active = 1
        WHERE e.is_active = 1
        GROUP BY e.id, e.subject_code, e.exam_date, e.start_time, e.end_time, 
                 e.duration, e.session_type, s.subject_name
        ORDER BY e.exam_date, e.start_time
    '''
    exams = db_manager.execute_query(query)
    
    # Get statistics
    stats = seating_algorithm.get_arrangement_statistics('2024-01-01', '09:00')  # Default stats
    
    return render_template('seating/index.html', exams=exams, **stats)

@seating_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate_seating():
    if request.method == 'POST':
        try:
            exam_date = request.form['exam_date']
            session_time = request.form['session_time']
            arrangement_type = request.form.get('arrangement_type', 'mixed')
            conflict_avoidance = request.form.get('conflict_avoidance', 'strict')
            room_utilization = request.form.get('room_utilization', 'optimal')
            preserve_existing = 'preserve_existing' in request.form
            
            # Generate seating arrangement
            result = seating_algorithm.generate_seating_arrangement(
                exam_date, session_time, arrangement_type, 
                conflict_avoidance, room_utilization, preserve_existing
            )
            
            if result['success']:
                # Log action
                db_manager.log_action(session['admin_id'], 'generate_seating', 
                                    'seating_arrangements', result['arrangement_id'])
                
                flash(result['message'], 'success')
                return redirect(url_for('seating.view_seating', date=exam_date, session=session_time))
            else:
                flash(result['message'], 'error')
                
        except Exception as e:
            flash(f'Error generating seating arrangement: {str(e)}', 'error')
    
    return render_template('seating/generate.html')

@seating_bp.route('/view')
@login_required
def view_seating():
    exam_date = request.args.get('date')
    session_time = request.args.get('session')
    
    if not exam_date or not session_time:
        flash('Please select exam date and session!', 'error')
        return redirect(url_for('seating.seating_index'))
    
    # Get seating arrangements
    query = '''
        SELECT sa.*, s.name as student_name, sub.subject_name, r.name as room_name,
               r.rows, r.cols, r.capacity
        FROM seating_arrangements sa
        JOIN students s ON sa.student_id = s.student_id
        JOIN subjects sub ON sa.subject_code = sub.subject_code
        JOIN rooms r ON sa.room_id = r.room_id
        WHERE sa.exam_date = ? AND sa.session_time = ? AND sa.is_active = 1
        ORDER BY sa.room_id, sa.seat_row, sa.seat_col
    '''
    arrangements = db_manager.execute_query(query, (exam_date, session_time))
    
    # Get rooms used
    query_rooms = '''
        SELECT DISTINCT r.*
        FROM rooms r
        JOIN seating_arrangements sa ON r.room_id = sa.room_id
        WHERE sa.exam_date = ? AND sa.session_time = ? AND sa.is_active = 1
    '''
    rooms = db_manager.execute_query(query_rooms, (exam_date, session_time))
    
    # Get statistics
    stats = seating_algorithm.get_arrangement_statistics(exam_date, session_time)
    
    return render_template('seating/view.html', 
                         arrangements=arrangements, 
                         rooms=rooms,
                         exam_date=exam_date,
                         session_time=session_time,
                         **stats)

# Invigilator Routes
@invigilators_bp.route('/')
@login_required
def list_invigilators():
    department = request.args.get('department', '')
    search = request.args.get('search', '')
    
    invigilators = Invigilator.get_all(department=department if department else None,
                                     search=search if search else None)
    
    # Get filter options
    departments = db_manager.execute_query('SELECT DISTINCT department FROM invigilators WHERE is_active = 1 AND department IS NOT NULL ORDER BY department')
    
    return render_template('invigilators/list.html', 
                         invigilators=invigilators, 
                         departments=departments,
                         current_department=department,
                         current_search=search)

@invigilators_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_invigilator():
    if request.method == 'POST':
        try:
            # Prepare preferences and availability as JSON
            preferences = request.form.getlist('preferences')
            availability = request.form.getlist('availability')
            
            invigilator = Invigilator(
                staff_id=request.form['staff_id'],
                name=request.form['name'],
                email=request.form.get('email', ''),
                phone=request.form.get('phone', ''),
                department=request.form.get('department', ''),
                designation=request.form.get('designation', ''),
                experience=int(request.form.get('experience', 0)),
                max_assignments=int(request.form.get('max_assignments', 2)),
                preferences=','.join(preferences) if preferences else '',
                availability=','.join(availability) if availability else ''
            )
            
            # Check if staff ID already exists
            existing = Invigilator.get_by_id(invigilator.staff_id)
            if existing:
                flash('Staff ID already exists!', 'error')
                return render_template('invigilators/add.html')
            
            invigilator.save()
            
            # Log action
            db_manager.log_action(session['admin_id'], 'create', 'invigilators', invigilator.staff_id)
            
            flash('Invigilator added successfully!', 'success')
            return redirect(url_for('invigilators.list_invigilators'))
            
        except Exception as e:
            flash(f'Error adding invigilator: {str(e)}', 'error')
    
    return render_template('invigilators/add.html')

# Reports Routes
@reports_bp.route('/')
@login_required
def reports_index():
    # Get system statistics for the dashboard
    stats = db_manager.get_statistics()
    return render_template('reports/index.html', **stats)

@reports_bp.route('/generate', methods=['POST'])
@login_required
def generate_report():
    try:
        report_type = request.form['reportType']
        format_type = request.form.get('format', 'pdf')
        date_from = request.form.get('dateFrom')
        date_to = request.form.get('dateTo')
        
        if report_type == 'seating_arrangement':
            if not date_from:
                flash('Please select exam date for seating arrangement report', 'error')
                return redirect(url_for('reports.reports_index'))
            
            session_time = request.form.get('sessionTime', '09:00')
            result = report_generator.generate_seating_arrangement_report(
                date_from, session_time, format_type
            )
        elif report_type == 'student_slips':
            if not date_from:
                flash('Please select exam date for student admit cards', 'error')
                return redirect(url_for('reports.reports_index'))
            
            session_time = request.form.get('sessionTime', '09:00')
            result = report_generator.generate_student_admit_cards(
                date_from, session_time, format_type
            )
        elif report_type == 'room_utilization':
            result = report_generator.generate_room_utilization_report(
                date_from, date_to, format_type
            )
        elif report_type == 'duty_roster':
            result = report_generator.generate_invigilator_duty_roster(
                date_from, date_to, format_type
            )
        else:
            flash('Invalid report type', 'error')
            return redirect(url_for('reports.reports_index'))
        
        if result['success']:
            # Log action
            db_manager.log_action(session['admin_id'], 'generate_report', 
                                'reports', result['filename'])
            
            flash(result['message'], 'success')
            return send_file(result['filepath'], as_attachment=True, 
                           download_name=result['filename'])
        else:
            flash(result['message'], 'error')
            
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
    
    return redirect(url_for('reports.reports_index'))

# Register all blueprints
def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(exams_bp)
    app.register_blueprint(seating_bp)
    app.register_blueprint(invigilators_bp)
    app.register_blueprint(reports_bp)
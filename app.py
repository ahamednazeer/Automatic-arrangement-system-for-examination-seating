from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
import csv
import json
from datetime import datetime, timedelta
import uuid
from functools import wraps
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect('exam_system.db')
    cursor = conn.cursor()
    
    # Admin table (add is_active column)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Add is_active column if it doesn't exist (for existing DBs)
    try:
        cursor.execute('ALTER TABLE admins ADD COLUMN is_active INTEGER DEFAULT 1')
    except sqlite3.OperationalError:
        pass
    
    # Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            semester INTEGER NOT NULL,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT UNIQUE NOT NULL,
            subject_name TEXT NOT NULL,
            department TEXT NOT NULL,
            semester INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Student-Subject mapping
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (subject_code) REFERENCES subjects (subject_code)
        )
    ''')
    
    # Rooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            rows INTEGER NOT NULL,
            cols INTEGER NOT NULL,
            capacity INTEGER NOT NULL,
            building TEXT,
            floor INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Exams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT NOT NULL,
            exam_date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            duration INTEGER NOT NULL,
            session_type TEXT DEFAULT 'regular',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_code) REFERENCES subjects (subject_code)
        )
    ''')
    
    # Seating arrangements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seating_arrangements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            room_id TEXT NOT NULL,
            seat_row INTEGER NOT NULL,
            seat_col INTEGER NOT NULL,
            seat_number TEXT,
            exam_date DATE NOT NULL,
            session_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (subject_code) REFERENCES subjects (subject_code),
            FOREIGN KEY (room_id) REFERENCES rooms (room_id)
        )
    ''')
    
    # Add seat_number column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE seating_arrangements ADD COLUMN seat_number TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Invigilators table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invigilators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Invigilator assignments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invigilator_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id TEXT NOT NULL,
            room_id TEXT NOT NULL,
            exam_date DATE NOT NULL,
            session_time TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (staff_id) REFERENCES invigilators (staff_id),
            FOREIGN KEY (room_id) REFERENCES rooms (room_id),
            FOREIGN KEY (subject_code) REFERENCES subjects (subject_code)
        )
    ''')
    
    # Create default admin if not exists
    cursor.execute('SELECT COUNT(*) FROM admins')
    if cursor.fetchone()[0] == 0:
        default_password = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO admins (email, password_hash, name, is_active)
            VALUES (?, ?, ?, ?)
        ''', ('admin@exam.com', default_password, 'System Administrator', 1))
    
    conn.commit()
    conn.close()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('exam_system.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        admin = conn.execute(
            'SELECT * FROM admins WHERE email = ?', (email,)
        ).fetchone()
        conn.close()


        if admin and check_password_hash(admin['password_hash'], password):
            is_active = admin['is_active'] if 'is_active' in admin.keys() else 1
            try:
                is_active = int(is_active)
            except Exception:
                is_active = 0
            if is_active == 1:
                session['admin_id'] = admin['id']
                session['admin_name'] = admin['name']
                session['admin_email'] = admin['email']
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                # Do not set session, just show error on login page
                flash('Your account is inactive. Please contact the administrator.', 'error')
                return render_template('login.html')
        else:
            flash('Invalid email or password!', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    
    # Get statistics
    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_rooms = conn.execute('SELECT COUNT(*) FROM rooms').fetchone()[0]
    total_subjects = conn.execute('SELECT COUNT(*) FROM subjects').fetchone()[0]
    total_exams = conn.execute('SELECT COUNT(*) FROM exams').fetchone()[0]
    
    # Get recent activities
    recent_students = conn.execute(
        'SELECT * FROM students ORDER BY created_at DESC LIMIT 5'
    ).fetchall()
    
    recent_exams = conn.execute('''
        SELECT e.*, s.subject_name 
        FROM exams e 
        JOIN subjects s ON e.subject_code = s.subject_code 
        ORDER BY e.exam_date DESC, e.start_time DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    stats = {
        'total_students': total_students,
        'total_rooms': total_rooms,
        'total_subjects': total_subjects,
        'total_exams': total_exams
    }
    
    return render_template('dashboard.html', stats=stats, 
                         recent_students=recent_students, recent_exams=recent_exams)

# Student Management Routes
@app.route('/students', strict_slashes=False)
@login_required
def students():
    conn = get_db_connection()
    
    # Get filter parameters
    department = request.args.get('department', '')
    semester = request.args.get('semester', '')
    search = request.args.get('search', '')
    
    # Build query
    query = '''
        SELECT s.*, GROUP_CONCAT(sub.subject_code) as subjects
        FROM students s
        LEFT JOIN student_subjects ss ON s.student_id = ss.student_id
        LEFT JOIN subjects sub ON ss.subject_code = sub.subject_code
        WHERE 1=1
    '''
    params = []
    
    if department:
        query += ' AND s.department = ?'
        params.append(department)
    
    if semester:
        query += ' AND s.semester = ?'
        params.append(semester)
    
    if search:
        query += ' AND (s.name LIKE ? OR s.student_id LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    
    query += ' GROUP BY s.id ORDER BY s.created_at DESC'
    
    students = conn.execute(query, params).fetchall()
    
    # Get departments and semesters for filters
    departments = conn.execute('SELECT DISTINCT department FROM students ORDER BY department').fetchall()
    semesters = conn.execute('SELECT DISTINCT semester FROM students ORDER BY semester').fetchall()
    
    conn.close()
    
    return render_template('students/list.html', 
                         students=students, 
                         departments=departments,
                         semesters=semesters,
                         current_department=department,
                         current_semester=semester,
                         current_search=search)

@app.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        department = request.form['department']
        semester = int(request.form['semester'])
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        subjects = request.form.getlist('subjects')
        
        conn = get_db_connection()
        
        try:
            # Check if student ID already exists
            existing = conn.execute('SELECT id FROM students WHERE student_id = ?', (student_id,)).fetchone()
            if existing:
                flash('Student ID already exists!', 'error')
                return render_template('students/add.html')
            
            # Insert student
            conn.execute('''
                INSERT INTO students (student_id, name, department, semester, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (student_id, name, department, semester, email, phone))
            
            # Insert student-subject mappings
            for subject_code in subjects:
                if subject_code:
                    conn.execute('''
                        INSERT INTO student_subjects (student_id, subject_code)
                        VALUES (?, ?)
                    ''', (student_id, subject_code))
            
            conn.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('students'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error adding student: {str(e)}', 'error')
        finally:
            conn.close()
    
    # Get subjects for the form
    conn = get_db_connection()
    subjects = conn.execute('SELECT * FROM subjects ORDER BY subject_name').fetchall()
    conn.close()
    
    return render_template('students/add.html', subjects=subjects)

@app.route('/students/edit/<student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        semester = int(request.form['semester'])
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        subjects = request.form.getlist('subjects')
        
        try:
            # Update student
            conn.execute('''
                UPDATE students 
                SET name = ?, department = ?, semester = ?, email = ?, phone = ?
                WHERE student_id = ?
            ''', (name, department, semester, email, phone, student_id))
            
            # Delete existing subject mappings
            conn.execute('DELETE FROM student_subjects WHERE student_id = ?', (student_id,))
            
            # Insert new subject mappings
            for subject_code in subjects:
                if subject_code:
                    conn.execute('''
                        INSERT INTO student_subjects (student_id, subject_code)
                        VALUES (?, ?)
                    ''', (student_id, subject_code))
            
            conn.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error updating student: {str(e)}', 'error')
    
    # Get student data
    student = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('students'))
    
    # Get student's subjects
    student_subjects = conn.execute('''
        SELECT subject_code FROM student_subjects WHERE student_id = ?
    ''', (student_id,)).fetchall()
    student_subject_codes = [s['subject_code'] for s in student_subjects]
    
    # Get all subjects
    subjects = conn.execute('SELECT * FROM subjects ORDER BY subject_name').fetchall()
    
    conn.close()
    
    return render_template('students/edit.html', 
                         student=student, 
                         subjects=subjects,
                         student_subject_codes=student_subject_codes)

@app.route('/students/delete/<student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    conn = get_db_connection()
    
    try:
        # Delete student-subject mappings first
        conn.execute('DELETE FROM student_subjects WHERE student_id = ?', (student_id,))
        
        # Delete seating arrangements
        conn.execute('DELETE FROM seating_arrangements WHERE student_id = ?', (student_id,))
        
        # Delete student
        conn.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
        
        conn.commit()
        flash('Student deleted successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting student: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('students'))

@app.route('/students/import', methods=['GET', 'POST'])
@login_required
def import_students():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            try:
                # Save uploaded file
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Process CSV
                conn = get_db_connection()
                imported_count = 0
                error_count = 0
                
                with open(filepath, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        try:
                            # Check if student already exists
                            existing = conn.execute(
                                'SELECT id FROM students WHERE student_id = ?', 
                                (row['student_id'],)
                            ).fetchone()
                            
                            if not existing:
                                conn.execute('''
                                    INSERT INTO students (student_id, name, department, semester, email, phone)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (
                                    row['student_id'],
                                    row['name'],
                                    row['department'],
                                    int(row['semester']),
                                    row.get('email', ''),
                                    row.get('phone', '')
                                ))
                                imported_count += 1
                            else:
                                error_count += 1
                                
                        except Exception as e:
                            error_count += 1
                            continue
                
                conn.commit()
                conn.close()
                
                # Clean up uploaded file
                os.remove(filepath)
                
                flash(f'Import completed! {imported_count} students imported, {error_count} errors.', 'success')
                return redirect(url_for('students'))
                
            except Exception as e:
                flash(f'Error importing file: {str(e)}', 'error')
        else:
            flash('Please upload a CSV file!', 'error')
    
    return render_template('students/import.html')

@app.route('/students/assign-subjects', methods=['GET', 'POST'])
@login_required
def assign_subjects_bulk():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file!', 'error')
            return redirect(request.url)
        import csv, io
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        reader = csv.DictReader(stream)
        required_headers = ['student_id', 'subject_code']
        headers = [h.lower().strip() for h in (reader.fieldnames or [])]
        missing = [h for h in required_headers if h not in headers]
        if missing:
            flash(f'Invalid CSV: missing headers: {", ".join(missing)}', 'error')
            return redirect(request.url)
        conn = get_db_connection()
        assigned = skipped = errors = 0
        for row in reader:
            try:
                row_l = {(k.lower().strip() if k else ''): (v.strip() if v else '') for k, v in row.items()}
                sid = row_l.get('student_id', '')
                scode = row_l.get('subject_code', '')
                if not sid or not scode:
                    errors += 1
                    continue
                student = conn.execute('SELECT id FROM students WHERE student_id = ?', (sid,)).fetchone()
                subject = conn.execute('SELECT id FROM subjects WHERE subject_code = ?', (scode,)).fetchone()
                if not student or not subject:
                    skipped += 1
                    continue
                existing = conn.execute('SELECT id FROM student_subjects WHERE student_id = ? AND subject_code = ?', (sid, scode)).fetchone()
                if existing:
                    skipped += 1
                    continue
                conn.execute('INSERT INTO student_subjects (student_id, subject_code) VALUES (?, ?)', (sid, scode))
                assigned += 1
            except Exception:
                errors += 1
        conn.commit()
        conn.close()
        flash(f'Assignment completed: {assigned} added, {skipped} skipped, {errors} errors.', 'success' if assigned > 0 and errors == 0 else 'warning')
        return redirect(url_for('students'))
    return render_template('students/assign_subjects.html')

@app.route('/students/bulk-assign', methods=['GET', 'POST'])
@login_required
def bulk_assign_ui():
    conn = get_db_connection()
    if request.method == 'POST':
        student_ids = request.form.getlist('student_ids')
        subject_codes = request.form.getlist('subject_codes')
        if not student_ids or not subject_codes:
            conn.close()
            flash('Please select at least one student and one subject.', 'error')
            return redirect(request.url)
        assigned = skipped = 0
        try:
            for sid in student_ids:
                # validate student exists
                st = conn.execute('SELECT id FROM students WHERE student_id = ?', (sid,)).fetchone()
                if not st:
                    continue
                for scode in subject_codes:
                    # validate subject exists
                    sub = conn.execute('SELECT id FROM subjects WHERE subject_code = ?', (scode,)).fetchone()
                    if not sub:
                        continue
                    existing = conn.execute('SELECT id FROM student_subjects WHERE student_id = ? AND subject_code = ?', (sid, scode)).fetchone()
                    if existing:
                        skipped += 1
                        continue
                    conn.execute('INSERT INTO student_subjects (student_id, subject_code) VALUES (?, ?)', (sid, scode))
                    assigned += 1
            conn.commit()
            flash(f'Bulk assignment complete: {assigned} added, {skipped} skipped.', 'success' if assigned else 'info')
            return redirect(url_for('students'))
        except Exception as e:
            conn.rollback()
            flash(f'Error during bulk assign: {str(e)}', 'error')
        finally:
            conn.close()
    else:
        # Load students and subjects for selection with optional filters
        s_dept = request.args.get('s_department', '')
        s_sem = request.args.get('s_semester', '')
        s_search = request.args.get('s_search', '')
        sub_dept = request.args.get('sub_department', '')
        sub_sem = request.args.get('sub_semester', '')
        sub_search = request.args.get('sub_search', '')

        # Students query with filters
        s_query = 'SELECT student_id, name, department, semester FROM students WHERE 1=1'
        s_params = []
        if s_dept:
            s_query += ' AND department = ?'
            s_params.append(s_dept)
        if s_sem:
            try:
                s_query += ' AND semester = ?'
                s_params.append(int(s_sem))
            except ValueError:
                pass
        if s_search:
            s_query += ' AND (name LIKE ? OR student_id LIKE ?)'
            like_val = f"%{s_search}%"
            s_params.extend([like_val, like_val])
        s_query += ' ORDER BY department, semester, name'
        students = conn.execute(s_query, s_params).fetchall()

        # Subjects query with filters
        sub_query = 'SELECT subject_code, subject_name, department, semester FROM subjects WHERE 1=1'
        sub_params = []
        if sub_dept:
            sub_query += ' AND department = ?'
            sub_params.append(sub_dept)
        if sub_sem:
            try:
                sub_query += ' AND semester = ?'
                sub_params.append(int(sub_sem))
            except ValueError:
                pass
        if sub_search:
            sub_query += ' AND (subject_name LIKE ? OR subject_code LIKE ?)'
            like_val2 = f"%{sub_search}%"
            sub_params.extend([like_val2, like_val2])
        sub_query += ' ORDER BY department, semester, subject_name'
        subjects = conn.execute(sub_query, sub_params).fetchall()

        # Dropdown options
        student_departments = conn.execute('SELECT DISTINCT department FROM students ORDER BY department').fetchall()
        student_semesters = conn.execute('SELECT DISTINCT semester FROM students ORDER BY semester').fetchall()
        subject_departments = conn.execute('SELECT DISTINCT department FROM subjects ORDER BY department').fetchall()
        subject_semesters = conn.execute('SELECT DISTINCT semester FROM subjects ORDER BY semester').fetchall()

        conn.close()
        return render_template(
            'students/bulk_assign.html',
            students=students,
            subjects=subjects,
            student_departments=student_departments,
            student_semesters=student_semesters,
            subject_departments=subject_departments,
            subject_semesters=subject_semesters,
            current_s_department=s_dept,
            current_s_semester=str(s_sem),
            current_s_search=s_search,
            current_sub_department=sub_dept,
            current_sub_semester=str(sub_sem),
            current_sub_search=sub_search,
        )

# Room Management Routes
@app.route('/rooms', strict_slashes=False)
@login_required
def rooms():
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms ORDER BY created_at DESC').fetchall()
    conn.close()
    
    return render_template('rooms/list.html', rooms=rooms)

@app.route('/rooms/add', methods=['GET', 'POST'])
@login_required
def add_room():
    if request.method == 'POST':
        room_id = request.form['room_id']
        name = request.form['name']
        rows = int(request.form['rows'])
        cols = int(request.form['cols'])
        capacity = rows * cols
        building = request.form.get('building', '')
        floor = request.form.get('floor', 0)
        
        conn = get_db_connection()
        
        try:
            # Check if room ID already exists
            existing = conn.execute('SELECT id FROM rooms WHERE room_id = ?', (room_id,)).fetchone()
            if existing:
                flash('Room ID already exists!', 'error')
                return render_template('rooms/add.html')
            
            conn.execute('''
                INSERT INTO rooms (room_id, name, rows, cols, capacity, building, floor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (room_id, name, rows, cols, capacity, building, floor))
            
            conn.commit()
            flash('Room added successfully!', 'success')
            return redirect(url_for('rooms'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error adding room: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('rooms/add.html')

@app.route('/rooms/edit/<room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        rows = int(request.form['rows'])
        cols = int(request.form['cols'])
        capacity = rows * cols
        building = request.form.get('building', '')
        floor = request.form.get('floor', 0)
        
        try:
            conn.execute('''
                UPDATE rooms 
                SET name = ?, rows = ?, cols = ?, capacity = ?, building = ?, floor = ?
                WHERE room_id = ?
            ''', (name, rows, cols, capacity, building, floor, room_id))
            
            conn.commit()
            flash('Room updated successfully!', 'success')
            return redirect(url_for('rooms'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error updating room: {str(e)}', 'error')
        finally:
            conn.close()
    
    # Get room details for editing
    room = conn.execute('SELECT * FROM rooms WHERE room_id = ?', (room_id,)).fetchone()
    if not room:
        flash('Room not found!', 'error')
        return redirect(url_for('rooms'))
    
    conn.close()
    return render_template('rooms/edit.html', room=room)

@app.route('/rooms/delete/<room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    conn = get_db_connection()
    
    try:
        # First, check if room is being used in any seating arrangements
        existing_arrangements = conn.execute(
            'SELECT COUNT(*) as count FROM seating_arrangements WHERE room_id = ?', 
            (room_id,)
        ).fetchone()
        
        if existing_arrangements['count'] > 0:
            flash('Cannot delete room: It is currently being used in seating arrangements!', 'error')
        else:
            conn.execute('DELETE FROM rooms WHERE room_id = ?', (room_id,))
            conn.commit()
            flash('Room deleted successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting room: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('rooms'))

# Subject Management Routes
@app.route('/subjects', strict_slashes=False)
@login_required
def subjects():
    conn = get_db_connection()
    subjects = conn.execute('SELECT * FROM subjects ORDER BY department, semester, subject_name').fetchall()
    conn.close()
    
    return render_template('subjects/list.html', subjects=subjects)

@app.route('/subjects/add', methods=['GET', 'POST'])
@login_required
def add_subject():
    if request.method == 'POST':
        subject_code = request.form['subject_code']
        subject_name = request.form['subject_name']
        department = request.form['department']
        semester = int(request.form['semester'])
        
        conn = get_db_connection()
        
        try:
            # Check if subject code already exists
            existing = conn.execute('SELECT id FROM subjects WHERE subject_code = ?', (subject_code,)).fetchone()
            if existing:
                flash('Subject code already exists!', 'error')
                return render_template('subjects/add.html')
            
            conn.execute('''
                INSERT INTO subjects (subject_code, subject_name, department, semester)
                VALUES (?, ?, ?, ?)
            ''', (subject_code, subject_name, department, semester))
            
            conn.commit()
            flash('Subject added successfully!', 'success')
            return redirect(url_for('subjects'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error adding subject: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('subjects/add.html')

@app.route('/subjects/edit/<subject_code>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_code):
    conn = get_db_connection()
    
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        department = request.form['department']
        semester = int(request.form['semester'])
        
        try:
            conn.execute('''
                UPDATE subjects 
                SET subject_name = ?, department = ?, semester = ?
                WHERE subject_code = ?
            ''', (subject_name, department, semester, subject_code))
            
            conn.commit()
            flash('Subject updated successfully!', 'success')
            return redirect(url_for('subjects'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error updating subject: {str(e)}', 'error')
        finally:
            conn.close()
    
    # Get subject details for editing
    subject = conn.execute('SELECT * FROM subjects WHERE subject_code = ?', (subject_code,)).fetchone()
    if not subject:
        flash('Subject not found!', 'error')
        return redirect(url_for('subjects'))
    
    conn.close()
    return render_template('subjects/edit.html', subject=subject)

@app.route('/subjects/delete/<subject_code>', methods=['POST'])
@login_required
def delete_subject(subject_code):
    conn = get_db_connection()
    
    try:
        # First, check if subject is being used in any exams
        existing_exams = conn.execute(
            'SELECT COUNT(*) as count FROM exams WHERE subject_code = ?', 
            (subject_code,)
        ).fetchone()
        
        if existing_exams['count'] > 0:
            flash('Cannot delete subject: It is currently being used in scheduled exams!', 'error')
        else:
            conn.execute('DELETE FROM subjects WHERE subject_code = ?', (subject_code,))
            conn.commit()
            flash('Subject deleted successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting subject: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('subjects'))

# Exam Management Routes
@app.route('/exams', strict_slashes=False)
@login_required
def exams():
    conn = get_db_connection()
    exams = conn.execute('''
        SELECT e.*, s.subject_name 
        FROM exams e 
        JOIN subjects s ON e.subject_code = s.subject_code 
        ORDER BY e.exam_date DESC, e.start_time DESC
    ''').fetchall()
    conn.close()
    
    return render_template('exams/list.html', exams=exams)

@app.route('/exams/add', methods=['GET', 'POST'])
@login_required
def add_exam():
    if request.method == 'POST':
        subject_code = request.form['subject_code']
        exam_date = request.form['exam_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        duration = int(request.form['duration'])
        
        conn = get_db_connection()
        
        try:
            conn.execute('''
                INSERT INTO exams (subject_code, exam_date, start_time, end_time, duration)
                VALUES (?, ?, ?, ?, ?)
            ''', (subject_code, exam_date, start_time, end_time, duration))
            
            conn.commit()
            flash('Exam scheduled successfully!', 'success')
            return redirect(url_for('exams'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error scheduling exam: {str(e)}', 'error')
        finally:
            conn.close()
    
    # Get subjects for the form
    conn = get_db_connection()
    subjects = conn.execute('SELECT * FROM subjects ORDER BY subject_name').fetchall()
    conn.close()
    
    return render_template('exams/add.html', subjects=subjects)

@app.route('/exams/edit/<int:exam_id>', methods=['GET', 'POST'])
@login_required
def edit_exam(exam_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        subject_code = request.form['subject_code']
        exam_date = request.form['exam_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        duration = int(request.form['duration'])
        
        try:
            conn.execute('''
                UPDATE exams 
                SET subject_code = ?, exam_date = ?, start_time = ?, end_time = ?, duration = ?
                WHERE id = ?
            ''', (subject_code, exam_date, start_time, end_time, duration, exam_id))
            
            conn.commit()
            flash('Exam updated successfully!', 'success')
            return redirect(url_for('exams'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error updating exam: {str(e)}', 'error')
        finally:
            conn.close()
    
    # Get exam details for editing with subject name
    exam = conn.execute('''
        SELECT e.*, s.subject_name 
        FROM exams e 
        JOIN subjects s ON e.subject_code = s.subject_code 
        WHERE e.id = ?
    ''', (exam_id,)).fetchone()
    if not exam:
        flash('Exam not found!', 'error')
        return redirect(url_for('exams'))
    
    # Get subjects for the form
    subjects = conn.execute('SELECT * FROM subjects ORDER BY subject_name').fetchall()
    conn.close()
    
    return render_template('exams/edit.html', exam=exam, subjects=subjects)

@app.route('/exams/delete/<int:exam_id>', methods=['POST'])
@login_required
def delete_exam(exam_id):
    conn = get_db_connection()
    
    try:
        # First, delete any associated seating arrangements
        conn.execute('DELETE FROM seating_arrangements WHERE subject_code = (SELECT subject_code FROM exams WHERE id = ?) AND exam_date = (SELECT exam_date FROM exams WHERE id = ?) AND session_time = (SELECT start_time FROM exams WHERE id = ?)', (exam_id, exam_id, exam_id))
        
        # Then delete the exam
        conn.execute('DELETE FROM exams WHERE id = ?', (exam_id,))
        
        conn.commit()
        flash('Exam deleted successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting exam: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('exams'))

# Seating Management Routes
@app.route('/seating', strict_slashes=False)
@login_required
def seating():
    conn = get_db_connection()
    
    # Get exams for selection
    exams = conn.execute('''
        SELECT e.*, s.subject_name 
        FROM exams e 
        JOIN subjects s ON e.subject_code = s.subject_code 
        ORDER BY e.exam_date, e.start_time
    ''').fetchall()
    
    conn.close()
    
    return render_template('seating/index.html', exams=exams)

@app.route('/seating/generate', methods=['GET', 'POST'])
@login_required
def generate_seating():
    if request.method == 'POST':
        exam_date = request.form['exam_date']
        session_time = request.form['session_time']
        numbering_scheme = request.form.get('numbering_scheme', 'alpha_numeric')
        
        # Generate seating arrangement
        success, error_msg = generate_seating_arrangement(exam_date, session_time, numbering_scheme)
        
        if success:
            flash('Seating arrangement generated successfully!', 'success')
            return redirect(url_for('view_seating', date=exam_date, session=session_time))
        else:
            flash(f'Error generating seating arrangement: {error_msg}', 'error')
    
    return render_template('seating/generate.html')

# Invigilator Management Routes
@app.route('/invigilators', strict_slashes=False)
@login_required
def invigilators():
    conn = get_db_connection()
    
    # Get invigilators with assignment counts
    invigilators = conn.execute('''
        SELECT i.*, 
               COUNT(ia.id) as assignment_count,
               CASE WHEN COUNT(ia.id) > 0 THEN 0 ELSE 1 END as is_available
        FROM invigilators i
        LEFT JOIN invigilator_assignments ia ON i.staff_id = ia.staff_id AND ia.is_active = 1
        WHERE i.is_active = 1
        GROUP BY i.id, i.staff_id, i.name, i.email, i.phone, i.department
        ORDER BY i.name
    ''').fetchall()
    
    conn.close()
    
    return render_template('invigilators/list.html', invigilators=invigilators)

@app.route('/invigilators/add', methods=['GET', 'POST'])
@login_required
def add_invigilator():
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        name = request.form['name']
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        department = request.form.get('department', '')
        
        conn = get_db_connection()
        
        try:
            # Check if staff ID already exists
            existing = conn.execute('SELECT id FROM invigilators WHERE staff_id = ?', (staff_id,)).fetchone()
            if existing:
                flash('Staff ID already exists!', 'error')
                return render_template('invigilators/add.html')
            
            conn.execute('''
                INSERT INTO invigilators (staff_id, name, email, phone, department)
                VALUES (?, ?, ?, ?, ?)
            ''', (staff_id, name, email, phone, department))
            
            conn.commit()
            flash('Invigilator added successfully!', 'success')
            return redirect(url_for('invigilators'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error adding invigilator: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('invigilators/add.html')

@app.route('/invigilators/edit/<staff_id>', methods=['GET', 'POST'])
@login_required
def edit_invigilator(staff_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        department = request.form['department']
        
        try:
            conn.execute('''
                UPDATE invigilators 
                SET name = ?, email = ?, phone = ?, department = ?
                WHERE staff_id = ?
            ''', (name, email, phone, department, staff_id))
            
            conn.commit()
            flash('Invigilator updated successfully!', 'success')
            return redirect(url_for('invigilators'))
            
        except Exception as e:
            conn.rollback()
            flash(f'Error updating invigilator: {str(e)}', 'error')
        finally:
            conn.close()
    
    # Get invigilator details for editing
    invigilator = conn.execute('SELECT * FROM invigilators WHERE staff_id = ?', (staff_id,)).fetchone()
    if not invigilator:
        flash('Invigilator not found!', 'error')
        return redirect(url_for('invigilators'))
    
    conn.close()
    return render_template('invigilators/edit.html', invigilator=invigilator)

@app.route('/invigilators/delete/<staff_id>', methods=['POST'])
@login_required
def delete_invigilator(staff_id):
    conn = get_db_connection()
    
    try:
        # First, check if invigilator is assigned to any sessions
        existing_assignments = conn.execute(
            'SELECT COUNT(*) as count FROM invigilator_assignments WHERE staff_id = ?', 
            (staff_id,)
        ).fetchone()
        
        if existing_assignments['count'] > 0:
            flash('Cannot delete invigilator: They are currently assigned to exam sessions!', 'error')
        else:
            conn.execute('DELETE FROM invigilators WHERE staff_id = ?', (staff_id,))
            conn.commit()
            flash('Invigilator deleted successfully!', 'success')
        
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting invigilator: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('invigilators'))

@app.route('/invigilators/schedule/<staff_id>')
@login_required
def invigilator_schedule(staff_id):
    conn = get_db_connection()
    
    # Get invigilator details
    invigilator = conn.execute('SELECT * FROM invigilators WHERE staff_id = ?', (staff_id,)).fetchone()
    if not invigilator:
        flash('Invigilator not found!', 'error')
        return redirect(url_for('invigilators'))
    
    # Get invigilator assignments with exam and room details
    assignments = conn.execute('''
        SELECT ia.*, e.exam_date, e.start_time, e.end_time, e.duration,
               s.subject_name, s.subject_code, r.name as room_name
        FROM invigilator_assignments ia
        JOIN exams e ON ia.subject_code = e.subject_code 
                     AND ia.exam_date = e.exam_date 
                     AND ia.session_time = e.start_time
        JOIN subjects s ON ia.subject_code = s.subject_code
        JOIN rooms r ON ia.room_id = r.room_id
        WHERE ia.staff_id = ?
        ORDER BY ia.exam_date, ia.session_time
    ''', (staff_id,)).fetchall()
    
    conn.close()
    
    return render_template('invigilators/schedule.html', invigilator=invigilator, assignments=assignments)

@app.route('/invigilators/assign', methods=['POST'])
@login_required
def assign_invigilators():
    """Auto assign invigilators to exam sessions"""
    try:
        exam_date = request.form.get('assign_date')
        session_time = request.form.get('assign_session')
        strategy = request.form.get('strategy', 'balanced')
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if not exam_date or not session_time:
            error_msg = 'Please provide exam date and session time!'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('invigilators'))
        
        conn = get_db_connection()
        
        # Get exams for the specified date and session
        exams = conn.execute('''
            SELECT e.*, s.subject_name, s.department 
            FROM exams e 
            JOIN subjects s ON e.subject_code = s.subject_code 
            WHERE e.exam_date = ? AND e.start_time = ?
        ''', (exam_date, session_time)).fetchall()
        
        if not exams:
            error_msg = f'No exams found for {exam_date} at {session_time}!'
            conn.close()
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('invigilators'))
        
        # Get available rooms for seating arrangements
        rooms_with_students = conn.execute('''
            SELECT DISTINCT sa.room_id, r.name as room_name, COUNT(sa.student_id) as student_count
            FROM seating_arrangements sa
            JOIN rooms r ON sa.room_id = r.room_id
            WHERE sa.exam_date = ? AND sa.session_time = ? AND sa.is_active = 1
            GROUP BY sa.room_id, r.name
        ''', (exam_date, session_time)).fetchall()
        
        if not rooms_with_students:
            error_msg = f'No seating arrangements found for {exam_date} at {session_time}. Please generate seating first!'
            conn.close()
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('invigilators'))
        
        # Get available invigilators (not already assigned to this session)
        available_invigilators = conn.execute('''
            SELECT i.* FROM invigilators i
            WHERE i.is_active = 1 
            AND i.staff_id NOT IN (
                SELECT ia.staff_id FROM invigilator_assignments ia
                WHERE ia.exam_date = ? AND ia.session_time = ? AND ia.is_active = 1
            )
            ORDER BY i.name
        ''', (exam_date, session_time)).fetchall()
        
        if not available_invigilators:
            error_msg = f'No available invigilators for {exam_date} at {session_time}!'
            conn.close()
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('invigilators'))
        
        # Assign invigilators based on strategy
        assignments_made = 0
        
        if strategy == 'balanced':
            # Assign one invigilator per room in round-robin fashion
            invigilator_index = 0
            for room in rooms_with_students:
                if invigilator_index >= len(available_invigilators):
                    invigilator_index = 0
                
                invigilator = available_invigilators[invigilator_index]
                
                # Check for conflicts (same invigilator, same time, different room)
                conflict = conn.execute('''
                    SELECT COUNT(*) as count FROM invigilator_assignments 
                    WHERE staff_id = ? AND exam_date = ? AND session_time = ? AND is_active = 1
                ''', (invigilator['staff_id'], exam_date, session_time)).fetchone()
                
                if conflict['count'] == 0:
                    # Get the primary subject for this room (most students)
                    primary_subject = conn.execute('''
                        SELECT sa.subject_code, COUNT(*) as count
                        FROM seating_arrangements sa
                        WHERE sa.room_id = ? AND sa.exam_date = ? AND sa.session_time = ? AND sa.is_active = 1
                        GROUP BY sa.subject_code
                        ORDER BY count DESC
                        LIMIT 1
                    ''', (room['room_id'], exam_date, session_time)).fetchone()
                    
                    if primary_subject:
                        conn.execute('''
                            INSERT INTO invigilator_assignments 
                            (staff_id, room_id, exam_date, session_time, subject_code, is_active)
                            VALUES (?, ?, ?, ?, ?, 1)
                        ''', (invigilator['staff_id'], room['room_id'], exam_date, 
                              session_time, primary_subject['subject_code']))
                        assignments_made += 1
                
                invigilator_index += 1
        
        conn.commit()
        conn.close()
        
        if assignments_made > 0:
            success_msg = f'Successfully assigned {assignments_made} invigilators to exam sessions!'
            if is_ajax:
                return jsonify({'success': True, 'message': success_msg, 'assignments_made': assignments_made})
            flash(success_msg, 'success')
        else:
            warning_msg = 'No assignments could be made. Please check for conflicts or availability.'
            if is_ajax:
                return jsonify({'success': False, 'message': warning_msg}), 400
            flash(warning_msg, 'warning')
        
        if is_ajax:
            return jsonify({'success': True, 'redirect': url_for('invigilators')})
        return redirect(url_for('invigilators'))
        
    except Exception as e:
        error_msg = f'Error assigning invigilators: {str(e)}'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg}), 500
        flash(error_msg, 'error')
        return redirect(url_for('invigilators'))

@app.route('/invigilators/assign/manual', methods=['POST'])
@login_required
def manual_assign_invigilator():
    """Manually assign an invigilator to a specific session"""
    try:
        staff_id = request.form.get('staff_id')
        room_id = request.form.get('room_id')
        exam_date = request.form.get('exam_date')
        session_time = request.form.get('session_time')
        subject_code = request.form.get('subject_code')
        
        if not all([staff_id, room_id, exam_date, session_time, subject_code]):
            flash('All fields are required for manual assignment!', 'error')
            return redirect(url_for('invigilators'))
        
        conn = get_db_connection()
        
        # Check for conflicts
        conflict = conn.execute('''
            SELECT ia.*, r.name as room_name, i.name as invigilator_name
            FROM invigilator_assignments ia
            JOIN rooms r ON ia.room_id = r.room_id
            JOIN invigilators i ON ia.staff_id = i.staff_id
            WHERE ia.staff_id = ? AND ia.exam_date = ? AND ia.session_time = ? AND ia.is_active = 1
        ''', (staff_id, exam_date, session_time)).fetchone()
        
        if conflict:
            flash(f'Warning: {conflict["invigilator_name"]} is already assigned to {conflict["room_name"]} at {session_time} on {exam_date}!', 'error')
            conn.close()
            return redirect(url_for('invigilators'))
        
        # Insert assignment
        conn.execute('''
            INSERT INTO invigilator_assignments 
            (staff_id, room_id, exam_date, session_time, subject_code, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (staff_id, room_id, exam_date, session_time, subject_code))
        
        conn.commit()
        conn.close()
        
        flash('Invigilator assigned successfully!', 'success')
        return redirect(url_for('invigilators'))
        
    except Exception as e:
        flash(f'Error in manual assignment: {str(e)}', 'error')
        return redirect(url_for('invigilators'))

@app.route('/invigilators/unassign/<int:assignment_id>', methods=['POST'])
@login_required
def unassign_invigilator(assignment_id):
    """Remove an invigilator assignment"""
    try:
        conn = get_db_connection()
        
        # Soft delete the assignment
        conn.execute('''
            UPDATE invigilator_assignments 
            SET is_active = 0 
            WHERE id = ?
        ''', (assignment_id,))
        
        conn.commit()
        conn.close()
        
        flash('Invigilator assignment removed successfully!', 'success')
        return redirect(url_for('invigilators'))
        
    except Exception as e:
        flash(f'Error removing assignment: {str(e)}', 'error')
        return redirect(url_for('invigilators'))

# Reports Routes
@app.route('/reports', strict_slashes=False)
@login_required
def reports():
    return render_template('reports/index.html')

# Profile and Settings Routes
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# Seating Algorithm
def generate_seating_arrangement(exam_date, session_time, numbering_scheme='alpha_numeric'):
    """Generate automatic seating arrangement"""
    try:
        conn = get_db_connection()
        
# Get exams for the given date and session
        exams = conn.execute('''
            SELECT e.*, s.subject_name, s.department 
            FROM exams e 
            JOIN subjects s ON e.subject_code = s.subject_code 
            WHERE e.exam_date = ? AND e.start_time = ?
        ''', (exam_date, session_time)).fetchall()
        
        if not exams:
            conn.close()
            return False, f"No exams found for {exam_date} at {session_time}"
        
        # Get students for these exams
        students = []
        for exam in exams:
            exam_students = conn.execute('''
                SELECT s.*, ss.subject_code, sub.department as subject_dept
                FROM students s
                JOIN student_subjects ss ON s.student_id = ss.student_id
                JOIN subjects sub ON ss.subject_code = sub.subject_code
                WHERE ss.subject_code = ?
            ''', (exam['subject_code'],)).fetchall()
            # Convert Row objects to dictionaries
            for student in exam_students:
                students.append(dict(student))
        
        if not students:
            conn.close()
            return False, "No students found for the selected exams"
        
        # Get available rooms
        rooms_raw = conn.execute('SELECT * FROM rooms ORDER BY capacity DESC').fetchall()
        rooms = [dict(room) for room in rooms_raw]
        
        if not rooms:
            conn.close()
            return False, "No rooms available"
        
        # Clear existing arrangements for this session
        conn.execute('''
            DELETE FROM seating_arrangements 
            WHERE exam_date = ? AND session_time = ?
        ''', (exam_date, session_time))
        
        # Implement seating algorithm
        allocated_students = []
        room_occupancy = {}
        
        # Initialize room occupancy
        for room in rooms:
            room_occupancy[room['room_id']] = []
            for row in range(room['rows']):
                room_occupancy[room['room_id']].append([None] * room['cols'])
        
        # Shuffle students for random distribution
        students_list = list(students)
        random.shuffle(students_list)
        
        for student in students_list:
            allocated = False
            
            for room in rooms:
                if allocated:
                    break
                
                room_grid = room_occupancy[room['room_id']]
                
                for row in range(room['rows']):
                    if allocated:
                        break
                    
                    for col in range(room['cols']):
                        if room_grid[row][col] is None:
                            # Check for conflicts with adjacent seats
                            if not has_conflict(student, room_grid, row, col):
                                # Allocate seat
                                room_grid[row][col] = student
                                
                                # Generate seat number
                                seat_number = generate_seat_number(room['room_id'], row + 1, col + 1, numbering_scheme, room['cols'])
                                
                                # Insert into database
                                conn.execute('''
                                    INSERT INTO seating_arrangements 
                                    (student_id, subject_code, room_id, seat_row, seat_col, seat_number, exam_date, session_time)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    student['student_id'],
                                    student['subject_code'],
                                    room['room_id'],
                                    row + 1,
                                    col + 1,
                                    seat_number,
                                    exam_date,
                                    session_time
                                ))
                                
                                allocated = True
                                allocated_students.append(student)
                                break
        

        
        conn.commit()
        conn.close()
        
        if len(allocated_students) < len(students):
            return False, f"Could only allocate {len(allocated_students)} out of {len(students)} students. Insufficient room capacity or too many conflicts."
        
        return True, "Success"
        
    except Exception as e:
        print(f"Error in seating arrangement: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def has_conflict(student, room_grid, row, col):
    """Check if placing student at this position creates a conflict"""
    # Check adjacent seats for same subject (more lenient than department)
    # Only check immediate left, right, front, and back (not diagonals)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        
        if (0 <= new_row < len(room_grid) and 
            0 <= new_col < len(room_grid[0]) and 
            room_grid[new_row][new_col] is not None):
            
            adjacent_student = room_grid[new_row][new_col]
            
            # Only prevent same subject students from sitting adjacent
            # (Allow same department but different subjects)
            if adjacent_student['subject_code'] == student['subject_code']:
                return True
    
    return False

def generate_seat_number(room_id, row, col, numbering_scheme='sequential', max_cols=20):
    """Generate seat number based on different numbering schemes"""
    if numbering_scheme == 'sequential':
        # Simple sequential numbering: 1, 2, 3, ...
        return str((row - 1) * max_cols + col)
    elif numbering_scheme == 'row_col':
        # Row-Column format: R1C1, R1C2, etc.
        return f"R{row}C{col}"
    elif numbering_scheme == 'alpha_numeric':
        # Alphabetic rows, numeric columns: A1, A2, B1, B2, etc.
        if row <= 26:
            row_letter = chr(ord('A') + row - 1)
        else:
            # For rows beyond Z, use AA, AB, etc.
            first_letter = chr(ord('A') + (row - 27) // 26)
            second_letter = chr(ord('A') + (row - 27) % 26)
            row_letter = first_letter + second_letter
        return f"{row_letter}{col}"
    elif numbering_scheme == 'room_prefix':
        # Room prefix with sequential: ROOM1-001, ROOM1-002, etc.
        seat_num = (row - 1) * max_cols + col
        return f"{room_id}-{seat_num:03d}"
    else:
        # Default to sequential
        return str((row - 1) * max_cols + col)

@app.route('/seating/regenerate-numbers', methods=['POST'])
@login_required
def regenerate_seat_numbers():
    """Regenerate seat numbers for existing arrangements"""
    exam_date = request.form.get('exam_date')
    session_time = request.form.get('session_time')
    numbering_scheme = request.form.get('numbering_scheme', 'alpha_numeric')
    
    if not exam_date or not session_time:
        flash('Missing exam date or session time!', 'error')
        return redirect(url_for('seating'))
    
    try:
        conn = get_db_connection()
        
        # Get existing arrangements with room info
        arrangements = conn.execute('''
            SELECT sa.*, r.cols as room_cols 
            FROM seating_arrangements sa
            JOIN rooms r ON sa.room_id = r.room_id
            WHERE sa.exam_date = ? AND sa.session_time = ?
            ORDER BY sa.room_id, sa.seat_row, sa.seat_col
        ''', (exam_date, session_time)).fetchall()
        
        if not arrangements:
            flash('No seating arrangements found for the selected session!', 'error')
            conn.close()
            return redirect(url_for('seating'))
        
        # Update seat numbers
        for arrangement in arrangements:
            new_seat_number = generate_seat_number(
                arrangement['room_id'], 
                arrangement['seat_row'], 
                arrangement['seat_col'], 
                numbering_scheme,
                arrangement['room_cols']
            )
            
            conn.execute('''
                UPDATE seating_arrangements 
                SET seat_number = ? 
                WHERE id = ?
            ''', (new_seat_number, arrangement['id']))
        
        conn.commit()
        conn.close()
        
        flash(f'Seat numbers regenerated successfully using {numbering_scheme} scheme!', 'success')
        return redirect(url_for('view_seating', date=exam_date, session=session_time))
        
    except Exception as e:
        flash(f'Error regenerating seat numbers: {str(e)}', 'error')
        return redirect(url_for('seating'))

@app.route('/seating/session-exams')
@login_required
def seating_session_exams():
    exam_date = request.args.get('date')
    session_time = request.args.get('session')
    if not exam_date or not session_time:
        return jsonify({'success': False, 'message': 'date and session are required'}), 400

    conn = get_db_connection()
    try:
        rows = conn.execute('''
            SELECT e.subject_code, s.subject_name,
                   (
                     SELECT COUNT(*)
                     FROM student_subjects ss
                     JOIN students st ON st.student_id = ss.student_id
                     WHERE ss.subject_code = e.subject_code
                   ) AS student_count
            FROM exams e
            JOIN subjects s ON e.subject_code = s.subject_code
            WHERE e.exam_date = ? AND e.start_time = ?
            ORDER BY s.subject_name
        ''', (exam_date, session_time)).fetchall()
        exams = [{
            'subject_code': r['subject_code'],
            'subject_name': r['subject_name'],
            'student_count': r['student_count']
        } for r in rows]
        return jsonify({'success': True, 'exams': exams})
    finally:
        conn.close()

@app.route('/seating/view')
@login_required
def view_seating():
    exam_date = request.args.get('date')
    session_time = request.args.get('session')
    
    if not exam_date or not session_time:
        flash('Please select exam date and session!', 'error')
        return redirect(url_for('seating'))
    
    conn = get_db_connection()
    
    # Get seating arrangements
    arrangements_rows = conn.execute('''
        SELECT sa.*, s.name as student_name, sub.subject_name, r.name as room_name
        FROM seating_arrangements sa
        JOIN students s ON sa.student_id = s.student_id
        JOIN subjects sub ON sa.subject_code = sub.subject_code
        JOIN rooms r ON sa.room_id = r.room_id
        WHERE sa.exam_date = ? AND sa.session_time = ?
        ORDER BY sa.room_id, sa.seat_number, sa.seat_row, sa.seat_col
    ''', (exam_date, session_time)).fetchall()
    
    # Convert Row objects to dictionaries for JSON serialization
    arrangements = [dict(row) for row in arrangements_rows]
    
    # Get rooms used
    rooms_rows = conn.execute('''
        SELECT DISTINCT r.*
        FROM rooms r
        JOIN seating_arrangements sa ON r.room_id = sa.room_id
        WHERE sa.exam_date = ? AND sa.session_time = ?
    ''', (exam_date, session_time)).fetchall()
    
    # Convert Room objects to dictionaries for consistency
    rooms = [dict(row) for row in rooms_rows]
    
    conn.close()
    
    return render_template('seating/view.html', 
                         arrangements=arrangements, 
                         rooms=rooms,
                         exam_date=exam_date,
                         session_time=session_time)

# Initialize database when app starts
init_db()

if __name__ == '__main__':
    app.run(debug=True)
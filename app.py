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
    
    # Admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
            exam_date DATE NOT NULL,
            session_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (subject_code) REFERENCES subjects (subject_code),
            FOREIGN KEY (room_id) REFERENCES rooms (room_id)
        )
    ''')
    
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
            INSERT INTO admins (email, password_hash, name)
            VALUES (?, ?, ?)
        ''', ('admin@exam.com', default_password, 'System Administrator'))
    
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
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['name']
            session['admin_email'] = admin['email']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
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
@app.route('/students')
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

# Room Management Routes
@app.route('/rooms')
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

# Subject Management Routes
@app.route('/subjects')
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

# Exam Management Routes
@app.route('/exams')
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

# Seating Management Routes
@app.route('/seating')
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
        
        # Generate seating arrangement
        success = generate_seating_arrangement(exam_date, session_time)
        
        if success:
            flash('Seating arrangement generated successfully!', 'success')
            return redirect(url_for('view_seating', date=exam_date, session=session_time))
        else:
            flash('Error generating seating arrangement!', 'error')
    
    return render_template('seating/generate.html')

# Invigilator Management Routes
@app.route('/invigilators')
@login_required
def invigilators():
    conn = get_db_connection()
    invigilators = conn.execute('SELECT * FROM invigilators ORDER BY name').fetchall()
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

# Reports Routes
@app.route('/reports')
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
def generate_seating_arrangement(exam_date, session_time):
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
            return False
        
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
            students.extend(exam_students)
        
        # Get available rooms
        rooms = conn.execute('SELECT * FROM rooms ORDER BY capacity DESC').fetchall()
        
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
            for row in range(1, room['rows'] + 1):
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
                                
                                # Insert into database
                                conn.execute('''
                                    INSERT INTO seating_arrangements 
                                    (student_id, subject_code, room_id, seat_row, seat_col, exam_date, session_time)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''', (
                                    student['student_id'],
                                    student['subject_code'],
                                    room['room_id'],
                                    row + 1,
                                    col + 1,
                                    exam_date,
                                    session_time
                                ))
                                
                                allocated = True
                                allocated_students.append(student)
                                break
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error in seating arrangement: {e}")
        return False

def has_conflict(student, room_grid, row, col):
    """Check if placing student at this position creates a conflict"""
    # Check adjacent seats for same department/subject
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for dr, dc in directions:
        new_row, new_col = row + dr, col + dc
        
        if (0 <= new_row < len(room_grid) and 
            0 <= new_col < len(room_grid[0]) and 
            room_grid[new_row][new_col] is not None):
            
            adjacent_student = room_grid[new_row][new_col]
            
            # Check for same department or subject conflict
            if (adjacent_student['department'] == student['department'] or
                adjacent_student['subject_code'] == student['subject_code']):
                return True
    
    return False

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
    arrangements = conn.execute('''
        SELECT sa.*, s.name as student_name, sub.subject_name, r.name as room_name
        FROM seating_arrangements sa
        JOIN students s ON sa.student_id = s.student_id
        JOIN subjects sub ON sa.subject_code = sub.subject_code
        JOIN rooms r ON sa.room_id = r.room_id
        WHERE sa.exam_date = ? AND sa.session_time = ?
        ORDER BY sa.room_id, sa.seat_row, sa.seat_col
    ''', (exam_date, session_time)).fetchall()
    
    # Get rooms used
    rooms = conn.execute('''
        SELECT DISTINCT r.*
        FROM rooms r
        JOIN seating_arrangements sa ON r.room_id = sa.room_id
        WHERE sa.exam_date = ? AND sa.session_time = ?
    ''', (exam_date, session_time)).fetchall()
    
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
"""
Database management module for the Examination Seating System
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='exam_system.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Admin table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT DEFAULT 'admin',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                address TEXT,
                guardian_name TEXT,
                guardian_phone TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                credits INTEGER DEFAULT 3,
                subject_type TEXT DEFAULT 'theory',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Student-Subject mapping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                subject_code TEXT NOT NULL,
                enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (student_id) REFERENCES students (student_id),
                FOREIGN KEY (subject_code) REFERENCES subjects (subject_code),
                UNIQUE(student_id, subject_code)
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
                room_type TEXT DEFAULT 'classroom',
                facilities TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                exam_type TEXT DEFAULT 'written',
                instructions TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                arrangement_id TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (student_id),
                FOREIGN KEY (subject_code) REFERENCES subjects (subject_code),
                FOREIGN KEY (room_id) REFERENCES rooms (room_id),
                UNIQUE(room_id, seat_row, seat_col, exam_date, session_time)
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
                designation TEXT,
                experience INTEGER DEFAULT 0,
                max_assignments INTEGER DEFAULT 2,
                preferences TEXT,
                availability TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                assignment_type TEXT DEFAULT 'primary',
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES invigilators (staff_id),
                FOREIGN KEY (room_id) REFERENCES rooms (room_id),
                FOREIGN KEY (subject_code) REFERENCES subjects (subject_code)
            )
        ''')
        
        # System logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id TEXT,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES admins (id)
            )
        ''')
        
        # Reports table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                file_path TEXT,
                file_size INTEGER,
                parameters TEXT,
                generated_by INTEGER,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (generated_by) REFERENCES admins (id)
            )
        ''')
        
        # Create default admin if not exists
        cursor.execute('SELECT COUNT(*) FROM admins')
        if cursor.fetchone()[0] == 0:
            default_password = generate_password_hash('admin123')
            cursor.execute('''
                INSERT INTO admins (email, password_hash, name, role)
                VALUES (?, ?, ?, ?)
            ''', ('admin@exam.com', default_password, 'System Administrator', 'super_admin'))
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_department ON students(department)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_students_semester ON students(semester)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subjects_department ON subjects(department)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_exams_date ON exams(exam_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_seating_exam ON seating_arrangements(exam_date, session_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_seating_room ON seating_arrangements(room_id)')
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=True):
        """Execute a query and return results"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor
            else:
                conn.commit()
                result = cursor.rowcount
            
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def log_action(self, user_id, action, table_name=None, record_id=None, 
                   old_values=None, new_values=None, ip_address=None, user_agent=None):
        """Log user actions for audit trail"""
        query = '''
            INSERT INTO system_logs 
            (user_id, action, table_name, record_id, old_values, new_values, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (user_id, action, table_name, record_id, old_values, new_values, ip_address, user_agent)
        self.execute_query(query, params)
    
    def backup_database(self, backup_path=None):
        """Create a backup of the database"""
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f'backup_exam_system_{timestamp}.db'
        
        # Create backup directory if it doesn't exist
        backup_dir = os.path.dirname(backup_path) or 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy database file
        import shutil
        shutil.copy2(self.db_path, backup_path)
        return backup_path
    
    def get_statistics(self):
        """Get system statistics"""
        stats = {}
        
        # Count records in each table
        tables = ['students', 'subjects', 'rooms', 'exams', 'invigilators', 'seating_arrangements']
        for table in tables:
            count = self.execute_query(f'SELECT COUNT(*) FROM {table}', fetch_one=True)[0]
            stats[f'total_{table}'] = count
        
        # Additional statistics
        stats['active_students'] = self.execute_query(
            'SELECT COUNT(*) FROM students WHERE is_active = 1', fetch_one=True)[0]
        
        stats['upcoming_exams'] = self.execute_query(
            'SELECT COUNT(*) FROM exams WHERE exam_date >= date("now")', fetch_one=True)[0]
        
        stats['rooms_in_use'] = self.execute_query(
            '''SELECT COUNT(DISTINCT room_id) FROM seating_arrangements 
               WHERE exam_date >= date("now")''', fetch_one=True)[0]
        
        return stats

# Global database instance
db_manager = DatabaseManager()
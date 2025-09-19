"""
Data models for the Examination Seating System
"""
from datetime import datetime
from backend.database import db_manager
import json

class BaseModel:
    """Base model class with common functionality"""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {key: value for key, value in self.__dict__.items() 
                if not key.startswith('_')}
    
    def save(self):
        """Save model to database"""
        raise NotImplementedError("Subclasses must implement save method")
    
    def delete(self):
        """Delete model from database"""
        raise NotImplementedError("Subclasses must implement delete method")

class Student(BaseModel):
    """Student model"""
    
    def __init__(self, student_id=None, name=None, department=None, semester=None, 
                 email=None, phone=None, address=None, guardian_name=None, 
                 guardian_phone=None, is_active=True, **kwargs):
        super().__init__(**kwargs)
        self.student_id = student_id
        self.name = name
        self.department = department
        self.semester = semester
        self.email = email
        self.phone = phone
        self.address = address
        self.guardian_name = guardian_name
        self.guardian_phone = guardian_phone
        self.is_active = is_active
    
    def save(self):
        """Save student to database"""
        if hasattr(self, 'id') and self.id:
            # Update existing student
            query = '''
                UPDATE students SET name=?, department=?, semester=?, email=?, 
                phone=?, address=?, guardian_name=?, guardian_phone=?, is_active=?, 
                updated_at=CURRENT_TIMESTAMP WHERE student_id=?
            '''
            params = (self.name, self.department, self.semester, self.email, 
                     self.phone, self.address, self.guardian_name, self.guardian_phone, 
                     self.is_active, self.student_id)
        else:
            # Insert new student
            query = '''
                INSERT INTO students (student_id, name, department, semester, email, 
                phone, address, guardian_name, guardian_phone, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (self.student_id, self.name, self.department, self.semester, 
                     self.email, self.phone, self.address, self.guardian_name, 
                     self.guardian_phone, self.is_active)
        
        return db_manager.execute_query(query, params)
    
    def delete(self):
        """Soft delete student"""
        query = 'UPDATE students SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE student_id=?'
        return db_manager.execute_query(query, (self.student_id,))
    
    def get_subjects(self):
        """Get subjects enrolled by this student"""
        query = '''
            SELECT s.* FROM subjects s
            JOIN student_subjects ss ON s.subject_code = ss.subject_code
            WHERE ss.student_id = ? AND ss.is_active = 1
        '''
        return db_manager.execute_query(query, (self.student_id,))
    
    def enroll_subject(self, subject_code):
        """Enroll student in a subject"""
        query = '''
            INSERT OR REPLACE INTO student_subjects (student_id, subject_code, is_active)
            VALUES (?, ?, 1)
        '''
        return db_manager.execute_query(query, (self.student_id, subject_code))
    
    def unenroll_subject(self, subject_code):
        """Unenroll student from a subject"""
        query = '''
            UPDATE student_subjects SET is_active=0 
            WHERE student_id=? AND subject_code=?
        '''
        return db_manager.execute_query(query, (self.student_id, subject_code))
    
    @classmethod
    def get_by_id(cls, student_id):
        """Get student by ID"""
        query = 'SELECT * FROM students WHERE student_id = ? AND is_active = 1'
        result = db_manager.execute_query(query, (student_id,), fetch_one=True)
        return cls(**dict(result)) if result else None
    
    @classmethod
    def get_all(cls, department=None, semester=None, search=None):
        """Get all students with optional filters"""
        query = 'SELECT * FROM students WHERE is_active = 1'
        params = []
        
        if department:
            query += ' AND department = ?'
            params.append(department)
        
        if semester:
            query += ' AND semester = ?'
            params.append(semester)
        
        if search:
            query += ' AND (name LIKE ? OR student_id LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += ' ORDER BY name'
        results = db_manager.execute_query(query, params)
        return [cls(**dict(row)) for row in results]

class Subject(BaseModel):
    """Subject model"""
    
    def __init__(self, subject_code=None, subject_name=None, department=None, 
                 semester=None, credits=3, subject_type='theory', is_active=True, **kwargs):
        super().__init__(**kwargs)
        self.subject_code = subject_code
        self.subject_name = subject_name
        self.department = department
        self.semester = semester
        self.credits = credits
        self.subject_type = subject_type
        self.is_active = is_active
    
    def save(self):
        """Save subject to database"""
        if hasattr(self, 'id') and self.id:
            # Update existing subject
            query = '''
                UPDATE subjects SET subject_name=?, department=?, semester=?, 
                credits=?, subject_type=?, is_active=?, updated_at=CURRENT_TIMESTAMP 
                WHERE subject_code=?
            '''
            params = (self.subject_name, self.department, self.semester, 
                     self.credits, self.subject_type, self.is_active, self.subject_code)
        else:
            # Insert new subject
            query = '''
                INSERT INTO subjects (subject_code, subject_name, department, 
                semester, credits, subject_type, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            params = (self.subject_code, self.subject_name, self.department, 
                     self.semester, self.credits, self.subject_type, self.is_active)
        
        return db_manager.execute_query(query, params)
    
    def delete(self):
        """Soft delete subject"""
        query = 'UPDATE subjects SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE subject_code=?'
        return db_manager.execute_query(query, (self.subject_code,))
    
    def get_enrolled_students(self):
        """Get students enrolled in this subject"""
        query = '''
            SELECT s.* FROM students s
            JOIN student_subjects ss ON s.student_id = ss.student_id
            WHERE ss.subject_code = ? AND ss.is_active = 1 AND s.is_active = 1
        '''
        return db_manager.execute_query(query, (self.subject_code,))
    
    @classmethod
    def get_by_code(cls, subject_code):
        """Get subject by code"""
        query = 'SELECT * FROM subjects WHERE subject_code = ? AND is_active = 1'
        result = db_manager.execute_query(query, (subject_code,), fetch_one=True)
        return cls(**dict(result)) if result else None
    
    @classmethod
    def get_all(cls, department=None, semester=None, search=None):
        """Get all subjects with optional filters"""
        query = 'SELECT * FROM subjects WHERE is_active = 1'
        params = []
        
        if department:
            query += ' AND department = ?'
            params.append(department)
        
        if semester:
            query += ' AND semester = ?'
            params.append(semester)
        
        if search:
            query += ' AND (subject_name LIKE ? OR subject_code LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += ' ORDER BY subject_name'
        results = db_manager.execute_query(query, params)
        return [cls(**dict(row)) for row in results]

class Room(BaseModel):
    """Room model"""
    
    def __init__(self, room_id=None, name=None, rows=None, cols=None, capacity=None,
                 building=None, floor=None, room_type='classroom', facilities=None, 
                 is_active=True, **kwargs):
        super().__init__(**kwargs)
        self.room_id = room_id
        self.name = name
        self.rows = rows
        self.cols = cols
        self.capacity = capacity
        self.building = building
        self.floor = floor
        self.room_type = room_type
        self.facilities = facilities
        self.is_active = is_active
    
    def save(self):
        """Save room to database with validation"""
        # Validate room data
        self._validate()
        
        if hasattr(self, 'id') and self.id:
            # Update existing room
            query = '''
                UPDATE rooms SET name=?, rows=?, cols=?, capacity=?, building=?, 
                floor=?, room_type=?, facilities=?, is_active=?, updated_at=CURRENT_TIMESTAMP 
                WHERE room_id=?
            '''
            params = (self.name, self.rows, self.cols, self.capacity, self.building,
                     self.floor, self.room_type, self.facilities, self.is_active, self.room_id)
        else:
            # Insert new room
            query = '''
                INSERT INTO rooms (room_id, name, rows, cols, capacity, building, 
                floor, room_type, facilities, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (self.room_id, self.name, self.rows, self.cols, self.capacity,
                     self.building, self.floor, self.room_type, self.facilities, self.is_active)
        
        return db_manager.execute_query(query, params)
    
    def _validate(self):
        """Validate room data"""
        if not self.room_id or not self.room_id.strip():
            raise ValueError("Room ID is required")
        
        if not self.name or not self.name.strip():
            raise ValueError("Room name is required")
        
        if not isinstance(self.rows, int) or self.rows <= 0:
            raise ValueError("Rows must be a positive integer")
        
        if not isinstance(self.cols, int) or self.cols <= 0:
            raise ValueError("Columns must be a positive integer")
        
        if not isinstance(self.capacity, int) or self.capacity <= 0:
            raise ValueError("Capacity must be a positive integer")
        
        # Validate that capacity matches rows * cols
        expected_capacity = self.rows * self.cols
        if self.capacity != expected_capacity:
            raise ValueError(f"Capacity ({self.capacity}) must equal rows × columns ({expected_capacity})")
    
    def delete(self):
        """Soft delete room"""
        query = 'UPDATE rooms SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE room_id=?'
        return db_manager.execute_query(query, (self.room_id,))
    
    def is_available(self, exam_date, session_time):
        """Check if room is available for given date and time"""
        query = '''
            SELECT COUNT(*) FROM seating_arrangements 
            WHERE room_id = ? AND exam_date = ? AND session_time = ? AND is_active = 1
        '''
        result = db_manager.execute_query(query, (self.room_id, exam_date, session_time), fetch_one=True)
        return result[0] == 0
    
    def get_occupancy(self, exam_date, session_time):
        """Get current occupancy for given date and time"""
        query = '''
            SELECT COUNT(*) FROM seating_arrangements 
            WHERE room_id = ? AND exam_date = ? AND session_time = ? AND is_active = 1
        '''
        result = db_manager.execute_query(query, (self.room_id, exam_date, session_time), fetch_one=True)
        occupied = result[0] if result else 0
        return {
            'occupied': occupied,
            'capacity': self.capacity,
            'occupancy_rate': (occupied / self.capacity * 100) if self.capacity > 0 else 0
        }
    
    @classmethod
    def get_by_id(cls, room_id):
        """Get room by ID"""
        query = 'SELECT * FROM rooms WHERE room_id = ? AND is_active = 1'
        result = db_manager.execute_query(query, (room_id,), fetch_one=True)
        return cls(**dict(result)) if result else None
    
    @classmethod
    def get_all(cls, building=None, floor=None, room_type=None):
        """Get all rooms with optional filters"""
        query = 'SELECT * FROM rooms WHERE is_active = 1'
        params = []
        
        if building:
            query += ' AND building = ?'
            params.append(building)
        
        if floor is not None:
            query += ' AND floor = ?'
            params.append(floor)
        
        if room_type:
            query += ' AND room_type = ?'
            params.append(room_type)
        
        query += ' ORDER BY building, floor, name'
        results = db_manager.execute_query(query, params)
        return [cls(**dict(row)) for row in results]

class Exam(BaseModel):
    """Exam model"""
    
    def __init__(self, subject_code=None, exam_date=None, start_time=None, 
                 end_time=None, duration=None, session_type='regular', 
                 exam_type='written', instructions=None, is_active=True, **kwargs):
        super().__init__(**kwargs)
        self.subject_code = subject_code
        self.exam_date = exam_date
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.session_type = session_type
        self.exam_type = exam_type
        self.instructions = instructions
        self.is_active = is_active
    
    def save(self):
        """Save exam to database"""
        if hasattr(self, 'id') and self.id:
            # Update existing exam
            query = '''
                UPDATE exams SET subject_code=?, exam_date=?, start_time=?, 
                end_time=?, duration=?, session_type=?, exam_type=?, instructions=?, 
                is_active=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
            '''
            params = (self.subject_code, self.exam_date, self.start_time, 
                     self.end_time, self.duration, self.session_type, self.exam_type,
                     self.instructions, self.is_active, self.id)
            return db_manager.execute_query(query, params)
        else:
            # Insert new exam
            query = '''
                INSERT INTO exams (subject_code, exam_date, start_time, end_time, 
                duration, session_type, exam_type, instructions, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (self.subject_code, self.exam_date, self.start_time, 
                     self.end_time, self.duration, self.session_type, self.exam_type,
                     self.instructions, self.is_active)
            
            # Execute insert and get the ID
            conn = db_manager.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                self.id = cursor.lastrowid
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
    
    def delete(self):
        """Soft delete exam"""
        query = 'UPDATE exams SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?'
        return db_manager.execute_query(query, (self.id,))
    
    def get_enrolled_students(self):
        """Get students enrolled for this exam"""
        query = '''
            SELECT s.* FROM students s
            JOIN student_subjects ss ON s.student_id = ss.student_id
            WHERE ss.subject_code = ? AND ss.is_active = 1 AND s.is_active = 1
        '''
        return db_manager.execute_query(query, (self.subject_code,))
    
    @classmethod
    def get_by_id(cls, exam_id):
        """Get exam by ID"""
        query = 'SELECT * FROM exams WHERE id = ? AND is_active = 1'
        result = db_manager.execute_query(query, (exam_id,), fetch_one=True)
        return cls(**dict(result)) if result else None
    
    @classmethod
    def get_all(cls, date_from=None, date_to=None, subject_code=None):
        """Get all exams with optional filters"""
        query = 'SELECT * FROM exams WHERE is_active = 1'
        params = []
        
        if date_from:
            query += ' AND exam_date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND exam_date <= ?'
            params.append(date_to)
        
        if subject_code:
            query += ' AND subject_code = ?'
            params.append(subject_code)
        
        query += ' ORDER BY exam_date, start_time'
        results = db_manager.execute_query(query, params)
        return [cls(**dict(row)) for row in results]

class Invigilator(BaseModel):
    """Invigilator model"""
    
    def __init__(self, staff_id=None, name=None, email=None, phone=None, 
                 department=None, designation=None, experience=0, max_assignments=2,
                 preferences=None, availability=None, is_active=True, **kwargs):
        super().__init__(**kwargs)
        self.staff_id = staff_id
        self.name = name
        self.email = email
        self.phone = phone
        self.department = department
        self.designation = designation
        self.experience = experience
        self.max_assignments = max_assignments
        self.preferences = preferences
        self.availability = availability
        self.is_active = is_active
    
    def save(self):
        """Save invigilator to database"""
        if hasattr(self, 'id') and self.id:
            # Update existing invigilator
            query = '''
                UPDATE invigilators SET name=?, email=?, phone=?, department=?, 
                designation=?, experience=?, max_assignments=?, preferences=?, 
                availability=?, is_active=?, updated_at=CURRENT_TIMESTAMP WHERE staff_id=?
            '''
            params = (self.name, self.email, self.phone, self.department, 
                     self.designation, self.experience, self.max_assignments,
                     self.preferences, self.availability, self.is_active, self.staff_id)
        else:
            # Insert new invigilator
            query = '''
                INSERT INTO invigilators (staff_id, name, email, phone, department, 
                designation, experience, max_assignments, preferences, availability, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            params = (self.staff_id, self.name, self.email, self.phone, self.department,
                     self.designation, self.experience, self.max_assignments,
                     self.preferences, self.availability, self.is_active)
        
        return db_manager.execute_query(query, params)
    
    def delete(self):
        """Soft delete invigilator"""
        query = 'UPDATE invigilators SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE staff_id=?'
        return db_manager.execute_query(query, (self.staff_id,))
    
    def get_assignments(self, date_from=None, date_to=None):
        """Get assignments for this invigilator"""
        query = '''
            SELECT ia.*, r.name as room_name, s.subject_name 
            FROM invigilator_assignments ia
            JOIN rooms r ON ia.room_id = r.room_id
            JOIN subjects s ON ia.subject_code = s.subject_code
            WHERE ia.staff_id = ? AND ia.is_active = 1
        '''
        params = [self.staff_id]
        
        if date_from:
            query += ' AND ia.exam_date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND ia.exam_date <= ?'
            params.append(date_to)
        
        query += ' ORDER BY ia.exam_date, ia.session_time'
        return db_manager.execute_query(query, params)
    
    @classmethod
    def get_by_id(cls, staff_id):
        """Get invigilator by staff ID"""
        query = 'SELECT * FROM invigilators WHERE staff_id = ? AND is_active = 1'
        result = db_manager.execute_query(query, (staff_id,), fetch_one=True)
        return cls(**dict(result)) if result else None
    
    @classmethod
    def get_all(cls, department=None, search=None):
        """Get all invigilators with optional filters"""
        query = 'SELECT * FROM invigilators WHERE is_active = 1'
        params = []
        
        if department:
            query += ' AND department = ?'
            params.append(department)
        
        if search:
            query += ' AND (name LIKE ? OR staff_id LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])
        
        query += ' ORDER BY name'
        results = db_manager.execute_query(query, params)
        return [cls(**dict(row)) for row in results]
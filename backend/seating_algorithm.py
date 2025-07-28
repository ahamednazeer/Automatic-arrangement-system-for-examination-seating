"""
Advanced Seating Arrangement Algorithm for Examination System
"""
import random
import math
from collections import defaultdict
from backend.database import db_manager
from backend.models import Student, Room, Exam, Subject
import uuid

class SeatingAlgorithm:
    """Advanced seating arrangement algorithm with conflict resolution"""
    
    def __init__(self):
        self.conflict_strategies = {
            'strict': self._strict_conflict_check,
            'moderate': self._moderate_conflict_check,
            'relaxed': self._relaxed_conflict_check
        }
        
        self.arrangement_strategies = {
            'mixed': self._mixed_arrangement,
            'department_wise': self._department_wise_arrangement,
            'random': self._random_arrangement,
            'alphabetical': self._alphabetical_arrangement
        }
    
    def generate_seating_arrangement(self, exam_date, session_time, 
                                   arrangement_type='mixed', 
                                   conflict_avoidance='strict',
                                   room_utilization='optimal',
                                   preserve_existing=False):
        """
        Generate seating arrangement for given exam session
        
        Args:
            exam_date: Date of the exam
            session_time: Time of the exam session
            arrangement_type: Type of arrangement (mixed, department_wise, random, alphabetical)
            conflict_avoidance: Level of conflict avoidance (strict, moderate, relaxed)
            room_utilization: Room utilization strategy (optimal, balanced, minimal)
            preserve_existing: Whether to preserve existing arrangements
        
        Returns:
            dict: Result of the arrangement process
        """
        try:
            # Get exams for the session
            exams = self._get_exams_for_session(exam_date, session_time)
            if not exams:
                return {'success': False, 'message': 'No exams found for the specified session'}
            
            # Get students for these exams
            students = self._get_students_for_exams(exams)
            if not students:
                return {'success': False, 'message': 'No students found for the exams'}
            
            # Get available rooms
            rooms = self._get_available_rooms(exam_date, session_time, room_utilization)
            if not rooms:
                return {'success': False, 'message': 'No rooms available for the session'}
            
            # Check capacity
            total_capacity = sum(room['capacity'] for room in rooms)
            if len(students) > total_capacity:
                return {'success': False, 'message': f'Insufficient capacity. Need {len(students)} seats, available {total_capacity}'}
            
            # Clear existing arrangements if not preserving
            if not preserve_existing:
                self._clear_existing_arrangements(exam_date, session_time)
            
            # Apply arrangement strategy
            arrangement_strategy = self.arrangement_strategies.get(arrangement_type, self._mixed_arrangement)
            arranged_students = arrangement_strategy(students)
            
            # Apply conflict avoidance strategy
            conflict_strategy = self.conflict_strategies.get(conflict_avoidance, self._strict_conflict_check)
            
            # Perform seating allocation
            allocation_result = self._allocate_seats(
                arranged_students, rooms, exam_date, session_time, conflict_strategy
            )
            
            # Generate arrangement ID for tracking
            arrangement_id = str(uuid.uuid4())
            
            # Update arrangement records with ID
            self._update_arrangement_id(exam_date, session_time, arrangement_id)
            
            return {
                'success': True,
                'arrangement_id': arrangement_id,
                'students_allocated': allocation_result['allocated'],
                'students_failed': allocation_result['failed'],
                'rooms_used': allocation_result['rooms_used'],
                'conflicts_resolved': allocation_result['conflicts_resolved'],
                'message': f'Successfully allocated {allocation_result["allocated"]} students'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Error generating seating arrangement: {str(e)}'}
    
    def _get_exams_for_session(self, exam_date, session_time):
        """Get exams for the specified session"""
        query = '''
            SELECT e.*, s.subject_name, s.department 
            FROM exams e 
            JOIN subjects s ON e.subject_code = s.subject_code 
            WHERE e.exam_date = ? AND e.start_time = ? AND e.is_active = 1
        '''
        return db_manager.execute_query(query, (exam_date, session_time))
    
    def _get_students_for_exams(self, exams):
        """Get students enrolled for the exams"""
        students = []
        for exam in exams:
            query = '''
                SELECT s.*, ss.subject_code, sub.department as subject_dept, sub.subject_name
                FROM students s
                JOIN student_subjects ss ON s.student_id = ss.student_id
                JOIN subjects sub ON ss.subject_code = sub.subject_code
                WHERE ss.subject_code = ? AND ss.is_active = 1 AND s.is_active = 1
            '''
            exam_students = db_manager.execute_query(query, (exam['subject_code'],))
            students.extend([dict(student) for student in exam_students])
        
        return students
    
    def _get_available_rooms(self, exam_date, session_time, utilization_strategy):
        """Get available rooms based on utilization strategy"""
        query = 'SELECT * FROM rooms WHERE is_active = 1'
        
        if utilization_strategy == 'optimal':
            query += ' ORDER BY capacity DESC'
        elif utilization_strategy == 'balanced':
            query += ' ORDER BY capacity ASC'
        else:  # minimal
            query += ' ORDER BY capacity DESC LIMIT 5'
        
        rooms = db_manager.execute_query(query)
        
        # Filter out rooms that are already occupied
        available_rooms = []
        for room in rooms:
            if self._is_room_available(room['room_id'], exam_date, session_time):
                available_rooms.append(dict(room))
        
        return available_rooms
    
    def _is_room_available(self, room_id, exam_date, session_time):
        """Check if room is available for the session"""
        query = '''
            SELECT COUNT(*) FROM seating_arrangements 
            WHERE room_id = ? AND exam_date = ? AND session_time = ? AND is_active = 1
        '''
        result = db_manager.execute_query(query, (room_id, exam_date, session_time), fetch_one=True)
        return result[0] == 0
    
    def _clear_existing_arrangements(self, exam_date, session_time):
        """Clear existing seating arrangements for the session"""
        query = '''
            UPDATE seating_arrangements 
            SET is_active = 0 
            WHERE exam_date = ? AND session_time = ?
        '''
        db_manager.execute_query(query, (exam_date, session_time))
    
    def _mixed_arrangement(self, students):
        """Mixed arrangement strategy - shuffle students randomly"""
        shuffled = students.copy()
        random.shuffle(shuffled)
        return shuffled
    
    def _department_wise_arrangement(self, students):
        """Department-wise arrangement strategy"""
        # Group by department
        dept_groups = defaultdict(list)
        for student in students:
            dept_groups[student['department']].append(student)
        
        # Shuffle within departments and combine
        arranged = []
        for dept, dept_students in dept_groups.items():
            random.shuffle(dept_students)
            arranged.extend(dept_students)
        
        return arranged
    
    def _random_arrangement(self, students):
        """Random arrangement strategy"""
        return self._mixed_arrangement(students)
    
    def _alphabetical_arrangement(self, students):
        """Alphabetical arrangement strategy"""
        return sorted(students, key=lambda x: x['name'])
    
    def _allocate_seats(self, students, rooms, exam_date, session_time, conflict_strategy):
        """Allocate seats to students"""
        allocated_count = 0
        failed_students = []
        rooms_used = set()
        conflicts_resolved = 0
        
        # Initialize room grids
        room_grids = {}
        for room in rooms:
            room_grids[room['room_id']] = {
                'grid': [[None for _ in range(room['cols'])] for _ in range(room['rows'])],
                'room_info': room
            }
        
        # Allocate students
        for student in students:
            allocated = False
            
            for room_id, room_data in room_grids.items():
                if allocated:
                    break
                
                grid = room_data['grid']
                room_info = room_data['room_info']
                
                # Try to find a suitable seat
                for row in range(room_info['rows']):
                    if allocated:
                        break
                    
                    for col in range(room_info['cols']):
                        if grid[row][col] is None:
                            # Check for conflicts
                            if conflict_strategy(student, grid, row, col):
                                conflicts_resolved += 1
                                continue
                            
                            # Allocate seat
                            grid[row][col] = student
                            
                            # Insert into database
                            self._insert_seating_record(
                                student, room_id, row + 1, col + 1, 
                                exam_date, session_time
                            )
                            
                            allocated_count += 1
                            rooms_used.add(room_id)
                            allocated = True
                            break
            
            if not allocated:
                failed_students.append(student)
        
        return {
            'allocated': allocated_count,
            'failed': len(failed_students),
            'failed_students': failed_students,
            'rooms_used': len(rooms_used),
            'conflicts_resolved': conflicts_resolved
        }
    
    def _insert_seating_record(self, student, room_id, seat_row, seat_col, exam_date, session_time):
        """Insert seating arrangement record"""
        query = '''
            INSERT INTO seating_arrangements 
            (student_id, subject_code, room_id, seat_row, seat_col, exam_date, session_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            student['student_id'], student['subject_code'], room_id,
            seat_row, seat_col, exam_date, session_time
        )
        db_manager.execute_query(query, params)
    
    def _strict_conflict_check(self, student, grid, row, col):
        """Strict conflict checking - no adjacent same department/subject"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            if (0 <= new_row < len(grid) and 
                0 <= new_col < len(grid[0]) and 
                grid[new_row][new_col] is not None):
                
                adjacent_student = grid[new_row][new_col]
                
                # Check for conflicts
                if (adjacent_student['department'] == student['department'] or
                    adjacent_student['subject_code'] == student['subject_code']):
                    return True
        
        return False
    
    def _moderate_conflict_check(self, student, grid, row, col):
        """Moderate conflict checking - 1 seat gap allowed"""
        # Check immediate adjacent seats only
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        conflicts = 0
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            if (0 <= new_row < len(grid) and 
                0 <= new_col < len(grid[0]) and 
                grid[new_row][new_col] is not None):
                
                adjacent_student = grid[new_row][new_col]
                
                if (adjacent_student['department'] == student['department'] or
                    adjacent_student['subject_code'] == student['subject_code']):
                    conflicts += 1
        
        # Allow up to 1 conflict
        return conflicts > 1
    
    def _relaxed_conflict_check(self, student, grid, row, col):
        """Relaxed conflict checking - allow some conflicts"""
        # Only check for same subject conflicts in immediate vicinity
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            
            if (0 <= new_row < len(grid) and 
                0 <= new_col < len(grid[0]) and 
                grid[new_row][new_col] is not None):
                
                adjacent_student = grid[new_row][new_col]
                
                # Only prevent same subject conflicts
                if adjacent_student['subject_code'] == student['subject_code']:
                    return True
        
        return False
    
    def _update_arrangement_id(self, exam_date, session_time, arrangement_id):
        """Update arrangement records with arrangement ID"""
        query = '''
            UPDATE seating_arrangements 
            SET arrangement_id = ? 
            WHERE exam_date = ? AND session_time = ? AND is_active = 1
        '''
        db_manager.execute_query(query, (arrangement_id, exam_date, session_time))
    
    def get_arrangement_statistics(self, exam_date, session_time):
        """Get statistics for a seating arrangement"""
        # Total students
        total_query = '''
            SELECT COUNT(*) FROM seating_arrangements 
            WHERE exam_date = ? AND session_time = ? AND is_active = 1
        '''
        total_students = db_manager.execute_query(total_query, (exam_date, session_time), fetch_one=True)[0]
        
        # Rooms used
        rooms_query = '''
            SELECT COUNT(DISTINCT room_id) FROM seating_arrangements 
            WHERE exam_date = ? AND session_time = ? AND is_active = 1
        '''
        rooms_used = db_manager.execute_query(rooms_query, (exam_date, session_time), fetch_one=True)[0]
        
        # Room utilization
        utilization_query = '''
            SELECT r.room_id, r.capacity, COUNT(sa.id) as occupied
            FROM rooms r
            LEFT JOIN seating_arrangements sa ON r.room_id = sa.room_id 
                AND sa.exam_date = ? AND sa.session_time = ? AND sa.is_active = 1
            WHERE r.room_id IN (
                SELECT DISTINCT room_id FROM seating_arrangements 
                WHERE exam_date = ? AND session_time = ? AND is_active = 1
            )
            GROUP BY r.room_id, r.capacity
        '''
        utilization_data = db_manager.execute_query(
            utilization_query, (exam_date, session_time, exam_date, session_time)
        )
        
        avg_occupancy = 0
        if utilization_data:
            total_capacity = sum(row['capacity'] for row in utilization_data)
            total_occupied = sum(row['occupied'] for row in utilization_data)
            avg_occupancy = (total_occupied / total_capacity * 100) if total_capacity > 0 else 0
        
        return {
            'total_students': total_students,
            'rooms_used': rooms_used,
            'avg_occupancy': round(avg_occupancy, 1),
            'room_details': [dict(row) for row in utilization_data] if utilization_data else []
        }
    
    def validate_arrangement(self, exam_date, session_time):
        """Validate a seating arrangement for conflicts"""
        conflicts = []
        
        # Get all arrangements for the session
        query = '''
            SELECT sa.*, s.name as student_name, s.department, sub.subject_name
            FROM seating_arrangements sa
            JOIN students s ON sa.student_id = s.student_id
            JOIN subjects sub ON sa.subject_code = sub.subject_code
            WHERE sa.exam_date = ? AND sa.session_time = ? AND sa.is_active = 1
            ORDER BY sa.room_id, sa.seat_row, sa.seat_col
        '''
        arrangements = db_manager.execute_query(query, (exam_date, session_time))
        
        # Group by room
        room_arrangements = defaultdict(list)
        for arr in arrangements:
            room_arrangements[arr['room_id']].append(dict(arr))
        
        # Check for conflicts in each room
        for room_id, room_seats in room_arrangements.items():
            # Create position map
            position_map = {}
            for seat in room_seats:
                position_map[(seat['seat_row'], seat['seat_col'])] = seat
            
            # Check each seat for conflicts
            for seat in room_seats:
                row, col = seat['seat_row'], seat['seat_col']
                
                # Check adjacent positions
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                for dr, dc in directions:
                    adj_pos = (row + dr, col + dc)
                    if adj_pos in position_map:
                        adj_seat = position_map[adj_pos]
                        
                        # Check for department or subject conflicts
                        if (seat['department'] == adj_seat['department'] or
                            seat['subject_code'] == adj_seat['subject_code']):
                            conflicts.append({
                                'type': 'adjacent_conflict',
                                'room_id': room_id,
                                'student1': {
                                    'id': seat['student_id'],
                                    'name': seat['student_name'],
                                    'position': f"{row}-{col}",
                                    'department': seat['department'],
                                    'subject': seat['subject_code']
                                },
                                'student2': {
                                    'id': adj_seat['student_id'],
                                    'name': adj_seat['student_name'],
                                    'position': f"{adj_seat['seat_row']}-{adj_seat['seat_col']}",
                                    'department': adj_seat['department'],
                                    'subject': adj_seat['subject_code']
                                }
                            })
        
        return conflicts

# Global seating algorithm instance
seating_algorithm = SeatingAlgorithm()
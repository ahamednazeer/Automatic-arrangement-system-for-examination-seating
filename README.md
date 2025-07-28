# Examination Seating Arrangement System

A comprehensive web-based system for managing examination seating arrangements with automatic conflict resolution and intelligent room allocation.

## Features

### 🔐 1. Admin Authentication
- Secure login system for exam administrators
- Role-based access control
- Session management with automatic logout
- Password hashing and security

### 👥 2. Student Management
- Add, edit, and delete student records
- Bulk import from CSV/Excel files
- Department and semester-wise filtering
- Subject enrollment management
- Search and filter capabilities

### 🏫 3. Room Management
- Define exam rooms with capacity and layout
- Grid-based seating arrangement (rows × columns)
- Building and floor organization
- Room availability tracking
- Facility management

### 📚 4. Subject Management
- Create and manage academic subjects
- Department and semester categorization
- Credit system support
- Student enrollment tracking

### 📅 5. Exam Scheduling
- Schedule exams with date and time slots
- Multiple session support (morning/afternoon)
- Duration and exam type management
- Conflict detection for overlapping exams

### 🪑 6. Automatic Seating Arrangement
- **Intelligent Algorithm**: Prevents same department/subject students from sitting adjacent
- **Multiple Strategies**:
  - Mixed arrangement (random distribution)
  - Department-wise grouping
  - Alphabetical ordering
  - Custom arrangements
- **Conflict Avoidance Levels**:
  - Strict: No adjacent conflicts
  - Moderate: 1-seat gap allowed
  - Relaxed: Minimal conflicts
- **Room Utilization**:
  - Optimal: Fill rooms efficiently
  - Balanced: Distribute evenly
  - Minimal: Use fewer rooms

### 🗺️ 7. Seating Map Generation
- Visual 2D layout of student placement
- Room-wise seating charts
- Interactive seat selection
- Real-time occupancy display
- Printable seating maps

### 👨‍🏫 8. Invigilator Management
- Staff database with contact information
- Automatic duty assignment
- Workload balancing
- Availability tracking
- Department-wise preferences

### 📊 9. Reports & Analytics
- **Seating Reports**: Room-wise arrangements, student lists
- **Admit Cards**: Individual student seat slips
- **Utilization Reports**: Room occupancy analysis
- **Duty Rosters**: Invigilator assignments
- **Export Formats**: PDF, Excel, CSV
- **Statistical Dashboard**: System metrics and analytics

### 🔍 10. Search & Filter
- Advanced search across all modules
- Multi-criteria filtering
- Real-time search suggestions
- Export filtered results

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Werkzeug Security
- **File Processing**: Pandas, OpenPyXL
- **PDF Generation**: ReportLab
- **Algorithm**: Custom seating optimization

### Frontend
- **Template Engine**: Jinja2
- **CSS Framework**: Bootstrap 4
- **JavaScript**: jQuery, Chart.js
- **Icons**: Font Awesome
- **UI Components**: AdminLTE theme

### Architecture
- **Modular Design**: Separated backend and frontend
- **MVC Pattern**: Models, Views, Controllers
- **Blueprint Structure**: Organized route management
- **Database Layer**: Abstracted data access
- **Utility Modules**: Reusable components

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Quick Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd Automatic-arrangement-system-for-examination-seating-1
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Initialize the database**
```bash
python -c "from backend.database import db_manager; db_manager.init_database()"
```

4. **Run the application**
```bash
# Using the modular version (recommended)
python app_modular.py

# Or using the original version
python app.py
```

5. **Access the application**
- Open your browser and go to `http://localhost:5000`
- Login with default credentials:
  - Email: `admin@exam.com`
  - Password: `admin123`

### Production Setup

1. **Environment Configuration**
```bash
export FLASK_ENV=production
export SECRET_KEY=your-production-secret-key
```

2. **Database Configuration**
- For production, consider using PostgreSQL or MySQL
- Update database connection in `backend/database.py`

3. **Web Server**
- Use Gunicorn or uWSGI for production deployment
- Configure reverse proxy with Nginx

## Usage Guide

### 1. Initial Setup
1. Login with admin credentials
2. Add rooms with their capacity and layout
3. Import or add subjects for different departments
4. Import or add student records
5. Enroll students in their respective subjects

### 2. Exam Scheduling
1. Go to Exams → Add Exam
2. Select subject, date, and time
3. Set duration and exam type
4. Save the exam schedule

### 3. Seating Arrangement
1. Go to Seating → Generate Seating
2. Select exam date and session
3. Choose arrangement strategy and conflict level
4. Click "Generate Seating"
5. Review and download the arrangement

### 4. Reports Generation
1. Go to Reports
2. Select report type (seating, utilization, etc.)
3. Set date range and filters
4. Choose export format (PDF/Excel/CSV)
5. Generate and download report

## API Endpoints

### Student Management
- `GET /api/students/search` - Search students
- `POST /api/import/students` - Import students from CSV
- `GET /api/export/students` - Export students data

### Room Management
- `GET /api/rooms/availability` - Check room availability
- `GET /api/rooms/occupancy` - Get room occupancy data

### Seating Management
- `POST /seating/generate` - Generate seating arrangement
- `GET /api/seating/validate` - Validate arrangement for conflicts
- `GET /seating/view` - View seating arrangement

### Reports
- `POST /reports/generate` - Generate various reports
- `GET /api/reports/preview` - Preview report data

## File Structure

```
├── app.py                 # Original monolithic application
├── app_modular.py         # Modular application (recommended)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── backend/              # Backend modules
│   ├── __init__.py
│   ├── database.py       # Database management
│   ├── models.py         # Data models
│   ├── seating_algorithm.py  # Seating arrangement logic
│   ├── reports.py        # Report generation
│   └── utils.py          # Utility functions
├── frontend/             # Frontend modules
│   ├── __init__.py
│   └── routes.py         # Route definitions
├── templates/            # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── login.html
│   ├── students/         # Student templates
│   ├── subjects/         # Subject templates
│   ├── rooms/           # Room templates
│   ├── exams/           # Exam templates
│   ├── seating/         # Seating templates
│   ├── invigilators/    # Invigilator templates
│   ├── reports/         # Report templates
│   └── errors/          # Error pages
├── static/              # Static files
│   ├── css/
│   └── js/
├── uploads/             # File uploads
├── reports/             # Generated reports
└── backups/             # Database backups
```

## Configuration

### Database Settings
- Default: SQLite (`exam_system.db`)
- For production: Configure in `backend/database.py`

### File Upload Settings
- Max file size: 16MB
- Allowed formats: CSV, Excel
- Upload directory: `uploads/`

### Report Settings
- Output directory: `reports/`
- Supported formats: PDF, Excel, CSV
- Template customization available

## Security Features

- Password hashing with Werkzeug
- Session management
- CSRF protection
- File upload validation
- SQL injection prevention
- XSS protection

## Performance Optimization

- Database indexing for faster queries
- Efficient seating algorithm
- Pagination for large datasets
- Caching for frequently accessed data
- Optimized PDF generation

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure SQLite file permissions
   - Check database initialization

2. **Import Errors**
   - Verify CSV format and headers
   - Check for duplicate entries

3. **Seating Generation Fails**
   - Ensure sufficient room capacity
   - Check for valid exam data

4. **Report Generation Issues**
   - Verify report directory permissions
   - Check for required data

### Logs and Debugging
- Enable debug mode: `app.run(debug=True)`
- Check console output for errors
- Review database logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Email: admin@exam.com
- Create an issue on GitHub
- Check the documentation

## Changelog

### Version 1.0.0
- Initial release with all core features
- Modular architecture implementation
- Comprehensive reporting system
- Advanced seating algorithm

### Future Enhancements
- Mobile responsive design
- REST API for external integrations
- Advanced analytics dashboard
- Multi-language support
- Cloud deployment options
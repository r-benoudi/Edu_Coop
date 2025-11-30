# Educational Cooperative Information System

## Overview
A comprehensive Django-based management system for an educational cooperative that handles students, instructors, courses, attendance, finances, and profit distribution. The system supports tutoring (Math, Physics, Life Sciences) and IT training courses.

## Current State
- **Status**: Fully functional MVP
- **Last Updated**: November 30, 2025

## Technology Stack
- **Backend**: Django 5.x with Python 3.11
- **Frontend**: Django Templates with Tailwind CSS (via CDN for development)
- **Database**: PostgreSQL (configured via DATABASE_URL)
- **PDF Generation**: ReportLab

## Project Structure
```
cooperative_system/
├── cooperative_system/       # Django project settings
│   ├── settings.py          # Project configuration
│   ├── urls.py               # Root URL configuration
│   └── wsgi.py               # WSGI configuration
├── core/                      # Main application
│   ├── models.py             # Database models
│   ├── views.py              # View functions
│   ├── forms.py              # Django forms
│   ├── admin.py              # Admin configuration
│   ├── urls.py               # App URL patterns
│   └── pdf_generator.py      # PDF generation utilities
├── templates/                 # HTML templates
│   ├── base.html             # Base template with sidebar
│   └── core/                 # App-specific templates
├── static/                    # Static files
└── manage.py                 # Django management script
```

## Key Features

### 1. Student Management
- Registration with parent/guardian information
- Enrollment tracking across courses
- Fee management and payment history
- Invoice generation (PDF)

### 2. Instructor Management
- Profile management with specialization
- Course assignments
- Payment tracking (100 DH/student for tutoring, 120 DH/hour for IT)
- Contract generation (PDF)

### 3. Course Management
- Two types: Tutoring (250 DH/month) and IT Training (500 DH/month)
- Subjects: Math, Physics, Life Sciences, IT Training
- Enrollment limits and duration tracking

### 4. Attendance System
- Bulk attendance recording by course
- Status tracking: Present, Absent, Excused
- Attendance reports with filtering

### 5. Financial Management
- Automated payment generation
- Student fee collection tracking
- Instructor payment management
- Monthly financial reports
- Profit distribution to members

### 6. Member Management
- Active members and passive contributors
- Capital share tracking
- Profit distribution based on shares
- Compliance with cooperative regulations

## Fee Structure
- **Tutoring courses**: 250 DH/month per student
- **IT courses**: 500 DH/month per student

## Instructor Payment
- **Tutoring**: 100 DH per student per month
- **IT Training**: 120 DH per hour (max 8 hours/month)

## Running the Application
The Django development server runs on port 5000:
```bash
python manage.py runserver 0.0.0.0:5000
```

## Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

## Production Notes
- For production deployment, configure gunicorn or similar WSGI server
- Set up proper Tailwind CSS build (PostCSS) instead of CDN
- Configure proper static file serving with whitenoise
- Set DEBUG=False in production

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (auto-configured)
- `SECRET_KEY`: Django secret key (auto-generated)
- `DEBUG`: Set to False for production

## Recent Changes
- Initial MVP implementation with all core features
- Dashboard with KPIs and quick actions
- PDF generation for invoices, contracts, and financial reports
- Tailwind CSS styling throughout

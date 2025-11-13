# BCM Management System

**Business Continuity Management System** - A comprehensive web-based platform for managing organizational risks and business continuity planning.

## 📋 Overview

The BCM Management System digitizes and automates the BCM data collection process across multiple departments, replacing manual Excel-based workflows with a centralized electronic system. The platform enables departments to log potential risks, expected impacts, and estimated resolution times while providing BCM Managers with powerful monitoring and reporting capabilities.

## ✨ Features

### Core Functionality
- **Risk Management**: Complete CRUD operations for risk entries
- **Role-Based Access Control**: Three user roles (Admin/BCM Manager, Department User, Viewer/Auditor)
- **Department Management**: Support for 50+ departments with independent risk tracking
- **Dashboard & Analytics**: Real-time KPIs and statistics
- **Reporting**: Export to Excel and PDF formats
- **Email Notifications**: Automatic alerts on risk creation/updates
- **Search & Filtering**: Dynamic risk filtering by severity, status, and keywords
- **Risk Locking**: BCM Managers can lock risks after review

### Security Features
- Authentication system with password reset
- Role-based permissions and authorization
- Locked risks prevent unauthorized edits
- Audit trail with timestamps and user tracking

## 🏗️ Architecture

### Technology Stack
- **Framework**: Django 4.2.26
- **Python**: 3.9+
- **Database**: SQLite (development) / PostgreSQL-ready (production)
- **Frontend**: Bootstrap 4, HTML5, CSS3, JavaScript
- **Libraries**:
  - django-crispy-forms (form styling)
  - openpyxl (Excel export)
  - reportlab (PDF generation)
  - django-filter (advanced filtering)

### Project Structure
```
bcm/
├── accounts/          # User authentication & management
├── departments/       # Department models & management
├── risks/            # Risk management (core module)
├── dashboard/        # Dashboards, KPIs, and reports
├── templates/        # HTML templates
├── static/           # CSS, JS, images
└── manage.py         # Django management script
```

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.9 or higher
- Virtual environment (recommended)

### 2. Setup Virtual Environment
```bash
# Navigate to project directory
cd /Users/abdulrahmanalshehri/Desktop/DjangoApp/bcm

# Activate virtual environment
source venv/bin/activate
```

### 3. Install Dependencies
Dependencies are already installed in the venv:
- Django 4.2.26
- pillow
- django-crispy-forms
- crispy-bootstrap4
- openpyxl
- reportlab
- django-filter

### 4. Database Setup
```bash
# Run migrations (already completed)
python manage.py migrate

# Seed initial data
python manage.py seed_data
```

### 5. Run Development Server
```bash
python manage.py runserver
```

Access the application at: `http://127.0.0.1:8000`

## 👥 User Roles & Permissions

### 1. Admin (BCM Manager)
- **Full access** to all departments and risks
- Can lock/unlock risks after review
- Access to all reports and exports
- Department management
- User management via admin panel

### 2. Department User
- Create, view, and edit risks **for their department only**
- Cannot edit locked risks
- View their department's dashboard and statistics
- Receive notifications about their risks

### 3. Viewer/Auditor
- **Read-only access** to all departments and risks
- View dashboards and statistics
- Cannot create or modify risks
- Useful for compliance and audit purposes

## 🔐 Default Login Credentials

```
Admin (BCM Manager):
  Username: admin
  Password: admin123

IT Department User:
  Username: it_user
  Password: password123

HR Department User:
  Username: hr_user
  Password: password123

Viewer:
  Username: viewer
  Password: viewer123
```

**⚠️ IMPORTANT**: Change all default passwords before deploying to production!

## 📊 Key Features Explained

### Risk Management Module
Each risk entry contains:
- **Expected Problem**: Description of potential risk
- **Impact**: Expected consequences if risk occurs
- **Estimated Resolution Duration**: Time needed to resolve (in hours/days/weeks)
- **Mitigation Notes**: Action plan and mitigation strategies
- **Severity**: LOW, MEDIUM, HIGH, CRITICAL
- **Status**: OPEN, IN_PROGRESS, RESOLVED, CLOSED
- **Lock Status**: Prevents editing after BCM Manager review

### Dashboard
- **BCM Manager**: Overview of all departments with statistics
- **Department User**: Department-specific metrics and risks
- **Viewer**: Read-only view of all data

### Reporting & Export
- **Excel Export**: Detailed risk report with all fields
- **PDF Export**: Executive summary with key statistics
- **Filters**: Export by department, severity, or status

## 🗂️ Database Models

### User Model
- Extended Django AbstractUser
- Custom fields: role, department, phone
- Methods: `is_admin()`, `can_edit_risk()`, `can_view_risk()`

### Department Model
- name, code, description
- head_name, contact_email, contact_phone
- is_active flag
- Timestamps (created_at, updated_at)

### Risk Model
- expected_problem, impact, mitigation_notes
- estimated_resolution_duration, resolution_duration_unit
- severity, status
- department (ForeignKey)
- created_by, updated_by, locked_by (ForeignKey to User)
- is_locked, locked_at
- Timestamps

## 🔧 Management Commands

### Seed Data
```bash
python manage.py seed_data
```
Creates:
- 8 departments (IT, HR, Finance, Operations, Marketing, Legal, CS, R&D)
- Admin user and sample department users
- Viewer user
- Sample risks for testing

### Create Superuser
```bash
python manage.py createsuperuser
```

## 📱 API Endpoints

### Main Routes
- `/` - Redirects to dashboard
- `/accounts/login/` - Login page
- `/accounts/logout/` - Logout
- `/accounts/profile/` - User profile
- `/dashboard/` - Main dashboard
- `/risks/` - Risk list
- `/risks/create/` - Create new risk
- `/risks/<id>/` - Risk detail view
- `/risks/<id>/update/` - Edit risk
- `/risks/<id>/delete/` - Delete risk (Admin only)
- `/risks/<id>/lock/` - Lock risk (Admin only)
- `/risks/<id>/unlock/` - Unlock risk (Admin only)
- `/dashboard/export/excel/` - Export to Excel (Admin only)
- `/dashboard/export/pdf/` - Export to PDF (Admin only)
- `/admin/` - Django admin panel

## 🎨 UI/UX Features

- **Responsive Design**: Works on desktop, tablet, and mobile
- **Bootstrap 4**: Modern, professional interface
- **Color-Coded Badges**: Visual severity and status indicators
- **Toast Notifications**: Success/error messages
- **Pagination**: Efficient handling of large datasets
- **Search & Filter**: Real-time risk filtering
- **Font Awesome Icons**: Enhanced visual experience

## 🔒 Security Best Practices

1. **Authentication Required**: All views protected with @login_required
2. **Role-Based Authorization**: Custom decorators enforce permissions
3. **CSRF Protection**: Enabled by default
4. **Password Validation**: Django's built-in validators
5. **SQL Injection Protection**: Django ORM prevents SQL injection
6. **XSS Protection**: Template auto-escaping enabled
7. **Session Management**: Configurable session timeouts

## 📈 Production Deployment Checklist

1. **Environment Variables**
   - Set `DEBUG = False`
   - Configure `SECRET_KEY` from environment
   - Set `ALLOWED_HOSTS`

2. **Database**
   - Migrate to PostgreSQL or MySQL
   - Configure database connection

3. **Static Files**
   - Run `python manage.py collectstatic`
   - Configure web server to serve static files

4. **Email**
   - Configure SMTP settings for email notifications
   - Update `EMAIL_BACKEND` from console to SMTP

5. **Security**
   - Enable HTTPS
   - Configure `SECURE_SSL_REDIRECT = True`
   - Set `SESSION_COOKIE_SECURE = True`
   - Set `CSRF_COOKIE_SECURE = True`
   - Change all default passwords

6. **Monitoring**
   - Set up error logging
   - Configure database backups
   - Monitor application performance

## 🐛 Troubleshooting

### Issue: Cannot login
- Ensure migrations are run: `python manage.py migrate`
- Run seed data: `python manage.py seed_data`
- Check credentials match default or created users

### Issue: Templates not loading
- Verify `TEMPLATES['DIRS']` in settings.py
- Ensure templates directory exists

### Issue: Static files not loading
- Run: `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATICFILES_DIRS` settings

## 📝 Future Enhancements (Optional)

- Multi-language support (English/Arabic)
- Microsoft Teams integration for alerts
- Advanced workflow approval system
- Risk assessment matrix with automatic scoring
- Historical risk tracking and trends
- Mobile app for on-the-go access
- API for third-party integrations
- Advanced analytics with charts (Chart.js)

## 📞 Support

For questions or issues, please contact your system administrator or BCM team.

## 📄 License

Proprietary - Internal use only

---

**Developed with Django Best Practices**
- Clean architecture with app separation
- DRY (Don't Repeat Yourself) principle
- Comprehensive documentation
- Security-first approach
- Scalable design for 50+ departments

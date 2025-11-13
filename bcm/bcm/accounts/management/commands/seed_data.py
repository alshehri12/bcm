from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import User
from departments.models import Department
from risks.models import Risk


class Command(BaseCommand):
    help = 'Seed initial data for BCM System'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))

        # Create Departments
        self.stdout.write('Creating departments...')
        departments_data = [
            {'name': 'Information Technology', 'code': 'IT', 'head_name': 'John Smith'},
            {'name': 'Human Resources', 'code': 'HR', 'head_name': 'Jane Doe'},
            {'name': 'Finance', 'code': 'FIN', 'head_name': 'Michael Johnson'},
            {'name': 'Operations', 'code': 'OPS', 'head_name': 'Sarah Williams'},
            {'name': 'Marketing', 'code': 'MKT', 'head_name': 'David Brown'},
            {'name': 'Legal', 'code': 'LEG', 'head_name': 'Emily Davis'},
            {'name': 'Customer Service', 'code': 'CS', 'head_name': 'Robert Wilson'},
            {'name': 'Research & Development', 'code': 'RD', 'head_name': 'Lisa Anderson'},
        ]

        departments = {}
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={
                    'name': dept_data['name'],
                    'head_name': dept_data['head_name'],
                    'is_active': True
                }
            )
            departments[dept.code] = dept
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created department: {dept.name}'))

        # Create Admin User (BCM Manager)
        self.stdout.write('Creating admin user...')
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@bcm.com',
                'first_name': 'BCM',
                'last_name': 'Manager',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('  ✓ Created admin user'))
            self.stdout.write(self.style.WARNING('    Username: admin'))
            self.stdout.write(self.style.WARNING('    Password: admin123'))
        else:
            self.stdout.write(self.style.WARNING('  Admin user already exists'))

        # Create Department Users
        self.stdout.write('Creating department users...')
        dept_users_data = [
            {'username': 'it_user', 'dept': 'IT', 'name': ('Tom', 'Hardy')},
            {'username': 'hr_user', 'dept': 'HR', 'name': ('Alice', 'Cooper')},
            {'username': 'fin_user', 'dept': 'FIN', 'name': ('Bob', 'Martin')},
            {'username': 'ops_user', 'dept': 'OPS', 'name': ('Carol', 'White')},
        ]

        for user_data in dept_users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': f"{user_data['username']}@bcm.com",
                    'first_name': user_data['name'][0],
                    'last_name': user_data['name'][1],
                    'role': User.Role.DEPARTMENT_USER,
                    'department': departments[user_data['dept']],
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created user: {user.username}'))

        # Create a Viewer User
        self.stdout.write('Creating viewer user...')
        viewer, created = User.objects.get_or_create(
            username='viewer',
            defaults={
                'email': 'viewer@bcm.com',
                'first_name': 'Audit',
                'last_name': 'Viewer',
                'role': User.Role.VIEWER,
            }
        )
        if created:
            viewer.set_password('viewer123')
            viewer.save()
            self.stdout.write(self.style.SUCCESS('  ✓ Created viewer user'))

        # Create Sample Risks
        self.stdout.write('Creating sample risks...')
        sample_risks = [
            {
                'department': departments['IT'],
                'expected_problem': 'Server failure during peak hours causing system downtime',
                'impact': 'Complete loss of access to critical systems affecting all departments',
                'severity': Risk.Severity.CRITICAL,
                'status': Risk.Status.OPEN,
                'estimated_resolution_duration': 4,
                'resolution_duration_unit': Risk.DurationUnit.HOURS,
                'mitigation_notes': 'Implement redundant servers and automated failover system',
            },
            {
                'department': departments['HR'],
                'expected_problem': 'Loss of employee records due to data corruption',
                'impact': 'Unable to process payroll and maintain compliance with labor laws',
                'severity': Risk.Severity.HIGH,
                'status': Risk.Status.IN_PROGRESS,
                'estimated_resolution_duration': 2,
                'resolution_duration_unit': Risk.DurationUnit.DAYS,
                'mitigation_notes': 'Daily backups to cloud storage with encryption',
            },
            {
                'department': departments['FIN'],
                'expected_problem': 'Unauthorized access to financial systems',
                'impact': 'Potential financial fraud and regulatory penalties',
                'severity': Risk.Severity.CRITICAL,
                'status': Risk.Status.OPEN,
                'estimated_resolution_duration': 24,
                'resolution_duration_unit': Risk.DurationUnit.HOURS,
                'mitigation_notes': 'Implement multi-factor authentication and access logging',
            },
            {
                'department': departments['OPS'],
                'expected_problem': 'Supply chain disruption from vendor bankruptcy',
                'impact': 'Production delays and inability to fulfill customer orders',
                'severity': Risk.Severity.MEDIUM,
                'status': Risk.Status.OPEN,
                'estimated_resolution_duration': 1,
                'resolution_duration_unit': Risk.DurationUnit.WEEKS,
                'mitigation_notes': 'Maintain relationships with backup vendors',
            },
        ]

        for risk_data in sample_risks:
            risk, created = Risk.objects.get_or_create(
                department=risk_data['department'],
                expected_problem=risk_data['expected_problem'],
                defaults={
                    'impact': risk_data['impact'],
                    'severity': risk_data['severity'],
                    'status': risk_data['status'],
                    'estimated_resolution_duration': risk_data['estimated_resolution_duration'],
                    'resolution_duration_unit': risk_data['resolution_duration_unit'],
                    'mitigation_notes': risk_data['mitigation_notes'],
                    'created_by': admin_user,
                    'updated_by': admin_user,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created risk for {risk.department.code}'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.WARNING('\nLogin Credentials:'))
        self.stdout.write(self.style.WARNING('  Admin: admin / admin123'))
        self.stdout.write(self.style.WARNING('  IT User: it_user / password123'))
        self.stdout.write(self.style.WARNING('  HR User: hr_user / password123'))
        self.stdout.write(self.style.WARNING('  Viewer: viewer / viewer123'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

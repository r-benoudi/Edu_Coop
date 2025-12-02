from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from datetime import date

class Instructor(models.Model):
    """Instructor model"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=200)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=120)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Student(models.Model):
    """Student model"""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    parent_name = models.CharField(max_length=200, blank=True)
    parent_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    registration_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

class Course(models.Model):
    """Course model"""
    COURSE_TYPE_CHOICES = [
        ('tutoring', 'Tutoring'),
        ('it_course', 'IT Course'),
    ]
    
    SUBJECT_CHOICES = [
        ('math', 'Mathematics'),
        ('physics', 'Physics'),
        ('life_sciences', 'Life Sciences'),
        ('it_training', 'IT Training'),
    ]
    
    name = models.CharField(max_length=200)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    description = models.TextField(blank=True)
    instructors = models.ManyToManyField(Instructor, related_name='courses', blank=True)
    monthly_fee = models.DecimalField(max_digits=8, decimal_places=2)
    enrollment_limit = models.PositiveIntegerField(default=30)
    duration_hours = models.PositiveIntegerField(default=8)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def enrolled_count(self):
        return self.enrollments.filter(is_active=True).count()

class Enrollment(models.Model):
    """Enrollment model"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course']

class Attendance(models.Model):
    """Attendance tracking"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused'),
    ]
    
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['enrollment', 'date']

class InstructorHours(models.Model):
    """Track instructor hours for IT courses"""
    instructor = models.ForeignKey('Instructor', on_delete=models.CASCADE, related_name='hours')
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='instructor_hours')
    month = models.DateField()
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['instructor', 'course', 'month']
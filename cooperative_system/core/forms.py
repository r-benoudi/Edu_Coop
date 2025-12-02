from django import forms
from .models import (
    User,
)
from academics.models import Student, Instructor, Course, Enrollment, Attendance, InstructorHours
from cooperative.models import Member

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'phone', 'parent_name', 'parent_phone', 'address', 'date_of_birth', 'is_active']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class InstructorForm(forms.ModelForm):
    class Meta:
        model = Instructor
        fields = ['first_name', 'last_name', 'email', 'phone', 'specialization', 'hourly_rate', 'is_active']


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'course_type', 'subject', 'description', 'instructors', 'monthly_fee', 'enrollment_limit', 'duration_hours', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'instructors': forms.SelectMultiple(attrs={'class': 'h-32'}),
        }


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'enrollment_date', 'is_active']
        widgets = {
            'enrollment_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(is_active=True)
        self.fields['course'].queryset = Course.objects.filter(is_active=True)


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['enrollment', 'date', 'status', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class BulkAttendanceForm(forms.Form):
    course = forms.ModelChoiceField(queryset=Course.objects.filter(is_active=True))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))


class PaymentRecordForm(forms.Form):
    amount_paid = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    payment_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'email', 'phone', 'member_type', 'capital_shares', 'join_date', 'is_active']
        widgets = {
            'join_date': forms.DateInput(attrs={'type': 'date'}),
        }


class InstructorHoursForm(forms.ModelForm):
    class Meta:
        model = InstructorHours
        fields = ['instructor', 'course', 'month', 'hours_worked']
        widgets = {
            'month': forms.DateInput(attrs={'type': 'date'}),
        }


class MonthSelectForm(forms.Form):
    month = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'month'}),
        help_text="Select the month for the report"
    )


class GeneratePaymentsForm(forms.Form):
    month = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="First day of the month to generate payments for"
    )

from cooperative_system.core.models import Student, Course, Enrollment
from datetime import date
import random

# --------- CREATE COURSES ---------
course1, _ = Course.objects.get_or_create(
    name="Mathematics Level 1",
    course_type="tutoring",
    subject="math",
    monthly_fee=250
)

course2, _ = Course.objects.get_or_create(
    name="IT Training Essentials",
    course_type="it_course",
    subject="it_training",
    monthly_fee=500
)

# --------- 30 STUDENTS ---------
first_names = ["Adam","Sara","Youssef","Lina","Hamza","Amal","Imane","Mehdi","Othmane","Aya",
               "Issam","Salma","Reda","Fatima","Yassine","Aya","Kenza","Soufiane","Naoufal",
               "Marwa","Rania","Othmane","Sami","Rachid","Wiam","Youssef","Ines","Mehdi",
               "Salma","Amine"]

last_names = ["Bennani","El Amrani","Ait Ali","Idrissi","Outmane","Soufi","Karimi","Rachidi",
              "El Fassi","Zahra","Bouchaib","Fadili","Chami","Lamrani","Jabrane","Benomar",
              "Tahiri","El Ghali","Idrissi","El Khatib","Bakkali","Douiri","El Hani",
              "Bennouna","Harrak","Guessous","Mansouri","Lamarti","Ettayeb","Cherif"]

students = []
for i in range(30):
    s, _ = Student.objects.get_or_create(
        first_name=first_names[i],
        last_name=last_names[i],
        email=f"student{i+1}@example.com",
        phone=f"06000100{i+1}",
        address="Morocco"
    )
    students.append(s)

# --------- ENROLLMENTS ---------
for s in students:
    Enrollment.objects.get_or_create(student=s, course=course1)
    Enrollment.objects.get_or_create(student=s, course=course2)

print("Seed data created successfully!")

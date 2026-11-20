# AcadGenie: Intelligent Academic Companion
A Django web platform where college students record their marks, get SGPA and CGPA calculated automatically, track performance on a dashboard, and plan the SGPA they need to reach a target CGPA.
Built as a B.Tech Project-1 at Medicaps University, Indore.

## Features

- Student registration and login (JWT for the API)
- Student profile with enrollment number, branch, current semester and target CGPA
- Semester and subject management with credits
- Marks entry with automatic percentage, grade and grade point
- Credit-weighted SGPA per semester and CGPA across completed semesters
- Target CGPA calculator: shows the SGPA required in the remaining semesters and whether it is achievable
- Dashboard with CGPA gauge, grade distribution donut, SGPA/CGPA trend and average percentage per semester
- Versioned REST API under /api/v1/
- Every user sees only their own data

## How it works

- SGPA = Σ (grade point × credits) / Σ credits
- CGPA = Σ (SGPA × semester credits) / Σ credits of completed semesters
- Required SGPA = (target CGPA × total credits − points earned) / remaining credits
  
### Grade scale (10-point):

Percentage	       Grade	      Grade point
90 and above	       O	            10
80 to below 90	     A+	             9
70 to below 80	     A	             8 
60 to below 70	     B+	             7
50 to below 60	     B	             6
40 to below 50	     C	             5
Below 40	           F	             0

## Tech stack

Python , Django, Django REST Framework, SimpleJWT, SQLite, Bootstrap, Chart.js

## Project structure

```text
acadgenie/
│
├── config/                 # Settings and URL routing
│
├── accounts/               # Registration, login, profile
│
├── academics/              # Semesters, subjects, marks
│   └── services.py         # Grading and GPA logic
│
├── dashboard/              # Views, templates, charts
│
├── templates/               # Base template and shared pages
│   └── base.html
│
└── manage.py
```

## Setup

1. Clone the repository
```
git clone https://github.com/tanvipatilx/AcadGenie.git
cd AcadGenie
```

2. Create and activate a virtual environment
```
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Create a .env file in the project root 
```
SECRET_KEY=your-secret-key
DEBUG=True
```

5. Set up the database and run the server
```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

6. Open http://127.0.0.1:8000/

### Author
Tanvi Patil (EN23CS3011077) 
B.Tech Computer Science & Engineering 
Medicaps University, Indore


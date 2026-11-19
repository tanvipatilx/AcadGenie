def calculate_grade(percentage):
    """Returns (grade, grade_point) for a given percentage, on a 10-point scale."""
    if percentage >= 90:
        return 'O', 10
    elif percentage >= 80:
        return 'A+', 9
    elif percentage >= 70:
        return 'A', 8
    elif percentage >= 60:
        return 'B+', 7
    elif percentage >= 50:
        return 'B', 6
    elif percentage >= 40:
        return 'C', 5
    else:
        return 'F', 0


def update_marks_grade(marks_record):
    """Recalculates grade/grade_point on a MarksRecord based on marks_obtained."""
    if marks_record.marks_obtained is None:
        return
    percentage = (marks_record.marks_obtained / marks_record.max_marks) * 100
    grade, grade_point = calculate_grade(percentage)
    marks_record.grade = grade
    marks_record.grade_point = grade_point
    marks_record.save()

def calculate_sgpa(semester):
    """Credit-weighted average of grade points for all graded subjects in a semester."""
    subjects = semester.subjects.select_related('marks').all()
    total_points = 0
    total_credits = 0
    for subject in subjects:
        marks = getattr(subject, 'marks', None)
        if marks and marks.grade_point is not None:
            total_points += marks.grade_point * subject.credits
            total_credits += subject.credits
    if total_credits == 0:
        return None
    sgpa = round(total_points / total_credits, 2)
    semester.sgpa = sgpa
    semester.save()
    return sgpa


def calculate_cgpa(student_profile):
    """Credit-weighted average SGPA across all completed semesters."""
    semesters = student_profile.semesters.filter(is_completed=True, sgpa__isnull=False)
    total_points = 0
    total_credits = 0
    for sem in semesters:
        sem_credits = sum(s.credits for s in sem.subjects.all())
        total_points += float(sem.sgpa) * sem_credits
        total_credits += sem_credits
    if total_credits == 0:
        return None
    return round(total_points / total_credits, 2)

def calculate_required_sgpa(student_profile, target_cgpa, total_semesters=8, credits_per_semester=20):
    """
    Given a target CGPA, calculates the average SGPA needed in remaining semesters.
    Assumes roughly equal credits per semester unless overridden.
    """
    completed = student_profile.semesters.filter(is_completed=True, sgpa__isnull=False)
    completed_count = completed.count()
    remaining_count = total_semesters - completed_count

    if remaining_count <= 0:
        return {"error": "No remaining semesters."}

    earned_points = sum(float(s.sgpa) * credits_per_semester for s in completed)
    earned_credits = completed_count * credits_per_semester
    total_credits = total_semesters * credits_per_semester

    required_total_points = float(target_cgpa) * total_credits
    remaining_points_needed = required_total_points - earned_points
    remaining_credits = total_credits - earned_credits

    required_sgpa = remaining_points_needed / remaining_credits

    return {
        "completed_semesters": completed_count,
        "remaining_semesters": remaining_count,
        "current_cgpa": calculate_cgpa(student_profile),
        "required_sgpa_per_remaining_semester": round(required_sgpa, 2),
        "achievable": 0 <= required_sgpa <= 10,
    }


def get_grade_distribution(student_profile):
    """
    Returns an ordered dict of grade → count across all MarksRecord rows
    belonging to the student's subjects, covering only graded records.

    Canonical order: O, A+, A, B+, B, C, F
    """
    from academics.models import MarksRecord

    GRADE_ORDER = ['O', 'A+', 'A', 'B+', 'B', 'C', 'F']

    records = MarksRecord.objects.filter(
        subject__semester__student=student_profile,
        grade__in=GRADE_ORDER,
    ).values_list('grade', flat=True)

    counts = {g: 0 for g in GRADE_ORDER}
    for g in records:
        counts[g] += 1

    # Return only grades that actually exist (keeps the donut clean)
    return {g: counts[g] for g in GRADE_ORDER if counts[g] > 0}

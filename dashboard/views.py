from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from academics.services import (
    calculate_cgpa,
    calculate_required_sgpa,
    get_grade_distribution,
)


@login_required
def dashboard_view(request):
    # Guard: user exists but has no StudentProfile (e.g. created via admin)
    try:
        profile = request.user.profile
    except Exception:
        logout(request)
        return redirect('register_html')

    semesters = profile.semesters.prefetch_related('subjects__marks').order_by('semester_number')

    cgpa = calculate_cgpa(profile)

    # ── total credits earned across completed semesters ───────────────────────
    total_credits_earned = sum(
        sum(s.credits for s in sem.subjects.all())
        for sem in semesters
        if sem.is_completed
    )

    # ── per-semester data for line/bar charts ─────────────────────────────────
    chart_labels     = []   # "Sem 1", "Sem 2", …
    chart_sgpa       = []   # SGPA per completed semester
    chart_percentage = []   # avg % per completed semester

    for sem in semesters:
        if not sem.is_completed or sem.sgpa is None:
            continue
        chart_labels.append(f"Sem {sem.semester_number}")
        chart_sgpa.append(float(sem.sgpa))

        pcts = []
        for subj in sem.subjects.all():
            marks = getattr(subj, 'marks', None)
            if marks and marks.marks_obtained is not None and marks.max_marks:
                pcts.append(float(marks.marks_obtained) / float(marks.max_marks) * 100)
        chart_percentage.append(round(sum(pcts) / len(pcts), 2) if pcts else 0)

    # ── running CGPA progression ──────────────────────────────────────────────
    running_cgpa    = []
    running_points  = 0.0
    running_credits = 0
    for sem in semesters:
        if not sem.is_completed or sem.sgpa is None:
            continue
        sem_credits      = sum(s.credits for s in sem.subjects.all())
        running_points  += float(sem.sgpa) * sem_credits
        running_credits += sem_credits
        running_cgpa.append(
            round(running_points / running_credits, 2) if running_credits else 0
        )

    # ── subject grade-point bar (current / most recent semester) ─────────────
    subj_chart_labels      = []
    subj_chart_grade_points = []
    current_sem = semesters.filter(is_completed=False).first() or semesters.last()
    if current_sem:
        for subj in current_sem.subjects.all():
            marks = getattr(subj, 'marks', None)
            subj_chart_labels.append(subj.code)
            subj_chart_grade_points.append(
                float(marks.grade_point) if marks and marks.grade_point is not None else 0.0
            )

    # ── CGPA target calculator ────────────────────────────────────────────────
    target_result = None
    if profile.target_cgpa:
        target_result = calculate_required_sgpa(profile, float(profile.target_cgpa))

    # ── Speedometer data ──────────────────────────────────────────────────────
    # current CGPA (0 when no data yet) and target (10 as fallback)
    gauge_current = float(cgpa) if cgpa is not None else 0.0
    gauge_target  = float(profile.target_cgpa) if profile.target_cgpa else 10.0

    # ── Grade-distribution donut data ─────────────────────────────────────────
    grade_dist = get_grade_distribution(profile)   # e.g. {"O":3,"A+":2,"B":1}

    return render(request, 'dashboard/dashboard.html', {
        'profile':               profile,
        'semesters':             semesters,
        'cgpa':                  cgpa,
        'total_credits_earned':  total_credits_earned,
        # line / bar charts
        'chart_labels':          chart_labels,
        'chart_sgpa':            chart_sgpa,
        'chart_percentage':      chart_percentage,
        'running_cgpa':          running_cgpa,
        'subj_chart_labels':     subj_chart_labels,
        'subj_chart_grade_points': subj_chart_grade_points,
        'current_sem':           current_sem,
        # CGPA target
        'target_result':         target_result,
        # NEW — gauge
        'gauge_current':         gauge_current,
        'gauge_target':          gauge_target,
        # NEW — donut
        'grade_dist':            grade_dist,
    })

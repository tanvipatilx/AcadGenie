from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Semester, Subject, MarksRecord
from .serializers import SemesterSerializer, SubjectSerializer, MarksRecordSerializer
from .services import update_marks_grade, calculate_sgpa, calculate_cgpa, calculate_required_sgpa


# ── REST API views (JWT) ──────────────────────────────────────────────────────

class SemesterListCreateView(generics.ListCreateAPIView):
    serializer_class = SemesterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Semester.objects.filter(student__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.profile)


class SemesterDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SemesterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Semester.objects.filter(student__user=self.request.user)


class SubjectListCreateView(generics.ListCreateAPIView):
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subject.objects.filter(
            semester_id=self.kwargs['semester_id'],
            semester__student__user=self.request.user
        )

    def perform_create(self, serializer):
        # Verify the semester belongs to the requesting user before creating
        semester = generics.get_object_or_404(
            Semester,
            pk=self.kwargs['semester_id'],
            student__user=self.request.user,
        )
        subject = serializer.save(semester=semester)
        # Auto-create a blank MarksRecord so marks can be entered immediately
        MarksRecord.objects.get_or_create(subject=subject)


class SubjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Edit or delete a single subject (and its cascaded MarksRecord)."""
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Subject.objects.filter(
            semester__student__user=self.request.user
        )


class MarksUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = MarksRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MarksRecord.objects.filter(subject__semester__student__user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        update_marks_grade(instance)
        calculate_sgpa(instance.subject.semester)


class SGPAView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        semester = Semester.objects.get(pk=pk, student__user=request.user)
        return Response({'semester': semester.semester_number, 'sgpa': semester.sgpa})


class CGPAView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        cgpa = calculate_cgpa(profile)
        return Response({'cgpa': cgpa})


class RequiredSGPAView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        target_cgpa = request.data.get('target_cgpa')
        total_semesters = request.data.get('total_semesters', 8)
        if target_cgpa is None:
            return Response({"error": "target_cgpa is required"}, status=400)
        result = calculate_required_sgpa(
            request.user.profile,
            float(target_cgpa),
            int(total_semesters)
        )
        return Response(result)


# ── HTML / session-based views ────────────────────────────────────────────────

@login_required
def semester_list_html(request):
    profile = request.user.profile
    semesters = profile.semesters.prefetch_related('subjects').order_by('semester_number')
    sem_error = request.session.pop('sem_error', None)
    return render(request, 'academics/semester_list.html', {
        'semesters': semesters,
        'sem_error': sem_error,
    })


@login_required
def semester_create_html(request):
    if request.method == 'POST':
        profile = request.user.profile
        semester_number = request.POST.get('semester_number', '').strip()
        is_completed = bool(request.POST.get('is_completed'))
        try:
            Semester.objects.create(
                student=profile,
                semester_number=int(semester_number),
                is_completed=is_completed,
            )
        except Exception as exc:
            request.session['sem_error'] = str(exc)
    return redirect('semester_list_html')


@login_required
def semester_edit_html(request, pk):
    semester = get_object_or_404(Semester, pk=pk, student__user=request.user)
    error = None
    if request.method == 'POST':
        semester_number = request.POST.get('semester_number', '').strip()
        is_completed = bool(request.POST.get('is_completed'))
        try:
            semester.semester_number = int(semester_number)
            semester.is_completed = is_completed
            semester.save()
            return redirect('semester_list_html')
        except Exception as exc:
            error = str(exc)
    return render(request, 'academics/semester_edit.html', {
        'semester': semester,
        'error': error,
    })


@login_required
def semester_delete_html(request, pk):
    if request.method == 'POST':
        semester = get_object_or_404(Semester, pk=pk, student__user=request.user)
        semester.delete()
    return redirect('semester_list_html')


@login_required
def subject_list_html(request, semester_id):
    semester = get_object_or_404(Semester, pk=semester_id, student__user=request.user)
    subjects = semester.subjects.select_related('marks').order_by('id')
    subj_error = request.session.pop('subj_error', None)

    # compute summary stats for the footer
    total_credits = sum(s.credits for s in subjects)
    pcts = []
    for s in subjects:
        m = getattr(s, 'marks', None)
        if m and m.marks_obtained is not None and m.max_marks:
            pcts.append(float(m.marks_obtained) / float(m.max_marks) * 100)
    avg_percentage = round(sum(pcts) / len(pcts), 2) if pcts else None

    return render(request, 'academics/subject_list.html', {
        'semester': semester,
        'subjects': subjects,
        'subj_error': subj_error,
        'total_credits': total_credits,
        'avg_percentage': avg_percentage,
    })


@login_required
def subject_create_html(request, semester_id):
    if request.method == 'POST':
        semester = get_object_or_404(Semester, pk=semester_id, student__user=request.user)
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        credits = request.POST.get('credits', '').strip()
        try:
            subject = Subject.objects.create(
                semester=semester,
                name=name,
                code=code,
                credits=int(credits),
            )
            MarksRecord.objects.get_or_create(subject=subject)
        except Exception as exc:
            request.session['subj_error'] = str(exc)
    return redirect('subject_list_html', semester_id=semester_id)


@login_required
def subject_edit_html(request, pk):
    subject = get_object_or_404(Subject, pk=pk, semester__student__user=request.user)
    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        credits = request.POST.get('credits', '').strip()
        try:
            subject.name = name
            subject.code = code
            subject.credits = int(credits)
            subject.save()
            # recalculate SGPA in case credits changed
            calculate_sgpa(subject.semester)
            return redirect('subject_list_html', semester_id=subject.semester.id)
        except Exception as exc:
            error = str(exc)
    return render(request, 'academics/subject_edit.html', {
        'subject': subject,
        'error': error,
    })


@login_required
def subject_delete_html(request, pk):
    if request.method == 'POST':
        subject = get_object_or_404(Subject, pk=pk, semester__student__user=request.user)
        semester = subject.semester
        subject.delete()
        calculate_sgpa(semester)
    return redirect('subject_list_html', semester_id=semester.id)


@login_required
def marks_update_html(request, subject_id):
    """Inline marks form on the subject list page."""
    subject = get_object_or_404(Subject, pk=subject_id, semester__student__user=request.user)
    if request.method == 'POST':
        marks_obtained = request.POST.get('marks_obtained', '').strip()
        max_marks = request.POST.get('max_marks', '100').strip()
        marks, _ = MarksRecord.objects.get_or_create(subject=subject)
        try:
            marks.marks_obtained = float(marks_obtained) if marks_obtained else None
            marks.max_marks = float(max_marks) if max_marks else 100
            marks.save()
            update_marks_grade(marks)
            calculate_sgpa(subject.semester)
        except (ValueError, TypeError):
            pass
    return redirect('subject_list_html', semester_id=subject.semester.id)


@login_required
def target_calculator_html(request):
    """POST handler for the CGPA target calculator on the dashboard."""
    if request.method == 'POST':
        target_cgpa = request.POST.get('target_cgpa', '').strip()
        total_semesters = request.POST.get('total_semesters', '8').strip()
        profile = request.user.profile
        try:
            profile.target_cgpa = float(target_cgpa)
            profile.save()
        except (ValueError, TypeError):
            pass
    return redirect('dashboard')


# ── Resource Hub views ────────────────────────────────────────────────────────

from .models import Resource


@login_required
def resource_hub_html(request):
    """
    Main Resource Hub page.
    Shows all resources for the logged-in student's subjects,
    with search and filters for semester, subject, and resource type.
    """
    profile = request.user.profile

    # All semesters + their subjects — used to populate filter dropdowns
    semesters = (
        profile.semesters
        .prefetch_related('subjects')
        .order_by('semester_number')
    )

    # Flat list of all subjects owned by this student
    all_subjects = Subject.objects.filter(
        semester__student=profile
    ).select_related('semester').order_by('semester__semester_number', 'name')

    # Base queryset — only resources belonging to this student's subjects
    qs = Resource.objects.filter(
        subject__semester__student=profile
    ).select_related('subject__semester')

    # ── Apply filters from GET params ──────────────────────────────────────
    q            = request.GET.get('q', '').strip()
    sem_filter   = request.GET.get('semester', '').strip()
    subj_filter  = request.GET.get('subject', '').strip()
    type_filter  = request.GET.get('resource_type', '').strip()

    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)
        # Re-apply base ownership guard after OR
        qs = qs.filter(subject__semester__student=profile)

    if sem_filter:
        qs = qs.filter(subject__semester__id=sem_filter)

    if subj_filter:
        qs = qs.filter(subject__id=subj_filter)

    if type_filter:
        qs = qs.filter(resource_type=type_filter)

    qs = qs.order_by('-created_at')

    # Group resources by semester → subject for the grouped view
    grouped = {}   # { semester_obj: { subject_obj: [resource, …] } }
    for resource in qs:
        sem  = resource.subject.semester
        subj = resource.subject
        grouped.setdefault(sem, {}).setdefault(subj, []).append(resource)

    return render(request, 'academics/resource_hub.html', {
        'semesters':      semesters,
        'all_subjects':   all_subjects,
        'resource_types': Resource.RESOURCE_TYPES,
        'resources':      qs,
        'grouped':        grouped,
        # keep filter state for re-populating form
        'q':              q,
        'sem_filter':     sem_filter,
        'subj_filter':    subj_filter,
        'type_filter':    type_filter,
    })


@login_required
def resource_add_html(request):
    """
    Add a new resource. Accepts both file uploads and external URLs.
    Can be pre-filled with ?subject=<id> from the subject list page.
    """
    profile   = request.user.profile
    error     = None

    all_subjects = Subject.objects.filter(
        semester__student=profile
    ).select_related('semester').order_by('semester__semester_number', 'name')

    preselected_subject = request.GET.get('subject', '')

    if request.method == 'POST':
        title         = request.POST.get('title', '').strip()
        resource_type = request.POST.get('resource_type', '').strip()
        subject_id    = request.POST.get('subject', '').strip()
        url           = request.POST.get('url', '').strip()
        description   = request.POST.get('description', '').strip()
        uploaded_file = request.FILES.get('file')

        # Basic validation
        if not title:
            error = 'Title is required.'
        elif not resource_type:
            error = 'Resource type is required.'
        elif not subject_id:
            error = 'Subject is required.'
        elif not url and not uploaded_file:
            error = 'Provide either a file upload or a URL.'
        elif url and uploaded_file:
            error = 'Provide a file OR a URL, not both.'
        else:
            subject = get_object_or_404(
                Subject, pk=subject_id, semester__student=profile
            )
            Resource.objects.create(
                subject=subject,
                title=title,
                resource_type=resource_type,
                url=url or None,
                file=uploaded_file or None,
                description=description,
                uploaded_by=profile,
            )
            return redirect('resource_hub_html')

    return render(request, 'academics/resource_add.html', {
        'all_subjects':       all_subjects,
        'resource_types':     Resource.RESOURCE_TYPES,
        'error':              error,
        'preselected_subject': preselected_subject,
    })


@login_required
def resource_edit_html(request, pk):
    """Edit title, description, type, and URL/file of an existing resource."""
    profile  = request.user.profile
    resource = get_object_or_404(
        Resource, pk=pk, subject__semester__student=profile
    )
    error = None

    all_subjects = Subject.objects.filter(
        semester__student=profile
    ).select_related('semester').order_by('semester__semester_number', 'name')

    if request.method == 'POST':
        title         = request.POST.get('title', '').strip()
        resource_type = request.POST.get('resource_type', '').strip()
        subject_id    = request.POST.get('subject', '').strip()
        url           = request.POST.get('url', '').strip()
        description   = request.POST.get('description', '').strip()
        uploaded_file = request.FILES.get('file')
        clear_file    = request.POST.get('clear_file')

        if not title:
            error = 'Title is required.'
        elif not resource_type:
            error = 'Resource type is required.'
        else:
            subject = get_object_or_404(
                Subject, pk=subject_id, semester__student=profile
            )
            resource.title         = title
            resource.resource_type = resource_type
            resource.subject       = subject
            resource.description   = description

            if uploaded_file:
                resource.file = uploaded_file
                resource.url  = None
            elif url:
                resource.url  = url
                if clear_file:
                    resource.file = None
            elif clear_file:
                resource.file = None
                resource.url  = None

            resource.save()
            return redirect('resource_hub_html')

    return render(request, 'academics/resource_edit.html', {
        'resource':       resource,
        'all_subjects':   all_subjects,
        'resource_types': Resource.RESOURCE_TYPES,
        'error':          error,
    })


@login_required
def resource_delete_html(request, pk):
    """Delete a resource (POST only)."""
    profile  = request.user.profile
    resource = get_object_or_404(
        Resource, pk=pk, subject__semester__student=profile
    )
    if request.method == 'POST':
        resource.delete()
    return redirect('resource_hub_html')

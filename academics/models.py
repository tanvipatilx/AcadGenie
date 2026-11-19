from django.db import models
from accounts.models import StudentProfile


class Semester(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='semesters')
    semester_number = models.PositiveSmallIntegerField()
    sgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'semester_number')

    def __str__(self):
        return f"{self.student.user.username} - Sem {self.semester_number}"


class Subject(models.Model):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20)
    credits = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('semester', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class MarksRecord(models.Model):
    subject = models.OneToOneField(Subject, on_delete=models.CASCADE, related_name='marks')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    grade = models.CharField(max_length=2, blank=True)
    grade_point = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.subject.code} - {self.grade or 'Not graded'}"


class Resource(models.Model):
    """A study resource attached to a subject (and therefore a semester)."""

    TYPE_NOTES       = 'notes'
    TYPE_PDF         = 'pdf'
    TYPE_PYP         = 'pyp'          # Previous-year paper
    TYPE_IMP_QUESTIONS = 'imp_q'      # Important questions
    TYPE_YOUTUBE     = 'youtube'
    TYPE_REFERENCE   = 'reference'

    RESOURCE_TYPES = [
        (TYPE_NOTES,         'Notes'),
        (TYPE_PDF,           'PDF'),
        (TYPE_PYP,           'Previous-Year Paper'),
        (TYPE_IMP_QUESTIONS, 'Important Questions'),
        (TYPE_YOUTUBE,       'YouTube Link'),
        (TYPE_REFERENCE,     'Reference Material'),
    ]

    subject      = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='resources')
    title        = models.CharField(max_length=200)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    # One of these two is filled: a file upload OR an external URL
    file         = models.FileField(upload_to='resources/', null=True, blank=True)
    url          = models.URLField(max_length=500, null=True, blank=True)
    description  = models.TextField(blank=True)
    uploaded_by  = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='resources'
    )
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_resource_type_display()}] {self.title}"

    @property
    def is_link(self):
        return bool(self.url)

    @property
    def is_youtube(self):
        return self.resource_type == self.TYPE_YOUTUBE
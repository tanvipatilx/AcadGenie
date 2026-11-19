from django.db import models
from django.contrib.auth.models import User


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    enrollment_no = models.CharField(max_length=20, unique=True)
    branch = models.CharField(max_length=100)
    current_semester = models.PositiveSmallIntegerField(default=1)
    target_cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.enrollment_no})"
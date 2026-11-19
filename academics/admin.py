from django.contrib import admin
from .models import Semester, Subject, MarksRecord

admin.site.register(Semester)
admin.site.register(Subject)
admin.site.register(MarksRecord)
from rest_framework import serializers
from .models import Semester, Subject, MarksRecord


class MarksRecordSerializer(serializers.ModelSerializer):
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = MarksRecord
        fields = ['id', 'marks_obtained', 'max_marks', 'grade', 'grade_point', 'percentage']
        read_only_fields = ['grade', 'grade_point']

    def get_percentage(self, obj):
        if obj.marks_obtained is not None and obj.max_marks:
            return round(float(obj.marks_obtained) / float(obj.max_marks) * 100, 2)
        return None


class SubjectSerializer(serializers.ModelSerializer):
    marks = MarksRecordSerializer(read_only=True)

    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'credits', 'marks']


class SemesterSerializer(serializers.ModelSerializer):
    subjects = SubjectSerializer(many=True, read_only=True)
    total_credits = serializers.SerializerMethodField()
    semester_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Semester
        fields = ['id', 'semester_number', 'sgpa', 'is_completed', 'subjects',
                  'total_credits', 'semester_percentage']

    def get_total_credits(self, obj):
        return sum(s.credits for s in obj.subjects.all())

    def get_semester_percentage(self, obj):
        """Average percentage across all subjects that have marks entered."""
        subjects = obj.subjects.all()
        percentages = []
        for subject in subjects:
            marks = getattr(subject, 'marks', None)
            if marks and marks.marks_obtained is not None and marks.max_marks:
                percentages.append(
                    float(marks.marks_obtained) / float(marks.max_marks) * 100
                )
        if not percentages:
            return None
        return round(sum(percentages) / len(percentages), 2)
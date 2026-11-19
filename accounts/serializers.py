from django.contrib.auth.models import User
from rest_framework import serializers
from .models import StudentProfile


class RegisterSerializer(serializers.ModelSerializer):
    enrollment_no = serializers.CharField(write_only=True)
    branch = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'enrollment_no', 'branch']

    def create(self, validated_data):
        enrollment_no = validated_data.pop('enrollment_no')
        branch = validated_data.pop('branch')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
        )
        StudentProfile.objects.create(
            user=user,
            enrollment_no=enrollment_no,
            branch=branch,
        )
        return user

class StudentProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = StudentProfile
        fields = ['username', 'email', 'enrollment_no', 'branch',
                  'current_semester', 'target_cgpa']
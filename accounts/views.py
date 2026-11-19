from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from rest_framework import generics, permissions

from .models import StudentProfile
from .serializers import RegisterSerializer, StudentProfileSerializer


# ── REST API views (JWT) ──────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.profile


# ── HTML / session-based views ────────────────────────────────────────────────

def register_html(request):
    """Create a new account and auto-login the user."""
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        enrollment_no = request.POST.get('enrollment_no', '').strip()
        branch = request.POST.get('branch', '').strip()

        if User.objects.filter(username=username).exists():
            error = 'Username already taken.'
        elif StudentProfile.objects.filter(enrollment_no=enrollment_no).exists():
            error = 'Enrollment number already registered.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters.'
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            StudentProfile.objects.create(user=user, enrollment_no=enrollment_no, branch=branch)
            login(request, user)
            return redirect('dashboard')

    return render(request, 'accounts/register.html', {'error': error})


def login_html(request):
    """Session-based login for the HTML frontend."""
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next', 'dashboard'))
        error = 'Invalid username or password.'

    return render(request, 'accounts/login.html', {'error': error})


def logout_html(request):
    """Session logout — POST only to prevent CSRF."""
    if request.method == 'POST':
        logout(request)
    return redirect('login_html')


@login_required
def profile_html(request):
    """View/edit the student profile via HTML form."""
    profile = request.user.profile
    success = False
    error = None

    if request.method == 'POST':
        branch = request.POST.get('branch', '').strip()
        current_semester = request.POST.get('current_semester', '').strip()
        target_cgpa = request.POST.get('target_cgpa', '').strip()

        try:
            profile.branch = branch
            profile.current_semester = int(current_semester) if current_semester else profile.current_semester
            profile.target_cgpa = float(target_cgpa) if target_cgpa else None
            profile.save()
            success = True
        except (ValueError, TypeError) as exc:
            error = f'Invalid value: {exc}'

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'success': success,
        'error': error,
    })
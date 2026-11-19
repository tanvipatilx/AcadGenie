from django.urls import path
from .views import (
    # REST API
    SemesterListCreateView, SemesterDetailView,
    SubjectListCreateView, SubjectDetailView,
    MarksUpdateView, SGPAView, CGPAView, RequiredSGPAView,
    # HTML — semesters / subjects / marks / target
    semester_list_html, semester_create_html, semester_edit_html, semester_delete_html,
    subject_list_html, subject_create_html, subject_edit_html, subject_delete_html,
    marks_update_html, target_calculator_html,
    # HTML — resource hub
    resource_hub_html, resource_add_html, resource_edit_html, resource_delete_html,
)

urlpatterns = [
    # ── REST API ──────────────────────────────────────────────────────────────
    path('semesters/', SemesterListCreateView.as_view(), name='semester-list'),
    path('semesters/<int:pk>/', SemesterDetailView.as_view(), name='semester-detail'),
    path('semesters/<int:semester_id>/subjects/', SubjectListCreateView.as_view(), name='subject-list'),
    path('subjects/<int:pk>/', SubjectDetailView.as_view(), name='subject-detail'),
    path('marks/<int:pk>/', MarksUpdateView.as_view(), name='marks-update'),
    path('semesters/<int:pk>/sgpa/', SGPAView.as_view(), name='semester-sgpa'),
    path('cgpa/', CGPAView.as_view(), name='cgpa'),
    path('cgpa/target/', RequiredSGPAView.as_view(), name='cgpa-target'),

    # ── HTML — semesters & subjects ───────────────────────────────────────────
    path('html/semesters/', semester_list_html, name='semester_list_html'),
    path('html/semesters/create/', semester_create_html, name='semester_create_html'),
    path('html/semesters/<int:pk>/edit/', semester_edit_html, name='semester_edit_html'),
    path('html/semesters/<int:pk>/delete/', semester_delete_html, name='semester_delete_html'),
    path('html/semesters/<int:semester_id>/subjects/', subject_list_html, name='subject_list_html'),
    path('html/semesters/<int:semester_id>/subjects/create/', subject_create_html, name='subject_create_html'),
    path('html/subjects/<int:pk>/edit/', subject_edit_html, name='subject_edit_html'),
    path('html/subjects/<int:pk>/delete/', subject_delete_html, name='subject_delete_html'),
    path('html/subjects/<int:subject_id>/marks/', marks_update_html, name='marks_update_html'),
    path('html/target/', target_calculator_html, name='target_calculator_html'),

    # ── HTML — resource hub ───────────────────────────────────────────────────
    path('html/resources/', resource_hub_html, name='resource_hub_html'),
    path('html/resources/add/', resource_add_html, name='resource_add_html'),
    path('html/resources/<int:pk>/edit/', resource_edit_html, name='resource_edit_html'),
    path('html/resources/<int:pk>/delete/', resource_delete_html, name='resource_delete_html'),
]
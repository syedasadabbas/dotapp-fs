from django.urls import path
from django.contrib.auth import views as auth_views

from dot_app import views
from .views.auth_views import register, logout_view
from .views.profile_views import profile
from .views.dashboard_views import dashboard
from .views.track_views import track_list, track_detail, track
from .views.dot_views import dot_detail
from .views.subdot_views import subdot_detail, toggle_bookmark, ask_instructor
from .views.note_views import add_note, create_note, update_note, delete_note, get_note, get_all_notes
from .views.progress_views import mark_completed, progress_view, update_progress
from .views.assessment_views import start_assessment, assessment_result
from .views.subscription_views import CancelView, CreateStripeCheckoutSessionView, SuccessView, subscription_view, payment_view

app_name="learning"

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='learning/login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),
    path('tracks/', track_list, name='track_list'),
    path('track/<int:track_id>/', track_detail, name='track_detail'),
    path('track/<int:track_id>/dot/<int:dot_id>/', dot_detail, name='dot_detail'),
    path('subdot/<int:subdot_id>/', subdot_detail, name='subdot_detail'),
    path('subdot/<int:subdot_id>/bookmark/', toggle_bookmark, name='toggle_bookmark'),
    path('subdot/<int:subdot_id>/note/', add_note, name='add_note'),
    path('subdot/<int:subdot_id>/complete/', mark_completed, name='mark_completed'),
    path('subdot/<int:subdot_id>/ask/', ask_instructor, name='ask_instructor'),
    path('subdot/<int:subdot_id>/update-progress/', update_progress, name='update_progress'),
    path('progress/', progress_view, name='progress'),
    # Notes API endpoints
    path('api/notes/create/', create_note, name='create_note'),
    path('api/notes/<int:note_id>/update/', update_note, name='update_note'),
    path('api/notes/<int:note_id>/delete/', delete_note, name='delete_note'),
    path('api/notes/<int:note_id>/get/', get_note, name='get_note'),
    path('api/notes/', get_all_notes, name='get_all_notes'),
    path('dot/<int:dot_id>/start-assessment/', start_assessment, name='start_assessment'),
    path('assessment-result/<int:result_id>/', assessment_result, name='assessment_result'),

    path('subscription/', subscription_view, name='subscription_view'),
    path('payment/', payment_view, name='payment_view'),
    path(
        "create-checkout-session/<int:pk>/",
        CreateStripeCheckoutSessionView.as_view(),
        name="create-checkout-session",
    ),
    # path("success/", SuccessView.as_view(), name="success"),
    # path("cancel/", CancelView.as_view(), name="cancel"),
]

from django.urls import path
from .views import editor_dashboard, view_Dots, view_subdots, view_topics, view_topic, subscribe_editor, add_topic, content_addition, add_subdot, login_view, subscription_view, payment_view, earnings_view, register, logout_view

urlpatterns = [
    path('', editor_dashboard, name='editor_dashboard'),
    path('Dots/<int:track_id>/', view_Dots, name='view_Dots'),
    path('subdots/<int:Dot_id>/', view_subdots, name='view_subdots'),
    path('topics/<int:subdot_id>/', view_topics, name='view_topics'),
    path('topic/<int:topic_id>/', view_topic, name='view_topic'),
    path('subscribe/', subscribe_editor, name='subscribe_editor'),
    path('subscription/', subscription_view, name='subscription_view'),
    path('payment/', payment_view, name='payment_view'),
    path('earnings/', earnings_view, name='earnings_view'),
    path('add_topic/<int:subdot_id>/', add_topic, name='add_topic'),  # New URL for adding topics
    path('content_addition/', content_addition, name='content_addition'),  # New URL for content addition
    path('add_subdot/<int:Dot_id>/', add_subdot, name='add_subdot'),  # New URL for adding subdots
    path('login/', login_view, name='login_view'),  # New URL for login
    path('logout/', logout_view, name='logout_view'),
    path('register/', register, name='register_view'),
]

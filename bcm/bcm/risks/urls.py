from django.urls import path
from . import views

app_name = 'risks'

urlpatterns = [
    path('', views.risk_list, name='list'),
    path('<int:pk>/', views.risk_detail, name='detail'),
    path('create/', views.risk_create, name='create'),
    path('<int:pk>/update/', views.risk_update, name='update'),
    path('<int:pk>/delete/', views.risk_delete, name='delete'),
    path('<int:pk>/lock/', views.risk_lock, name='lock'),
    path('<int:pk>/unlock/', views.risk_unlock, name='unlock'),
]

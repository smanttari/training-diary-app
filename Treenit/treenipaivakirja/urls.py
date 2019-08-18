from django.urls import include,path
from rest_framework.urlpatterns import format_suffix_patterns
from treenipaivakirja import views


urlpatterns = [
    path('', views.index, name='index'),
    path('trainings/', views.trainings_view, name='trainings'),
    path('trainings/add/', views.training_add, name='training_add'),
    path('trainings/<int:pk>/modify', views.training_modify, name='training_modify'),
    path('trainings/<int:pk>/delete', views.training_delete, name='training_delete'),
    path('sport/add', views.sport_add, name='sport_add'),
    path('sport/<int:pk>/modify', views.sport_modify, name='sport_modify'),
    path('sport/<int:pk>/delete', views.sport_delete, name='sport_delete'),
    path('reports/', views.reports, name='reports'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('zone/add/', views.zone_add, name='zone_add'),
    path('zone/<int:pk>/modify', views.zone_modify, name='zone_modify'),
    path('zone/<int:pk>/delete', views.zone_delete, name='zone_delete'),
    path('settings/', views.settings_view, name='settings'),
    path('register', views.register, name='register'),
    path('trainings_list/', views.TrainingsList.as_view()),
    path('training_detail/<int:pk>/', views.TrainingDetail.as_view())
]

urlpatterns = format_suffix_patterns(urlpatterns)
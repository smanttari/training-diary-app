from django.urls import include, path
from treenipaivakirja import views


urlpatterns = [
    path('', views.index, name='index'),
    path('trainings/', views.trainings_view, name='trainings'),
    path('trainings/add/', views.training_add, name='training_add'),
    path('trainings/<int:pk>/modify', views.training_modify, name='training_modify'),
    path('trainings/<int:pk>/delete', views.training_delete, name='training_delete'),
    path('trainings/data', views.trainings_data, name='trainings_data'),
    path('trainings/<int:pk>/details', views.training_details, name='training_details'),
    path('trainings/map/', views.trainings_map, name='map'),
    path('trainings/map/data/', views.trainings_map_data, name='map_data'),
    path('reports/amounts/', views.reports_amounts, name='reports_amounts'),
    path('reports/sports/', views.reports_sports, name='reports_sports'),
    path('reports/zones/', views.reports_zones, name='reports_zones'),
    path('recovery/', views.recovery, name='recovery'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('settings/', views.settings_view, name='settings'),
    path('register', views.register, name='register'),
    path('accesslink_callback', views.accesslink_callback, name='accesslink_callback'),
    path('accesslink_trainings', views.accesslink_trainings, name='accesslink_trainings'),
    path('accesslink_recovery', views.accesslink_recovery, name='accesslink_recovery'),
    path('oura_callback', views.oura_callback, name='oura_callback'),
    path('oura_recovery', views.oura_recovery, name='oura_recovery')
]

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('scene/', views.scene, name='scene'),
    path('configuration/', views.configuration, name='configuration'),
    path('comparaison/', views.comparaison, name='comparaison'),
    path('generation/', views.generation, name='generation'),
    path('uploadZipFile/', views.upload_zip_file, name='uploadZipFile'),
    path('delete_folder/', views.delete_folder_view, name='delete_folder'),
    path('save_configuration/', views.save_configuration, name='save_configuration'),
    path('get_table_names/', views.get_table_names, name='get_table_names'),
    path('save_version/', views.save_version, name='save_version'),
    path('get_parameters/', views.get_parameters, name='get_parameters'),
    path('get_subfolders/', views.get_subfolders, name='get_subfolders'),
    path('view_all_images/', views.view_all_images, name='view_all_images'),
    path('get_image_names/', views.get_image_names, name='get_image_names'),
    path('check_image_presence/', views.check_image_presence, name='check_image_presence'),
    path('get_image/', views.get_image, name='get_image'),
    path('get_selected_version_params/', views.get_selected_version_params, name='get_selected_version_params'),

] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
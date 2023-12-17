from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authentication/', include('server.authentication.urls')),
    # path('authentication/registration/', include('dj_rest_auth.registration.urls')),
    path('profile/', include('server.profiles.urls')),
    path('workouts/', include('server.workouts.urls')),
]

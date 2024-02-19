from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authentication/', include('server.authentication.urls')),
    path('profile/', include('server.profiles.urls')),
    path('workouts/', include('server.workouts.urls')),
    path('health/', include('server.health.urls'))
]

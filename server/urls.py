from django.contrib import admin
from django.templatetags.static import static
from django.urls import path, include

from server import settings

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('authentication/', include('server.authentication.urls')),
                  path('profile/', include('server.profiles.urls')),
                  path('workouts/', include('server.workouts.urls')),
                  path('health/', include('server.health.urls'))
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

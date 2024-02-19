from django.urls import path, include

from server.health.views import EditMeasures, EditGoal, EditActivity

urlpatterns = [
    path('measures/edit/', EditMeasures.as_view(), name='edit measures'),
    path('fitness/', include([
        path('goal/edit/', EditGoal.as_view(), name='edit fitness data'),
        path('activity/edit/', EditActivity.as_view(), name='edit activity'),
    ])),

]

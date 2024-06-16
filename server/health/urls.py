from django.urls import path, include

from server.health.views import EditMeasures, FitnessActivityLevel, ProfileWeightView, \
    ProfileHeightView, FitnessGoalView

urlpatterns = [
    path('measures/', include([
        path('edit/', EditMeasures.as_view(), name='edit measures'),
        path('weight/', ProfileWeightView.as_view(), name='profile weight'),
        path('height/', ProfileHeightView.as_view(), name='profile height'),
    ])),
    path('fitness/', include([
        path('goal/', FitnessGoalView.as_view(), name='edit fitness data'),
        path('activity/', FitnessActivityLevel.as_view(), name='edit activity'),

    ])),

]

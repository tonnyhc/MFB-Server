from django.urls import path, include

from server.health.views import EditMeasures, EditGoal, EditActivity, ProfileGoalView, ProfileWeightView

urlpatterns = [
    path('measures/', include([
        path('edit/', EditMeasures.as_view(), name='edit measures'),
        path('weight/', ProfileWeightView.as_view(), name='profile weight'),
    ])),
    path('fitness/', include([

        path('goal/edit/', EditGoal.as_view(), name='edit fitness data'),
        path('activity/edit/', EditActivity.as_view(), name='edit activity'),
        path('details/', include([
            path('goal/', ProfileGoalView.as_view(), name='profile goal'),
        ])),
    ])),

]

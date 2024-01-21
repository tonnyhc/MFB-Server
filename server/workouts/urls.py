from django.urls import path, include

from server.workouts.views import CreateWorkoutPlanView, CreateExerciseView, SearchExerciseView, WorkoutsByUserListView, \
    WorkoutPlanDetailsView, publish_workout

urlpatterns = [
    path('workout-plan/', include([
        path('by-user/', WorkoutsByUserListView.as_view(), name='own workout plans list view'),
        path('create/', CreateWorkoutPlanView.as_view(), name='create workout plan view'),
        path('details/<int:id>/', WorkoutPlanDetailsView.as_view(), name='workout plan details'), ]
    )),
    # path('workout/', include([
    #     path("<int:id>/publish/", publish_workout.as_view(), name='publish workout'),
    # ])),
    path('exercise/', include([
        path('create/', CreateExerciseView.as_view(), name='create exercise view'),
        path('search/', SearchExerciseView.as_view(), name='search exercise')
    ]))

]

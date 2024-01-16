from django.urls import path, include

from server.workouts.views import CreateWorkoutPlanView, CreateExerciseView, SearchExerciseView, WorkoutsByUserListView, \
    WorkoutPlanDetailsView

urlpatterns = [
    path('workout-plan/', include([
        path('by-user/', WorkoutsByUserListView.as_view(), name='own workouts list view'),
        path('create/', CreateWorkoutPlanView.as_view(), name='create workout plan view'),
        path('details/<int:id>/', WorkoutPlanDetailsView.as_view(), name='workout details'), ]
    )),
    path('exercise/', include([
        path('create/', CreateExerciseView.as_view(), name='create exercise view'),
        path('search/', SearchExerciseView.as_view(), name='search exercise')
    ]))

]

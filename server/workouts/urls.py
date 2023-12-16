from django.urls import path

from server.workouts.views import CreateWorkoutPlanView, CreateExerciseView, SearchExerciseView, WorkoutsByUserListView, \
    WorkoutPlanDetailsView

urlpatterns = [
    path('own-workout-plans/', WorkoutsByUserListView.as_view(), name='own workouts list view'),
    path('workout-plan/<int:id>', WorkoutPlanDetailsView.as_view(), name='workout details'),
    path('create-workout-plan/', CreateWorkoutPlanView.as_view(), name='create workout plan view'),
    path('create-exercise/', CreateExerciseView.as_view(), name='create exercise view'),
    path('search_exercise/', SearchExerciseView.as_view(), name='search exercise')

]
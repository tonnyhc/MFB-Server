from django.urls import path

from server.workouts.views import CreateWorkoutPlanView, CreateExerciseView, SearchExerciseView

urlpatterns = [
    path('create-workout-plan/', CreateWorkoutPlanView.as_view(), name='create workout plan view'),
    path('create-exercise/', CreateExerciseView.as_view(), name='create exercise view'),
    path('search_exercise/', SearchExerciseView.as_view(), name='search exercise')

]
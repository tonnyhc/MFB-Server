from django.urls import path, include

from server.workouts.views import CreateWorkoutPlanView, CreateExerciseView, SearchExerciseView, WorkoutsByUserListView, \
    WorkoutPlanDetailsView, publish_workout, WorkoutSessionDetailsView, AddSetToExerciseSession, \
    RemoveSetFromExerciseSession, EditSet, GetExerciseProgress, MuscleGroupsListView, CreateWorkoutView, \
    ExercisesByMuscleGroup

urlpatterns = [
    path('workout-plan/', include([
        path('by-user/', WorkoutsByUserListView.as_view(), name='own workout plans list view'),
        path('create/', CreateWorkoutPlanView.as_view(), name='create workout plan view'),
        path('details/<int:id>/', WorkoutPlanDetailsView.as_view(), name='workout plan details'), ]
    )),
    path('exercise/', include([
        path('create/', CreateExerciseView.as_view(), name='create exercise view'),
        path('search/', SearchExerciseView.as_view(), name='search exercise'),
        path('session/', include([
            path("add-set/<int:session_id>/", AddSetToExerciseSession.as_view(), name='add set to exercise session'),
            path('progress/<int:session_id>/', GetExerciseProgress.as_view(), name='exercise session progress'),
            path('delete-set/<int:set_id>/', RemoveSetFromExerciseSession.as_view(),
                 name='delete set from exercise session'),
            path('update-set/<int:set_id>/', EditSet.as_view(), name='edit set data'),
        ]))
    ])),
    path('workout/', include([
        path('session/<int:id>/', WorkoutSessionDetailsView.as_view(), name='workout session details'),
        path('create/', CreateWorkoutView.as_view(), name='create workout'),
        # path('publish/<int:id>', publish_workout, name='publish workout')
    ])),
    path('muscle-group/', include([
        path('list/', MuscleGroupsListView.as_view(), name='muscle group list view'),
        path('list-exercises/', ExercisesByMuscleGroup.as_view(), name='exercises muscle group list view')

    ]))

]

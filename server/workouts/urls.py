from django.urls import path, include

from server.workouts.exercise_views import CreateCustomExerciseView, ExerciseDetailsView, SearchExerciseView, \
    GetExerciseProgress, EditExerciseSessionView, ExercisesByMuscleGroup, EditExerciseSessionNotesView
from server.workouts.set_views import AddSetToExerciseSession, RemoveSetFromExerciseSession, EditSet
from server.workouts.views import CreateRoutineView, RoutinesListView, \
    WorkoutPlanDetailsView, publish_workout, WorkoutSessionDetailsView, CreateWorkoutView, \
    MuscleGroupsListView, WorkoutSearchView, WorkoutSessionEditView, DeleteWorkoutPlanView, WorkoutSessionDeleteView, \
    AddWorkoutToRoutineView, WorkoutsListView, CreateWorkoutTemplateView, WorkoutTemplateListView, \
    WorkoutTemplateDetailsView

urlpatterns = [
    path('routine/', include([
        path('list/', RoutinesListView.as_view(), name='own workout plans list view'),
        path('create/', CreateRoutineView.as_view(), name='create workout plan view'),
        path('delete/<int:id>/', DeleteWorkoutPlanView.as_view(), name='delete workout plan view'),
        path('details/<int:id>/', WorkoutPlanDetailsView.as_view(), name='workout plan details'),
        path('add-workout/<int:id>/', AddWorkoutToRoutineView.as_view(), name='add workout to routine')
    ]
    )),
    path('exercise/', include([
        path('create/', CreateCustomExerciseView.as_view(), name='create exercise view'),
        path('details/<int:pk>/', ExerciseDetailsView.as_view(), name='exercise details view'),
        path('search/', SearchExerciseView.as_view(), name='search exercise'),
        path('session/', include([
            path('edit/<int:session_id>/', EditExerciseSessionView.as_view(), name='edit exercise session'),
            path('notes/<int:session_id>/', EditExerciseSessionNotesView.as_view(), name='edit exercise session notes'),
            path("add-set/<int:session_id>/", AddSetToExerciseSession.as_view(), name='add set to exercise session'),
            path('progress/<int:session_id>/', GetExerciseProgress.as_view(), name='exercise session progress'),
            path('delete-set/<int:set_id>/', RemoveSetFromExerciseSession.as_view(),
                 name='delete set from exercise session'),
            path('update-set/<int:set_id>/', EditSet.as_view(), name='edit set data'),
        ])),

    ])),
    path('workout/', include([
        path('list/', WorkoutsListView.as_view(), name='workout list view'),
        path('session/<int:id>/', WorkoutSessionDetailsView.as_view(), name='workout session details'),
        path('session/edit/<int:pk>/', WorkoutSessionEditView.as_view(), name='workout session edit '),
        path('session/delete/<int:pk>/', WorkoutSessionDeleteView.as_view(), name='workout session delete'),
        path('create/', CreateWorkoutView.as_view(), name='create workout'),
        path('template/create/', CreateWorkoutTemplateView.as_view(), name='create workout template'),
        path('template/list/', WorkoutTemplateListView.as_view(), name='workout template list view'),
        path('template/<int:pk>/', WorkoutTemplateDetailsView.as_view(), name='workout template details view'),
        path('search/', WorkoutSearchView.as_view(), name='search workout'),
        # path('publish/<int:id>', publish_workout, name='publish workout')
    ])),
    path('muscle-group/', include([
        path('list/', MuscleGroupsListView.as_view(), name='muscle group list view'),
        path('list-exercises/', ExercisesByMuscleGroup.as_view(), name='exercises muscle group list view')

    ]))

]

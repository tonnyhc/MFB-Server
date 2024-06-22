import cloudinary
from cloudinary.models import CloudinaryField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models, transaction, IntegrityError
from simple_history.models import HistoricalRecords

from server.profiles.models import Profile
from django.db.models import Max

from server.utils import string_to_bool


class MuscleGroup(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Rest(models.Model):
    minutes = models.IntegerField(default=0)
    seconds = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.minutes}m {self.seconds}s"


class Set(models.Model):
    weight = models.FloatField(
        blank=True,
        null=True
    )
    reps = models.IntegerField(
        blank=True,
        null=True
    )
    min_reps = models.IntegerField(
        blank=True,
        null=True
    )
    max_reps = models.IntegerField(
        blank=True,
        null=True
    )
    to_failure = models.BooleanField(
        default=False
    )
    bodyweight = models.BooleanField(
        default=False
    )
    # this is the index the set will be in the exercise session
    set_index = models.PositiveIntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )

    history = HistoricalRecords()

    @staticmethod
    def edit_data(set_instance, set_data):
        set_instance.reps = set_data['reps']
        set_instance.weight = set_data['weight']
        set_instance.min_reps = set_data['min_reps']
        set_instance.max_reps = set_data['max_reps']
        set_instance.to_failure = set_data['to_failure']
        set_instance.bodyweight = set_data['bodyweight']

        set_instance.save()
        return set_instance

    @staticmethod
    def remove_set_instance(set_instance):
        set_instance.delete()
        set_instance.save()

    class Meta:
        ordering = ['set_index']


class Interval(models.Model):
    time = models.PositiveIntegerField()
    distance = models.PositiveIntegerField()
    level = models.PositiveIntegerField()
    pace = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)

    index_in_session = models.PositiveIntegerField(
        default=0
    )


class Exercise(models.Model):
    MAX_LEN_TIPS = 255
    MAX_LEN_NAME = 50
    name = models.CharField(
        max_length=MAX_LEN_NAME,
    )
    # cover_photo = CloudinaryField('image', blank=True, null=True)
    targeted_muscle_groups = models.ManyToManyField(MuscleGroup, blank=True,
                                                    null=True)
    instructions = models.TextField(
        blank=True,
        null=True
    )

    video_tutorial = CloudinaryField(resource_type="video", blank=True, null=True)
    tips_and_tricks = models.TextField(
        max_length=MAX_LEN_TIPS,
        blank=True,
        null=True,
    )

    # If this is a custom exercise for the given user then set it, otherwise if it comes from the server's
    # already declared exercises skip it
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    is_published = models.BooleanField(
        default=False
    )
    is_cardio = models.BooleanField(
        blank=True,
        null=True,
        default=False,
    )
    bodyweight = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name


class ExerciseSession(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE
    )
    # sets = models.ManyToManyField(Set)
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    notes = models.TextField(
        blank=True,
        null=True
    )

    history = HistoricalRecords()

    @staticmethod
    def validate_sets(data):
        required_fields = ['weight', 'reps', 'min_reps', 'max_reps', 'to_failure', 'bodyweight']
        numbers_fields = ['weight', 'reps', 'min_reps', 'max_reps']
        for set_data in data:
            if not all(field in set_data for field in required_fields):
                raise ValidationError("Each set must have values for all fields: {}".format(', '.join(required_fields)))

            for field in numbers_fields:
                try:
                    field_value = set_data[field]
                    float(field_value)
                except ValueError:
                    raise ValidationError(f"The value for {field} must be a number and must not be emtpy")

    @staticmethod
    def create_sets(request, exercise_session, sets_data):
        sets_array = []
        ExerciseSession.validate_sets(sets_data)

        for set_data in sets_data:
            set_instance = Set.objects.create(
                weight=None if set_data['bodyweight'] else set_data['weight'],
                reps=None if set_data['to_failure'] else set_data['reps'],
                min_reps=None if set_data['to_failure'] else set_data['min_reps'],
                max_reps=None if set_data['to_failure'] else set_data['max_reps'],
                to_failure=set_data['to_failure'],
                bodyweight=set_data['bodyweight'],
                created_by=request.user.profile

            )
            sets_array.append(set_instance)
            exercise_session.sets.add(set_instance)
        return sets_array

    # TODO :NEW
    @staticmethod
    def create_session(request, exercise_name: str, exercise_id: int, session_data):
        try:
            exercise = Exercise.objects.get(name=exercise_name, pk=exercise_id)
        except Exercise.DoesNotExist:
            raise ValidationError(f"There was a problem selecting the exercise - {exercise_name}")

        with transaction.atomic():
            exercise_session = ExerciseSession.objects.create(
                profile=request.user.profile,
                exercise=exercise,
            )

            for item in session_data:
                if item['type'] == 'set':
                    ExerciseSession.add_set(request, exercise_session, item['data'])
                elif item['type'] == 'rest':
                    ExerciseSession.add_rest(request, exercise_session, item['data'])
                elif item['type'] == 'intervaL':
                    ExerciseSession.add_interval(request, exercise_session, item['data'])

        return exercise_session

    @staticmethod
    def add_single_set_instance(request, exercise_session, set_data):
        current_sets = exercise_session.sets.all()
        max_set_index = current_sets.aggregate(Max('set_index'))['set_index__max']
        new_set_index = max_set_index + 1 if max_set_index is not None else 0
        try:
            is_valid = ExerciseSession.validate_sets([set_data])
        except ValidationError as e:
            raise ValidationError(e.message)
        set_instance = Set.objects.create(
            weight=set_data.get('weight', 0),
            reps=set_data.get('reps', 0),
            min_reps=set_data.get('min_reps', 0),
            max_reps=set_data.get('max_reps', 0),
            to_failure=set_data.get('to_failure', False),
            bodyweight=set_data.get('bodyweight', False),
            set_index=new_set_index,
            created_by=request.user.profile
        )

        exercise_session.sets.add(set_instance)
        return set_instance

    @staticmethod
    def edit_session(request, exercise_session, data):
        sets = data['sets']
        notes = data['notes']
        for exercise_set in sets:
            if not 'id' in exercise_set:
                ExerciseSession.add_single_set_instance(request, exercise_session, exercise_set)
            else:
                try:
                    set_instance = Set.objects.get(pk=exercise_set['id'])
                    Set.edit_data(set_instance, exercise_set)
                except Set.DoesNotExist:
                    return models.ObjectDoesNotExist
        exercise_session.notes = notes
        return exercise_session.save()

    # added later
    @staticmethod
    def add_set(request, exercise_session, set_data):
        set_instance = Set.objects.create(
            weight=float(set_data.get('weight', 0)),
            reps=int(set_data.get('reps', 0)),
            min_reps=int(set_data.get('min_reps', 0)),
            max_reps=int(set_data.get('max_reps', 0)),
            to_failure=string_to_bool(set_data.get('to_failure', False)),  # Convert string to boolean
            bodyweight=string_to_bool(set_data.get('bodyweight', False)),  # Convert string to boolean
            created_by=request.user.profile
        )
        content_type = ContentType.objects.get_for_model(set_instance)
        ExerciseSessionItem.objects.create(
            exercise_session=exercise_session,
            content_type=content_type,
            object_id=set_instance.id,
            order=ExerciseSessionItem.objects.filter(exercise_session=exercise_session).count()
        )
        return set_instance

    # added later
    @staticmethod
    def add_rest(request, exercise_session, rest_data):
        rest_instance = Rest.objects.create(
            minutes=rest_data.get('minutes', 0),
            seconds=rest_data.get('seconds', 0),
            created_by=request.user.profile
        )
        content_type = ContentType.objects.get_for_model(rest_instance)
        ExerciseSessionItem.objects.create(
            exercise_session=exercise_session,
            content_type=content_type,
            object_id=rest_instance.id,
            order=ExerciseSessionItem.objects.filter(exercise_session=exercise_session).count()
        )
        return rest_instance

    @staticmethod
    def add_interval(request, exercise_session, interval_data):
        interval_instance = Interval.objects.create(
            time=interval_data.get('time', 0),
            distance=interval_data.get('distance', 0),
            level=interval_data.get('level', 0),
            pace=interval_data.get('pace', 0),
            created_by=request.user.profile
        )
        content_type = ContentType.objects.get_for_model(interval_instance)
        ExerciseSessionItem.objects.create(
            exercise_session=exercise_session,
            content_type=content_type,
            object_id=interval_instance.id,
            order=ExerciseSessionItem.objects.filter(exercise_session=exercise_session).count()
        )
        return interval_instance


class SupersetSession(models.Model):
    exercises = models.ManyToManyField(ExerciseSession)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f"Superset Session created by {self.created_by} at {self.created_at}"


# added later
class ExerciseSessionItem(models.Model):
    exercise_session = models.ForeignKey(ExerciseSession, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']


class WorkoutSession(models.Model):
    MAX_LEN_NAME = 50
    name = models.CharField(
        max_length=MAX_LEN_NAME
    )
    total_exercises = models.IntegerField()
    total_sets = models.IntegerField()
    total_weight_volume = models.IntegerField()
    # exercises = models.ManyToManyField(ExerciseSession)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    is_published = models.BooleanField(
        default=False
    )
    exercises = models.ManyToManyField(
        'WorkoutExerciseSession',
        related_name='workout_sessions'
    )

    #
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    # object_id = models.PositiveIntegerField(null=True)
    # exercises = GenericForeignKey('content_type', 'object_id')

    @staticmethod
    def create_session(request, workout_name, exercises):
        if not workout_name:
            raise ValidationError("Provide a name for your workout")
        if len(exercises) == 0:
            raise ValidationError("Please add exercises to your workout")

        workout_session = WorkoutSession.objects.create(
            name=workout_name,
            total_exercises=len(exercises),
            # TODO: Move the total_set and total_weight volume to a signal
            total_sets=0,
            total_weight_volume=0,
            created_by=request.user.profile,

        )

        total_sets = 0
        total_weight_volume = 0

        for exercise_data in exercises:
            session_type = exercise_data['session_type']
            # if session_type == 'superset':
            #     superset_exercise_sessions = exercise_data['exercises_data']
            #     superset_session = SupersetSession.objects.create(created_by=request.user.profile)
            #     for session in superset_exercise_sessions:
            #         exercise = session['exercise']
            #         exercise_session = ExerciseSession.create_session(request, exercise['name'], exercise['id'],
            #                                                           session['session_data'])
            #         superset_session.exercises.add(exercise_session)
            #
            #         superset_session_content_type = ContentType.objects.get_for_model(SupersetSession)
            #
            #         # Set the content_type and object_id fields of the workout_session
            #         workout_session.content_type = superset_session_content_type
            #         workout_session.object_id = superset_session.id
            #
            #         # Save the workout_session
            #         workout_session.save()
            #
            #     # workout_session.exercises.add(superset_session)
            if session_type == 'superset':
                superset_exercise_sessions = exercise_data['exercises_data']
                superset_session = SupersetSession.objects.create(created_by=request.user.profile)
                for session in superset_exercise_sessions:
                    exercise = session['exercise']
                    exercise_session = ExerciseSession.create_session(request, exercise['name'], exercise['id'],
                                                                      session['session_data'])
                    superset_session.exercises.add(exercise_session)

                # Create WorkoutExercise relation for superset
                superset_content_type = ContentType.objects.get_for_model(SupersetSession)
                WorkoutExerciseSession.objects.create(
                    content_type=superset_content_type,
                    object_id=superset_session.id,
                    workout_session=workout_session
                )
            elif session_type == 'exercise':
                exercise = exercise_data['exercise']
                session_data = exercise_data['session_data']
                exercise_session = ExerciseSession.create_session(request, exercise['name'], exercise['id'],
                                                                  session_data)
                # Create WorkoutExercise relation for exercise
                exercise_content_type = ContentType.objects.get_for_model(ExerciseSession)
                WorkoutExerciseSession.objects.create(
                    content_type=exercise_content_type,
                    object_id=exercise_session.id,
                    workout_session=workout_session
                )
            # elif session_type == 'exercise':
            #     exercise = exercise_data['exercise']
            #     session_data = exercise_data['session_data']
            #     exercise_session = ExerciseSession.create_session(request, exercise['name'], exercise['id'],
            #                                                       session_data)
            #     print(workout_session.exercises)
            #     workout_session.exercises.add(exercise_session)

            # Calculate total sets and total weight volume for the workout session
            # for session_item in session_data:
            #     if session_item['type'] == 'set':
            #         total_sets += 1
            #         total_weight_volume += float(session_item['data'].get('weight', 0)) * int(
            #             session_item['data'].get('reps', 0))

        # workout_session.total_sets = total_sets
        # workout_session.total_weight_volume = total_weight_volume
        # workout_session.save()

        return workout_session

    @staticmethod
    def publish_workout(request, workout_id):
        user = request.user
        try:
            workout = WorkoutSession.objects.get(id=workout_id)
            if workout.created_by != user.profile:
                raise PermissionDenied("You do not have permission to publish this workout.")
            workout.is_published = True
            workout.save()
            return workout
        except WorkoutSession.DoesNotExist:
            raise IntegrityError("Workout does not exist.")

    @staticmethod
    def edit_session(request, workout_session, new_data):
        workout_name = new_data.get('name')
        exercises = new_data.get('exercises')
        workout_session_exercises_instances = workout_session.exercises.all()

        # Getting all the ids for the exercises send by the request
        new_exercise_ids = [exercise_session.get('id') for exercise_session in exercises]

        for existing_exercise in workout_session_exercises_instances:
            # checking if the exercise is in the session if not deleting!
            if existing_exercise.pk not in new_exercise_ids:
                workout_session.exercises.remove(existing_exercise)
                existing_exercise.delete()

        # looping the exercises
        for exercise_session in exercises:
            # try, catch to get the exercise_instance
            try:
                exercise_instance = ExerciseSession.objects.get(pk=exercise_session.get('id'))
                # if instance, sending it to the model's method to edit it
                ExerciseSession.edit_session(request, exercise_instance, exercise_session)
            except ExerciseSession.DoesNotExist:
                # if not instance that means the exercise is added to the workout now!
                exercise = exercise_session['exercise']
                sets = exercise_session['sets']
                exercise_instance = ExerciseSession.create_session(request, exercise['name'], sets)
                exercise_instance.save()
                workout_session.exercises.add(exercise_instance)

        workout_session.name = workout_name
        workout_session.save()
        return workout_session


class WorkoutExerciseSession(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    workout_session = models.ForeignKey(WorkoutSession, related_name='workout_exercises', on_delete=models.CASCADE)


class WorkoutPlan(models.Model):
    MAX_LEN_NAME = 100
    name = models.CharField(
        max_length=MAX_LEN_NAME
    )
    total_workouts = models.IntegerField()
    workouts = models.ManyToManyField(WorkoutSession)
    created_by = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    @staticmethod
    def create_routine(request, routine_data):
        try:
            with transaction.atomic():
                name = routine_data['name']
                workouts = routine_data['workouts']
                total_workouts = len(workouts)

                # Plan name validation
                if not name:
                    raise ValidationError(message="Provide a name for your workout plan")

                workout_plan = WorkoutPlan.objects.create(
                    name=name,
                    total_workouts=total_workouts,
                    created_by=request.user.profile
                )

                for workout_data in routine_data['workouts']:
                    workout_name = workout_data['name']
                    exercises_data = workout_data['exercises']
                    # Creating the instance
                    workout_session = WorkoutSession.create_session(request=request, workout_name=workout_name,
                                                                    exercises=exercises_data)
                    # adding the instance to the workout plan instance
                    workout_plan.workouts.add(workout_session)

                # #     calculating the total_sets
                # workout_plan.total_sets = workout_plan.workouts.aggregate(total_sets=models.Sum('total_sets'))[
                #     'total_sets']
                # # calculating the total weight volume
                # total_weight_volume_aggregate = workout_session.exercises.aggregate(
                #     total_weight_volume=models.Sum(models.F('sets__weight') * models.F('sets__reps'),
                #                                    output_field=models.FloatField())
                # )
                # workout_session.total_weight_volume = total_weight_volume_aggregate['total_weight_volume'] or 0
                workout_plan.save()

                return workout_plan

        except Exception as e:
            # Handle the exception or log it
            raise e


class ActiveRoutine(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE
    )
    workout_plan = models.OneToOneField(
        WorkoutPlan,
        primary_key=True,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Active routine for {self.profile} created at {self.created_at}"

from celery import shared_task

from server.cloudinary import upload_to_cloudinary
from server.workouts.models import Exercise
import base64
from django.core.files.base import ContentFile


@shared_task
def upload_exercise_video_to_cloudinary(encoded_video, exercise_id):
    exercise = Exercise.objects.get(pk=exercise_id)
    video_data = base64.b64decode(encoded_video)
    video_file = ContentFile(video_data, name='exercise_video_tutorial.mp4')
    uploaded_video = upload_to_cloudinary(video_file)
    exercise.video_tutorial = uploaded_video
    exercise.save()

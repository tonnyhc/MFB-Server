from celery import shared_task
import base64
from cloudinary import uploader
from django.core.files.base import ContentFile

from server.cloudinary import upload_to_cloudinary
from server.profiles.models import Profile


@shared_task
def upload_profile_picture_to_cloudinary_and_save_to_profile(encoded_picture, profile_id):
    profile = Profile.objects.get(pk=profile_id)
    image_data = base64.b64decode(encoded_picture)
    image_file = ContentFile(image_data, name='profile_picture.jpg')
    uploaded_image = upload_to_cloudinary(image_file)
    print(uploaded_image)
    if profile.picture:
        public_id = profile.picture.public_id
        uploader.destroy(public_id)
        profile.picture = None
        profile.save()
    profile.picture = uploaded_image
    profile.save()
    # return Response(status=status.HTTP_204_NO_CONTENT)

    # try:
    #     # Upload the image to Cloudinary
    #     public_id = upload_to_cloudinary(image_url)
    #
    #     # Update the profile with the Cloudinary public ID
    #     profile = Profile.objects.get(pk=profile_id)
    #     profile.picture = public_id
    #     profile.save()
    # except Profile.DoesNotExist:
    #     # Handle the case where the profile object is not found
    #     # Log the error or take appropriate action
    #     pass

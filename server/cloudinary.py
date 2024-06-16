from cloudinary.uploader import upload


def upload_to_cloudinary(image_url):
    # Upload the image to Cloudinary
    response = upload(image_url)

    # Extract and return the public ID of the uploaded image
    public_id = response['public_id']
    return public_id

import cloudinary, cloudinary.uploader
from src.conf.config import settings


# Configure Cloudinary globally
cloudinary.config(
    cloud_name=settings.CLOUDINARY_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

async def upload_avatar(fileobj, public_id: str):
    
    """
    Upload an avatar image to Cloudinary.

    - Stores file in the ``avatars/`` folder.
    - Overwrites existing file if the same ``public_id`` is used.
    - Returns the secure HTTPS URL to the uploaded image.

    :param fileobj: File-like object (e.g. ``UploadFile.file`` from FastAPI).
    :type fileobj: BinaryIO | SpooledTemporaryFile
    :param public_id: Unique identifier for the file in Cloudinary.
                      Example: ``"ContactsAPI/username"``.
    :type public_id: str
    :return: Secure URL of the uploaded image.
    :rtype: str

    Example::

        url = await upload_avatar(file.file, public_id="ContactsAPI/john_doe")
        print(url)  
        # https://res.cloudinary.com/demo/image/upload/v1234567890/avatars/ContactsAPI/john_doe.png
    """    

    res = cloudinary.uploader.upload(fileobj, public_id=public_id, folder="avatars", overwrite=True)
    return res["secure_url"]

from fastapi import UploadFile, HTTPException, status

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


async def validate_file_size(file: UploadFile):
    """
    Validate uploaded file size (max 2 MB).

    - Reads the file in 1 MB chunks.
    - If size exceeds limit → raises HTTP 413.
    - After validation resets file pointer so it can be reused.

    :param file: Uploaded file to validate.
    :type file: UploadFile
    :raises HTTPException: 413 if file exceeds limit.
    """
    size = 0
    chunk = await file.read(1024 * 1024)  # read in 1MB chunks
    while chunk:
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max allowed size is {MAX_FILE_SIZE // (1024 * 1024)}MB",
            )
        chunk = await file.read(1024 * 1024)

    # reset file pointer for next usage (e.g. Cloudinary uploader)
    await file.seek(0)

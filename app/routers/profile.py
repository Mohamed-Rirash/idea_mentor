from fastapi import APIRouter, File, UploadFile, HTTPException, status, Response
from app.models import ImageModel
from app.schemas import ImageSchema
from app.database_dependency import db_dependency
from app.routers.auth import user_dependency

router = APIRouter(
    prefix="/profile",
    tags=["profile"]
)

@router.post("/upload/",  summary="Upload user profile image")
async def upload_image(db: db_dependency, user: user_dependency, file: UploadFile = File(...)):
    """
    Upload a profile image for the user.
    The user must be authenticated.
    Only image files are accepted.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid file type")

    try:
        img = ImageModel(
            name=file.filename,
            mimetype=file.content_type,
            image_data=await file.read(),
            user_id=user.get('id')
        )
        db.add(img)
        db.commit()
        db.refresh(img)
        return Response(content=img.image_data, media_type=img.mimetype)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.get("/get_profile", summary="Retrieve user profile image")
async def get_image(user: user_dependency, db: db_dependency):
    """
    Retrieve the profile image of the authenticated user.
    Returns the image file if found.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    image = db.query(ImageModel).filter(ImageModel.user_id == user.get('id')).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(content=image.image_data, media_type=image.mimetype)

@router.put("/update", summary="Update user profile image")
async def change_profile(user: user_dependency, db: db_dependency, file: UploadFile = File(...)):
    """
    Update the profile image of the authenticated user.
    The existing image will be replaced with the new one.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    db_image = db.query(ImageModel).filter(ImageModel.user_id == user.get("id")).first()
    if not db_image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        db_image.name = file.filename
        db_image.mimetype = file.content_type
        db_image.image_data = await file.read()
        db.commit()
        return {"message": "Image updated successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

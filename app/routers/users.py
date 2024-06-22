from fastapi import APIRouter, HTTPException, status, Path
from app.database_dependency import db_dependency
from app.routers.auth import user_dependency, bcrypt_context
from app import schemas, models
from typing import List

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/user_info", response_model=schemas.UserResponse, summary="Get user information")
async def get_user_info(db: db_dependency, user: user_dependency):
    """
    Retrieve the information of the authenticated user.
    Returns the user information as a UserResponse object.
    Raises HTTPException for unauthorized access.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    user_model = db.query(models.User).filter(models.User.id == user.get('id')).first()
    return user_model

@router.put('/change_password', status_code=status.HTTP_200_OK, summary="Change user password")
async def change_password(db: db_dependency, user: user_dependency, user_verify: schemas.UsersVerification):
    """
    Allows the user to change their password.
    Requires the current and new password.
    Raises HTTPException for invalid current password or unauthorized access.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    user_model = db.query(models.User).filter(models.User.id == user.get('id')).first()
    if not bcrypt_context.verify(user_verify.password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid current password")
    user_model.hashed_password = bcrypt_context.hash(user_verify.new_password)
    db.add(user_model)
    db.commit()
    return {"message": "Password changed successfully"}

@router.delete("/delete_account", summary="Delete user account")
async def delete_account(db: db_dependency, user: user_dependency):
    """
    Delete the authenticated user's account and all related data (projects, todos, resources, profile picture).
    Raises HTTPException for unauthorized access.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    # Deleting associated resources, todos, and projects
    db.query(models.Resource).join(models.Todo).join(models.Project).filter(models.Project.user_id == user.get('id')).delete(synchronize_session=False)
    db.query(models.Todo).join(models.Project).filter(models.Project.user_id == user.get('id')).delete(synchronize_session=False)
    db.query(models.Project).filter(models.Project.user_id == user.get('id')).delete(synchronize_session=False)

    # Delete profile picture and user account
    db.query(models.ImageModel).filter(models.ImageModel.user_id == user.get('id')).delete(synchronize_session=False)
    db.query(models.User).filter(models.User.id == user.get('id')).delete(synchronize_session=False)

    db.commit()
    return {"message": "User account and all related data deleted successfully"}


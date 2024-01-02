from fastapi import APIRouter, Path, HTTPException, status
from app import schemas, models
from app.database_dependency import db_dependency
from app.routers.auth import user_dependency
from typing import List

router = APIRouter(
    prefix="/resource",
    tags=["resource"]
)

@router.get('/allresources',
            status_code=status.HTTP_200_OK,
            response_model=List[schemas.ResourceResponse],
            summary="Get all resources associated with the user's projects")
async def get_all_resource(db: db_dependency, user: user_dependency):
    """
    Retrieve all resources related to the projects of the authenticated user.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")
    
    resource_models = db.query(models.Resource)\
                        .join(models.Todo, models.Resource.todo_id == models.Todo.id)\
                        .join(models.Project, models.Todo.project_id == models.Project.id)\
                        .filter(models.Project.user_id == user.get('id'))\
                        .all()

    if not resource_models:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resources found for this user")
    
    return resource_models

@router.get('/todos_resources/{todo_id}',
            status_code=status.HTTP_200_OK,
            response_model=List[schemas.ResourceResponse],
            summary="Get resources for a specific todo")
async def get_project_todos(
    db: db_dependency,
    user: user_dependency,
    todo_id: int = Path(..., gt=0, description="ID of the todo that owns this resource")
):
    """
    Retrieve resources associated with a specific todo, which belongs to the authenticated user.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")

    todo = db.query(models.Todo).join(models.Project).filter(
        models.Todo.id == todo_id, 
        models.Project.user_id == user.get('id')
    ).first()

    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    resources = db.query(models.Resource).filter(
        models.Resource.todo_id == todo_id
    ).all()

    if not resources:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No resources found")

    return resources

@router.post('/new_resource/{todo_id}',
             status_code=status.HTTP_201_CREATED,
             summary="Add a new resource to a todo")
async def add_resource(db: db_dependency,
                       user: user_dependency,
                       resource_request: schemas.ResourceRequest,
                       todo_id: int = Path(..., gt=0, description="ID of the todo to which this resource belongs")):
    """
    Create a new resource and associate it with a specified todo.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")
    
    todo_model = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if not todo_model or todo_model.project.user_id != user.get('id'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found or unauthorized access")

    resource_model = models.Resource(**resource_request.dict(), todo_id=todo_id)
    db.add(resource_model)
    db.commit()
    return {"message": "Resource added successfully"}

@router.put('/update_resource/{resource_id}',
            status_code=status.HTTP_200_OK,
            summary="Update a specific resource")
async def update_resource(
    db: db_dependency,
    user: user_dependency,
    resource_request: schemas.ResourceRequest, 
    resource_id: int = Path(..., gt=0, description="ID of the resource to update")
):
    """
    Update an existing resource. Only the owner of the resource can update it.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    resource_model = db.query(models.Resource)\
        .join(models.Todo, models.Todo.id == models.Resource.todo_id)\
        .join(models.Project, models.Project.id == models.Todo.project_id)\
        .filter(models.Resource.id == resource_id, models.Project.user_id == user.get('id'))\
        .first()

    if resource_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    resource_model.update(resource_request.dict())
    db.commit()
    return {"message": f"Resource with ID {resource_id} updated successfully"}

@router.delete('/delete_resource/{resource_id}',
               status_code=status.HTTP_200_OK,
               summary="Delete a specific resource")
async def delete_resource(
    db: db_dependency,
    user: user_dependency,
    resource_id: int = Path(..., gt=0, description="ID of the resource to delete")
):
    """
    Delete a specific resource. Only the owner of the resource can delete it.
    """
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")

    resource_model = db.query(models.Resource)\
        .join(models.Todo, models.Todo.id == models.Resource.todo_id)\
        .join(models.Project, models.Project.id == models.Todo.project_id)\
        .filter(models.Resource.id == resource_id, models.Project.user_id == user.get('id'))\
        .first()

    if resource_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    db.delete(resource_model)
    db.commit()
    return {"message": f"Resource with ID {resource_id} deleted successfully"}

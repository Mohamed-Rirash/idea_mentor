from fastapi import APIRouter, HTTPException, status, Path
from app.database_dependency import db_dependency
from app import schemas, models
from app.routers.auth import user_dependency
from typing import List

router = APIRouter(
    prefix="/project",
    tags=["projects"]
)

@router.get("/getallprojects", response_model=List[schemas.ProjectResponse], summary="Get all projects of a user")
async def get_all_projects(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    all_projects = db.query(models.Project).filter(models.Project.user_id == user.get('id')).all()
    return all_projects

@router.get("/get_project/{project_id}/", response_model=schemas.ProjectResponse, summary="Get a project by its ID")
async def read_project_by_id(user: user_dependency, db: db_dependency, project_id: int = Path(..., gt=0, description="ID of the project")):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    project_model = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == user.get('id')).first()
    if project_model is not None:
        return project_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

@router.post("/new", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED, summary="Create a new project")
async def create_new_project(db: db_dependency, user: user_dependency, project_request: schemas.ProjectRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    project_model = models.Project(**project_request.dict(), user_id=user.get('id'))
    db.add(project_model)
    db.commit()
    return project_model

@router.put('/update/{project_id}', response_model=schemas.ProjectResponse, status_code=status.HTTP_200_OK, summary="Update an existing project")
async def update_project(db: db_dependency, user: user_dependency, project_request: schemas.ProjectRequest, project_id: int = Path(..., gt=0, description="ID of the project")):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    project_model = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == user.get('id')).first()
    if project_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    project_model.title = project_request.title
    project_model.description = project_request.brief_description
    project_model.priority = project_request.detailed_description
    db.add(project_model)
    db.commit()
    return project_model

@router.delete('/delete/{project_id}', summary="Delete a project and its related entities")
async def delete_project(db: db_dependency, user: user_dependency, project_id: int = Path(..., gt=0, description="ID of the project")):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    project_model = db.query(models.Project).filter(models.Project.id == project_id, models.Project.user_id == user.get('id')).first()
    if project_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # Deleting todos and resources should be handled transactionally
    with db.begin():
        db.query(models.Resource).filter(models.Resource.todo_id.in_(
            db.query(models.Todo.id).filter(models.Todo.project_id == project_id)
        )).delete(synchronize_session=False)
        db.query(models.Todo).filter(models.Todo.project_id == project_id).delete(synchronize_session=False)
        db.delete(project_model)
    return {"message": f"Project {project_id} and all related todos and resources deleted successfully"}

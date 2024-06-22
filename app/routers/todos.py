from fastapi import APIRouter, Path, HTTPException, status
from app import schemas, models
from app.database_dependency import db_dependency
from app.routers.auth import user_dependency
from typing import List

router = APIRouter(
    prefix="/todos",
    tags=["Todos"]
)

@router.get('/alltodos', 
            status_code=status.HTTP_200_OK, 
            response_model=List[schemas.TodoResponse], 
            summary="Get all todos for the user")
async def get_all_todos(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")

    todo_models = db.query(models.Todo)\
                    .join(models.Project, models.Project.id == models.Todo.project_id)\
                    .filter(models.Project.user_id == user.get('id'))\
                    .all()

    return todo_models

@router.get('/all_project_todo/{project_id_para}',
            status_code=status.HTTP_200_OK,
            response_model=List[schemas.TodoResponse],
            summary="Get all todos for a specific project")
async def get_project_todos(db: db_dependency,
                            user: user_dependency,
                            project_id_para: int = Path(...,gt=0,description="ID of the project that owns these todos")):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")

    project = db.query(models.Project).filter(models.Project.id == project_id_para, models.Project.user_id == user.get('id')).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    todo_models = db.query(models.Todo).filter(models.Todo.project_id == project_id_para).all()
    return todo_models

@router.post("/new_todo/{project_id_para}",
             status_code=status.HTTP_201_CREATED,
             summary="Create a new todo in a project")
async def create_new_todo(db: db_dependency, 
                          user: user_dependency,
                          todo_request: schemas.TodoRequest, 
                          project_id_para: int = Path(..., gt=0, description="ID of the project to create this todo in")):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")

    project = db.query(models.Project).filter(models.Project.id == project_id_para, models.Project.user_id == user.get('id')).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    todo_model = models.Todo(**todo_request.dict(), project_id=project_id_para)
    db.add(todo_model)
    db.commit()
    return {"message": "Todo added successfully"}

@router.put('/update/{todo_id}',
            status_code=status.HTTP_200_OK,
            summary="Update a specific todo")
async def update_todo(db: db_dependency,
                      user: user_dependency,
                      todo_request: schemas.TodoRequest,
                      todo_id: int = Path(..., gt=0, description="ID of the todo to update")):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")

    todo_model = db.query(models.Todo).join(models.Project).filter(models.Todo.id == todo_id, models.Project.user_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    todo_model.task_title = todo_request.task_title
    todo_model.task_description = todo_request.task_description
    todo_model.completed = todo_request.completed

    db.add(todo_model)
    db.commit()
    return {"message": f"Todo {todo_id} updated successfully"}

@router.delete('/delete/{todo_id}',
               status_code=status.HTTP_200_OK,
               summary="Delete a specific todo")
async def delete_todo(db: db_dependency,
                      user: user_dependency,
                      todo_id: int = Path(..., gt=0, description="ID of the todo to delete")):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")

    todo_model = db.query(models.Todo).join(models.Project).filter(models.Todo.id == todo_id, models.Project.user_id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    db.delete(todo_model)
    db.commit()
    return {"message": f"Todo with ID {todo_id} deleted successfully"}

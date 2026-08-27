from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, HTTPException,Depends, status
from sqlalchemy import select
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload #for eagerloading
from app.models import model as models
from app.database import Base, engine, get_db
from app.schemas import UserCreate, UserResponse,UpdateUser,PostResponse

router = APIRouter()


## Create User
@router.post("",response_model=PostResponse,status_code=status.HTTP_201_CREATED,)
async def create_user(user: UserCreate,db:Annotated[AsyncSession,Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.username==user.username))
    existingUser=result.scalars().first();

    if(existingUser):
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username Already Exists")

    resultEmail=await db.execute(select(models.User).where(models.User.email==user.email))
    existingEmail=resultEmail.scalars().first();

    if(existingEmail):
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email Already Exists")

    newUser=models.User(username=user.username,email=user.email)
    db.add(newUser)
    await db.commit()
    await db.refresh(newUser)
    return newUser

#get user by id
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id),)

    user = result.scalars().first()

    if user:
        return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)


#get all post by users 
# @app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
# def get_user_posts(user_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = db.execute(select(models.User).where(models.User.id == user_id))

#     user = result.scalars().first()

#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

#     result = db.execute(select(models.Post).where(models.Post.user_id == user_id))

#     posts = result.scalars().all()

#     return posts
@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_posts(user_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
    print("Endpoint called")
    result = await db.execute(select(models.User).where(models.User.id == user_id))

    user = result.scalars().first()
    print("User called")

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    print("post called")

    return posts



##userdate partial users
@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int,user_update: UpdateUser,db: Annotated[AsyncSession, Depends(get_db)],):
    result =await  db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

    if (user_update.username is not None and user_update.username != user.username):
        result = await db.execute(select(models.User).where(models.User.username == user_update.username),)
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username already exists",)

    if (user_update.email is not None and user_update.email != user.email):
        result = await db.execute(select(models.User).where(models.User.email == user_update.email),)
        existing_email = result.scalars().first()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email already registered",)

    if user_update.username is not None:
        user.username = user_update.username

    if user_update.email is not None:
        user.email = user_update.email

    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)

    return user

##Delete user by usrid , when user delete its all post also deleted 
## delete_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)
    await db.delete(user)
    await db.commit()


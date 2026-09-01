from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, HTTPException,Depends, status
from sqlalchemy import select
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload #for eagerloading
from app.models import model as models
from app.database import Base, engine, get_db
from app.schemas import PostCreate,PostUpdate,PostResponse

router = APIRouter()


## Get all posts
# @app.get("/api/posts", response_model=list[PostResponse])
# def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
#     result = db.execute(select(models.Post))
#     posts = result.scalars().all()
#     return posts
@router.get("", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result =await  db.execute(select(models.Post).options(selectinload(models.Post.author)))
    posts = result.scalars().all()
    return posts

## Get  posts by post id
#data validation and Error Handling
# @app.get("/api/posts/{post_id}", response_model=PostResponse)
# def get_post(post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = db.execute(select(models.Post).where(models.Post.id == post_id))

#     post = result.scalars().first()

#     if post:
#         return post
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)
@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

    post = result.scalars().first()

    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)


## Update  posts by post id
# @app.put("/api/posts/{post_id}", response_model=PostResponse)
# def update_post_full(post_id: int,post_data:PostCreate,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = db.execute(select(models.Post).where(models.Post.id == post_id))

#     post = result.scalars().first()

#     if not post:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

#     if post_data.user_id != post.user_id:
#         result2 = db.execute(select(models.User).where(models.User.id == post_data.user_id))
#         existing_user = result2.scalars().first()
#         if not existing_user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

    
#     post.title=post_data.title
#     post.content=post_data.content
#     post.user_id=post_data.user_id
    
#     db.commit()
#     db.refresh(post)
#     return post
@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(post_id: int,post_data:PostCreate,db: Annotated[AsyncSession, Depends(get_db)],):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

    if post_data.user_id != post.user_id:
        result2 = await db.execute(select(models.User).where(models.User.id == post_data.user_id))
        existing_user = result2.scalars().first()
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)
    
    post.title=post_data.title
    post.content=post_data.content
    post.user_id=post_data.user_id
    
    await db.commit()
    await db.refresh(post,attribute_names=["author"])
     #each post need to load the author
    return post


## Partial Update using Patch
# @app.patch("/api/post/{post_id}", response_model=PostUpdate)
# def update_post_partial(post_id: int,post_data:PostUpdate,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = db.execute(select(models.Post).where(models.Post.id == post_id))

#     post = result.scalars().first()

#     if not post:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

#     # if post_data.title :
#     #     post.title=post_data.title
#     # if  post_data.content:
#     #     post.content=post_data.content
#     update_data = post_data.model_dump(exclude_unset=True)
#     #Note:exclude_unset=True includes only fields provided in the request.
#     #setattr() updates those fields dynamically.
#     for key, value in update_data.items():
#         setattr(post, key, value)    
#     db.commit()
#     db.refresh(post)
#     return post
@router.patch("/{post_id}", response_model=PostUpdate)
async def update_post_partial(post_id: int,post_data:PostUpdate,db: Annotated[AsyncSession, Depends(get_db)],):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

    # if post_data.title :
    #     post.title=post_data.title
    # if  post_data.content:
    #     post.content=post_data.content
    update_data = post_data.model_dump(exclude_unset=True)
    #Note:exclude_unset=True includes only fields provided in the request.
    #setattr() updates those fields dynamically.
    for key, value in update_data.items():
        setattr(post, key, value)    
    await db.commit()
    await db.refresh(post,attribute_names=["author"])
    return post


## Delete Post
# @app.delete("/api/post/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_post(post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = db.execute(select(models.Post).where(models.Post.id == post_id))

#     post = result.scalars().first()

#     if not post:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

#     db.delete(post)
#     db.commit()
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

    post = result.scalars().first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

    await db.delete(post)
    await db.commit()



## Create Post
@router.post("",response_model=PostResponse,status_code=status.HTTP_201_CREATED,)
async def create_post(post: PostCreate,db: Annotated[AsyncSession, Depends(get_db)],):
    result = await db.execute(select(models.User).where(models.User.id == post.user_id))

    existing_user = result.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

    new_post = models.Post(title=post.title,content=post.content,user_id=post.user_id,)

    db.add(new_post)
    await db.commit()
    await db.refresh(new_post,attribute_names=["author"])
    #each post need there author loaded
    return new_post


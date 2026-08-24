from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, HTTPException,Depends, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.schemas import PostCreate,PostResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
import models.model as models
from database import Base, engine, get_db
from schemas import PostCreate, PostResponse,UserCreate, UserResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)
app.mount(
    "/media",
    StaticFiles(directory=BASE_DIR / "media"),
    name="media"
)


templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# posts: list[dict] = [
#     {
#         "id": 1,
#         "author": "Surendra Sahani",
#         "title": "FastAPI is Awesome",
#         "content": "This framework is really easy to use and super fast.",
#         "date_posted": "April 20, 2025",
#     },
#     {
#         "id": 2,
#         "author": "Ram Sahani",
#         "title": "Python is Great for Web Development",
#         "content": "Python is a great language for web development, and FastAPI makes it even better.",
#         "date_posted": "April 21, 2025",
#     },
# ]

#home page
@app.get("/", include_in_schema=False,name="home")
@app.get("/posts", include_in_schema=False,name="posts")
def home(request: Request,db: Annotated[Session, Depends(get_db)]):
    result=db.execute(models.Post)
    posts=result.scalar().all()
    return templates.TemplateResponse(request,"home.html",
        {
            "posts": posts,
            "title": "Home",
        },
    )

## Single Post Page
@app.get("/posts/{post_id}", include_in_schema=False)
def post_page( request: Request,post_id: int,db: Annotated[Session, Depends(get_db)],):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))

    post = result.scalars().first()

    if post:
        title = post.title[:50]

        return templates.TemplateResponse(
            "post.html",
            {
                "request": request,
                "post": post,
                "title": title,
            },
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

## Get all posts
@app.get("/api/posts", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts

## Get  posts by post id
#data validation and Error Handling
@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int,db: Annotated[Session, Depends(get_db)],):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))

    post = result.scalars().first()

    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)


## Create Post
@app.post("/api/posts",response_model=PostResponse,status_code=status.HTTP_201_CREATED,)
def create_post(post: PostCreate,db: Annotated[Session, Depends(get_db)],):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))

    existing_user = result.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post



## Create User

@app.post(
    "/api/users",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(user: UserCreate,db:Annotated[Session,Depends(get_db)]):
    result=db.execute(select(models.User).where(models.User.username==user.username))
    existingUser=result.scalars().first();

    if(existingUser):
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username Already Exists")

    resultEmail=db.execute(select(models.User).where(models.User.email==user.email))
    existingEmail=resultEmail.scalars().first();

    if(existingEmail):
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email Already Exists")

    newUser=models.User(
            username=user.username,
            email=user.email
    )
    db.add(newUser)
    db.commit()
    db.refresh(newUser)
    return newUser

#get user by id
@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.id == user_id),
    )

    user = result.scalars().first()

    if user:
        return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


#get all post by users 
@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
def get_user_posts(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(
        select(models.User).where(models.User.id == user_id)
    )

    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = db.execute(
        select(models.Post).where(models.Post.user_id == user_id)
    )

    posts = result.scalars().all()

    return posts


## StarletteHTTPException Handler
@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(
    request: Request,
    exception: StarletteHTTPException
):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )

### RequestValidationError Handler
@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request,
    exception: RequestValidationError
):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
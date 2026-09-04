from pathlib import Path
from contextlib import asynccontextmanager
from fastapi.exception_handlers import (http_exception_handler,request_validation_exception_handler,)
from typing import Annotated
from fastapi import FastAPI, HTTPException,Depends, Request, status
from fastapi.exceptions import RequestValidationError
# from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import select,func
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload #for eagerloading
from app.models import model as models
from app.database import Base, engine, get_db
# from app.schemas import PostCreate, PostResponse,UserCreate, UserResponse,PostUpdate,UpdateUser
from app.routers import users,posts #from routers folder import users.py and posts.py
#create_all is synchronous we can call syncronous method with asyncengine
#Base.metadata.create_all(bind=engine)

from app.config import settings

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        #create db table it is idempotent
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown
    await engine.dispose()
#Note:
#in synchrounous sqlalchemy lazy loading just works in posts dont need to load post.author so select is used
#but in asynchrounous sqlalchemy lazy loading not works so in posts  need to load post.author so selectload is used

app = FastAPI(lifespan=lifespan)

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

# Register users routes
app.include_router(users.router, prefix="/api/users", tags=["users"])
# Register posts routes
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])

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
# @app.get("/", include_in_schema=False,name="home")
# @app.get("/posts", include_in_schema=False,name="posts")
# def home(request: Request,db: Annotated[AsyncSession, Depends(get_db)]):
#     result=db.execute(select(models.Post))
#     posts=result.scalars().all()
#     return templates.TemplateResponse(request,"home.html",
#         {
#             "posts": posts,
#             "title": "Home",
#         },
#     )

#Non pahinated
# @app.get("/", include_in_schema=False,name="home")
# @app.get("/posts", include_in_schema=False,name="posts")
# async def home(request: Request,db: Annotated[AsyncSession, Depends(get_db)]):
#     result= await db.execute(select(models.Post).options(selectinload(models.Post.author))
#                              .order_by(models.Post.date_posted.desc())
#                              )
#     posts=result.scalars().all()
#     return templates.TemplateResponse(request,"home.html",
#         {
#             "posts": posts,
#             "title": "Home",
#         },
#     )

#Paginated Home Page
## home route - paginated

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    count_result = await db.execute(
        select(func.count()).select_from(models.Post)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc())
        .limit(settings.posts_per_page),
    )

    posts = result.scalars().all()

    has_more = len(posts) < total

    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "posts": posts,
            "title": "Home",
            "limit": settings.posts_per_page,
            "has_more": has_more,
        },
    )

## Single Post Page
# @app.get("/posts/{post_id}", include_in_schema=False ,name="post_page")
# def post_page( request: Request,post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = db.execute(select(models.Post).where(models.Post.id == post_id))

#     post = result.scalars().first()

#     if post:
#         title = post.title[:50]

        
#         return templates.TemplateResponse(
#     request=request,
#     name="post.html",
#     context={
#         "post": post,
#         "title": title,
#     },
# )
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)
@app.get("/posts/{post_id}", include_in_schema=False ,name="post_page")
async def post_page( request: Request,post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

    post = result.scalars().first()

    if post:
        title = post.title[:50]

        
        return templates.TemplateResponse(
    request=request,
    name="post.html",
    context={
        "post": post,
        "title": title,
    },
)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)


# @app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
# def user_posts(request: Request,user_id: int,db: Annotated[AsyncSession, Depends(get_db)],):

#     result = db.execute(select(models.User).where(models.User.id == user_id))
#     user = result.scalars().first()

#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

#     result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
#     posts = result.scalars().all()

#     return templates.TemplateResponse(
#     request=request,
#     name="user_posts.html",
#     context={
#         "user": user,
#         "posts": posts,
#         "title": f"{user.username}'s Posts",
#     },)


#Non Paginated
# @app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
# async def user_posts(request: Request,user_id: int,db: Annotated[AsyncSession, Depends(get_db)],):

#     result =await db.execute(select(models.User).where(models.User.id == user_id))
#     user = result.scalars().first()

#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

#     result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
#     posts = result.scalars().all()

#     return templates.TemplateResponse(
#     request=request,
#     name="user_posts.html",
#     context={
#         "user": user,
#         "posts": posts,
#         "title": f"{user.username}'s Posts",
#     },)



#Paginated Users Post By UserId
## user_posts_page route - paginated
@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    count_result = await db.execute(
        select(func.count())
        .select_from(models.Post)
        .where(models.Post.user_id == user_id),
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
        .limit(settings.posts_per_page),
    )
    posts = result.scalars().all()

    has_more = len(posts) < total

    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {
            "posts": posts,
            "user": user,
            "title": f"{user.username}'s Posts",
            "limit": settings.posts_per_page,
            "has_more": has_more,
        },
    )



# ## Get all posts
# # @app.get("/api/posts", response_model=list[PostResponse])
# # def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
# #     result = db.execute(select(models.Post))
# #     posts = result.scalars().all()
# #     return posts
# @app.get("/api/posts", response_model=list[PostResponse])
# async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
#     result =await  db.execute(select(models.Post).options(selectinload(models.Post.author)))
#     posts = result.scalars().all()
#     return posts

# ## Get  posts by post id
# #data validation and Error Handling
# # @app.get("/api/posts/{post_id}", response_model=PostResponse)
# # def get_post(post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
# #     result = db.execute(select(models.Post).where(models.Post.id == post_id))

# #     post = result.scalars().first()

# #     if post:
# #         return post
# #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)
# @app.get("/api/posts/{post_id}", response_model=PostResponse)
# async def get_post(post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

#     post = result.scalars().first()

#     if post:
#         return post
#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)


# ## Update  posts by post id
# # @app.put("/api/posts/{post_id}", response_model=PostResponse)
# # def update_post_full(post_id: int,post_data:PostCreate,db: Annotated[AsyncSession, Depends(get_db)],):
# #     result = db.execute(select(models.Post).where(models.Post.id == post_id))

# #     post = result.scalars().first()

# #     if not post:
# #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

# #     if post_data.user_id != post.user_id:
# #         result2 = db.execute(select(models.User).where(models.User.id == post_data.user_id))
# #         existing_user = result2.scalars().first()
# #         if not existing_user:
# #             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

    
# #     post.title=post_data.title
# #     post.content=post_data.content
# #     post.user_id=post_data.user_id
    
# #     db.commit()
# #     db.refresh(post)
# #     return post
# @app.put("/api/posts/{post_id}", response_model=PostResponse)
# async def update_post_full(post_id: int,post_data:PostCreate,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

#     post = result.scalars().first()

#     if not post:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

#     if post_data.user_id != post.user_id:
#         result2 = await db.execute(select(models.User).where(models.User.id == post_data.user_id))
#         existing_user = result2.scalars().first()
#         if not existing_user:
#             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)
    
#     post.title=post_data.title
#     post.content=post_data.content
#     post.user_id=post_data.user_id
    
#     await db.commit()
#     await db.refresh(post,attribute_names=["author"]) #each post need to load the author
#     return post


# ## Partial Update using Patch
# # @app.patch("/api/post/{post_id}", response_model=PostUpdate)
# # def update_post_partial(post_id: int,post_data:PostUpdate,db: Annotated[AsyncSession, Depends(get_db)],):
# #     result = db.execute(select(models.Post).where(models.Post.id == post_id))

# #     post = result.scalars().first()

# #     if not post:
# #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

# #     # if post_data.title :
# #     #     post.title=post_data.title
# #     # if  post_data.content:
# #     #     post.content=post_data.content
# #     update_data = post_data.model_dump(exclude_unset=True)
# #     #Note:exclude_unset=True includes only fields provided in the request.
# #     #setattr() updates those fields dynamically.
# #     for key, value in update_data.items():
# #         setattr(post, key, value)    
# #     db.commit()
# #     db.refresh(post)
# #     return post
# @app.patch("/api/post/{post_id}", response_model=PostUpdate)
# async def update_post_partial(post_id: int,post_data:PostUpdate,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

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
#     await db.commit()
#     await db.refresh(post,attribute_names=["author"])
#     return post


# ## Delete Post
# # @app.delete("/api/post/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
# # def delete_post(post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
# #     result = db.execute(select(models.Post).where(models.Post.id == post_id))

# #     post = result.scalars().first()

# #     if not post:
# #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

# #     db.delete(post)
# #     db.commit()
# @app.delete("/api/post/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_post(post_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.id == post_id))

#     post = result.scalars().first()

#     if not post:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found",)

#     await db.delete(post)
#     await db.commit()



# ## Create Post
# @app.post("/api/posts",response_model=PostResponse,status_code=status.HTTP_201_CREATED,)
# async def create_post(post: PostCreate,db: Annotated[AsyncSession, Depends(get_db)],):
#     result = await db.execute(select(models.User).where(models.User.id == post.user_id))

#     existing_user = result.scalars().first()

#     if not existing_user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

#     new_post = models.Post(title=post.title,content=post.content,user_id=post.user_id,)

#     db.add(new_post)
#     await db.commit()
#     await db.refresh(new_post,attribute_names=["author"])#each post need there author loaded
#     return new_post



# ## Create User
# @app.post("/api/users",response_model=PostResponse,status_code=status.HTTP_201_CREATED,)
# async def create_user(user: UserCreate,db:Annotated[AsyncSession,Depends(get_db)]):
#     result=await db.execute(select(models.User).where(models.User.username==user.username))
#     existingUser=result.scalars().first();

#     if(existingUser):
#       raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username Already Exists")

#     resultEmail=await db.execute(select(models.User).where(models.User.email==user.email))
#     existingEmail=resultEmail.scalars().first();

#     if(existingEmail):
#       raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email Already Exists")

#     newUser=models.User(username=user.username,email=user.email)
#     db.add(newUser)
#     await db.commit()
#     await db.refresh(newUser)
#     return newUser

# #get user by id
# @app.get("/api/users/{user_id}", response_model=UserResponse)
# async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
#     result = await db.execute(select(models.User).where(models.User.id == user_id),)

#     user = result.scalars().first()

#     if user:
#         return user

#     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)


# #get all post by users 
# # @app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
# # def get_user_posts(user_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
# #     result = db.execute(select(models.User).where(models.User.id == user_id))

# #     user = result.scalars().first()

# #     if not user:
# #         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

# #     result = db.execute(select(models.Post).where(models.Post.user_id == user_id))

# #     posts = result.scalars().all()

# #     return posts
# @app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
# async def get_user_posts(user_id: int,db: Annotated[AsyncSession, Depends(get_db)],):
#     print("Endpoint called")
#     result = await db.execute(select(models.User).where(models.User.id == user_id))

#     user = result.scalars().first()
#     print("User called")

#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

#     result = await db.execute(select(models.Post).options(selectinload(models.Post.author)).where(models.Post.user_id == user_id))
#     posts = result.scalars().all()
#     print("post called")

#     return posts



# ##userdate partial users
# @app.patch("/api/users/{user_id}", response_model=UserResponse)
# async def update_user(user_id: int,user_update: UpdateUser,db: Annotated[AsyncSession, Depends(get_db)],):
#     result =await  db.execute(select(models.User).where(models.User.id == user_id))
#     user = result.scalars().first()

#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)

#     if (user_update.username is not None and user_update.username != user.username):
#         result = await db.execute(select(models.User).where(models.User.username == user_update.username),)
#         existing_user = result.scalars().first()

#         if existing_user:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username already exists",)

#     if (user_update.email is not None and user_update.email != user.email):
#         result = await db.execute(select(models.User).where(models.User.email == user_update.email),)
#         existing_email = result.scalars().first()

#         if existing_email:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email already registered",)

#     if user_update.username is not None:
#         user.username = user_update.username

#     if user_update.email is not None:
#         user.email = user_update.email

#     if user_update.image_file is not None:
#         user.image_file = user_update.image_file

#     await db.commit()
#     await db.refresh(user)

#     return user

# ##Delete user by usrid , when user delete its all post also deleted 
# ## delete_user

# @app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
#     result = await db.execute(select(models.User).where(models.User.id == user_id))
#     user = result.scalars().first()

#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found",)
#     await db.delete(user)
#     await db.commit()

## StarletteHTTPException Handler
##Here our current Exception Handler are synchronous and we are returning here the JsonResponse Manually 

# @app.exception_handler(StarletteHTTPException)
# def general_http_exception_handler(request: Request,exception: StarletteHTTPException):
#     message = (
#         exception.detail
#         if exception.detail
#         else "An error occurred. Please check your request and try again."
#     )

#     if request.url.path.startswith("/api"):
#         return JSONResponse(
#             status_code=exception.status_code,
#             content={"detail": message},
#         )

#     return templates.TemplateResponse(
#         request,
#         "error.html",
#         {
#             "status_code": exception.status_code,
#             "title": exception.status_code,
#             "message": message,
#         },
#         status_code=exception.status_code,
#     )



@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        name="login.html",
        context={
            "title": "Login"
        }
    )
 


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        name="register.html",
        context={"title": "Register"},
    )

@app.get("/account", include_in_schema=False)
async def account_page(request: Request):
    return templates.TemplateResponse(
        request,
        name="account.html",
        context={"title": "Account"},
    )

@app.get("/forgot-password", include_in_schema=False)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot_password.html",
        {"title": "Forgot Password"},
    )


@app.get("/reset-password", include_in_schema=False)
async def reset_password_page(request: Request):
    response = templates.TemplateResponse(
        request,
        "reset_password.html",
        {"title": "Reset Password"},
    )

    response.headers["Referrer-Policy"] = "no-referrer"
    return response
    
##so the better approach will be asynchrounous FastAPi default handler
@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request,exception: StarletteHTTPException):

    #when api is used
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request,exception)
    #when template used
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
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
##Here our current Exception Handler are synchronous and we are returning here the JsonResponse Manually 
# @app.exception_handler(RequestValidationError)
# def validation_exception_handler(
#     request: Request,
#     exception: RequestValidationError
# ):
#     if request.url.path.startswith("/api"):
#         return JSONResponse(
#             status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
#             content={"detail": exception.errors()},
#         )

#     return templates.TemplateResponse(
#         request,
#         "error.html",
#         {
#             "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
#             "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
#             "message": "Invalid request. Please check your input and try again.",
#         },
#         status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
#     )

##so the better approach will be asynchrounous FastAPi default handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError
):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request,exception)
    
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
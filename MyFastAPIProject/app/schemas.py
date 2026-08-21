from  pydantic import BaseModel,ConfigDict,Field

class PostBase(BaseModel):
    title:str =Field(min_length=5,max_length=100)
    content:str =Field(min_length=5)
    author:str =Field(min_length=5,max_length=100)

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    model_config=ConfigDict(from_attributes=True)#it can read data with attribute not just dictionery ie: in dictionery we acess data like post['title'] but for db oject obj.title
    id:int
    date_posted:str

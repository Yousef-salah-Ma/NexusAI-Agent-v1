from pydantic import BaseModel 

class login_users(BaseModel):
    email: str 
    password : str 

class Create_Account(BaseModel):
    FirstName : str 
    LastName : str 
    age: int 
    email : str 
    password : str 
 

class messegas(BaseModel):
    user_input : str= None 
    
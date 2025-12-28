from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


# istanza della classe FastAPI
app = FastAPI(title="ITS App API") #,lifespan=lifespan

# @app.get("/{user_msg}")
# async def root(user_msg: str, limit: int = 10):
#     return{user_msg[:limit]}

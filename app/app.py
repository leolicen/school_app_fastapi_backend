from fastapi import FastAPI




# istanza della classe FastAPI
app = FastAPI(title="ITS App API") #,lifespan=lifespan

# @app.get("/{user_msg}")
# async def root(user_msg: str, limit: int = 10):
#     return{user_msg[:limit]}

import uvicorn
from fastapi import FastAPI
from routers.webhook import router

app = FastAPI(title="SAT Bot")
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=False)

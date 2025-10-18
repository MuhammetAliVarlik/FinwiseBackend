from fastapi import FastAPI
from app.api import user_routes, prompt_routes, response_routes
from app.core.database import Base, engine

# DB tablolarını oluştur (ilk seferde)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Finwise Backend")

# Router ekleme
app.include_router(user_routes.router)
app.include_router(prompt_routes.router)
app.include_router(response_routes.router)

@app.get("/")
def root():
    return {"message": "Finwise Backend is running 🚀"}

from fastapi import FastAPI
from pydantic import BaseModel
from Beta import run_assistant

app = FastAPI()

class Query(BaseModel):
    text: str

@app.post("/ask")
async def ask(query: Query):
    # здесь подключаешь свой код ассистента
    response = f"Элли ответила на: {query.text}"
    return {"answer": response}

if __name__ == "__main__":
    run_assistant()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List

app = FastAPI()

class Item(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1)
    description: str = Field(default="", max_length=300)

items_db = []  # in-memory items list

@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

@app.post("/items", response_model=Item, status_code=201)
async def create_item(item: Item):
    # check if id already exists
    if any(existing_item.id == item.id for existing_item in items_db):
        raise HTTPException(status_code=400, detail="Item with this ID already exists")
    items_db.append(item)
    return item

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

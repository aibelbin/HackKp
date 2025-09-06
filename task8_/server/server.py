from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from PIL import Image, ImageFilter
import io
import base64


class Rect(BaseModel):
    x: int
    y: int
    width: int
    height: int


class ProcessRequest(BaseModel):
    image_base64: str
    selections: List[Rect]


class SelectRequest(BaseModel):
    selections: List[Rect]
    rect: Rect


class PointRequest(BaseModel):
    selections: List[Rect]
    x: int
    y: int


class ProcessResponse(BaseModel):
    image_base64: str


app = FastAPI(title="Investigator Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def b64_to_image(data: str) -> Image.Image:
    raw = base64.b64decode(data)
    return Image.open(io.BytesIO(raw)).convert("RGBA")


def image_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/crop", response_model=ProcessResponse)
def crop(req: ProcessRequest):
    img = b64_to_image(req.image_base64)
    if not req.selections:
        return {"image_base64": image_to_b64(img)}
    r = req.selections[0]
    left = max(0, r.x)
    top = max(0, r.y)
    right = min(img.width, r.x + r.width)
    bottom = min(img.height, r.y + r.height)
    cropped = img.crop((left, top, right, bottom))
    return {"image_base64": image_to_b64(cropped)}


@app.post("/blackout", response_model=ProcessResponse)
def blackout(req: ProcessRequest):
    img = b64_to_image(req.image_base64)
    pixels = img.load()
    for r in req.selections:
        x0 = max(0, r.x)
        y0 = max(0, r.y)
        x1 = min(img.width, r.x + r.width)
        y1 = min(img.height, r.y + r.height)
        for y in range(y0, y1):
            for x in range(x0, x1):
                pixels[x, y] = (0, 0, 0, 255)
    return {"image_base64": image_to_b64(img)}


@app.post("/blur", response_model=ProcessResponse)
def blur(req: ProcessRequest):
    img = b64_to_image(req.image_base64)
    base = img.copy()
    for r in req.selections:
        x0 = max(0, r.x)
        y0 = max(0, r.y)
        x1 = min(img.width, r.x + r.width)
        y1 = min(img.height, r.y + r.height)
        region = img.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(radius=10))
        base.paste(region, (x0, y0))
    return {"image_base64": image_to_b64(base)}


@app.post("/select")
def select(req: SelectRequest):
    updated = req.selections + [req.rect]
    return {"selections": [s.model_dump() for s in updated]}


@app.post("/deselect")
def deselect(req: PointRequest):
    def contains(r: Rect, px: int, py: int) -> bool:
        return (px >= r.x and px <= r.x + r.width and py >= r.y and py <= r.y + r.height)

    remaining = [s for s in req.selections if not contains(s, req.x, req.y)]
    return {"selections": [s.model_dump() for s in remaining]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

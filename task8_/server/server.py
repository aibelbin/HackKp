from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from PIL import Image, ImageFilter
import io
import base64
import numpy as np
import cv2
try:
    from rembg import remove, new_session  # type: ignore
    _RMBG_SESSION = new_session("isnet-general-use")
except Exception:
    _RMBG_SESSION = None


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


def crop_to_alpha_bbox(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.split()[-1]
    bbox = alpha.getbbox()
    if bbox:
        return img.crop(bbox)
    return img


def enhance_rgba(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    rgba = np.array(img)
    bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l2 = clahe.apply(l)
    lab2 = cv2.merge([l2, a, b])
    bgr2 = cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)
    blur = cv2.GaussianBlur(bgr2, (0, 0), 1.0)
    sharp = cv2.addWeighted(bgr2, 1.35, blur, -0.35, 0)
    out = cv2.cvtColor(sharp, cv2.COLOR_BGR2RGBA)
    out[..., 3] = rgba[..., 3]
    return Image.fromarray(out)


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
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    for r in req.selections:
        x0 = max(0, r.x)
        y0 = max(0, r.y)
        x1 = min(img.width, r.x + r.width)
        y1 = min(img.height, r.y + r.height)
        draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0, 255))
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


@app.post("/select_object", response_model=ProcessResponse)
def select_object(req: ProcessRequest):
    img_pil = b64_to_image(req.image_base64)
    if not req.selections:
        return {"image_base64": image_to_b64(img_pil)}
    r = req.selections[0]
    x = max(0, r.x)
    y = max(0, r.y)
    w = max(1, r.width)
    h = max(1, r.height)

    x1 = min(img_pil.width, x + w)
    y1 = min(img_pil.height, y + h)
    roi_pil = img_pil.crop((x, y, x1, y1)).convert("RGBA")

    out_pil: Image.Image | None = None
    if _RMBG_SESSION is not None:
        try:
            out = remove(
                roi_pil,
                session=_RMBG_SESSION,
                alpha_matting=True,
                alpha_matting_foreground_threshold=240,
                alpha_matting_background_threshold=10,
                alpha_matting_erode_size=10,
            )
            out_pil = out if isinstance(out, Image.Image) else Image.open(io.BytesIO(out)).convert("RGBA")
        except Exception:
            out_pil = None

    if out_pil is None:
        img_rgba = np.array(img_pil)
        img_bgr = cv2.cvtColor(img_rgba, cv2.COLOR_RGBA2BGR)
        roi = img_bgr[y:y1, x:x1]
        mask_full = np.zeros(img_bgr.shape[:2], dtype=np.uint8)
        used_saliency = False
        if hasattr(cv2, "saliency") and roi.size:
            try:
                sal = cv2.saliency.StaticSaliencyFineGrained_create()
                ok, sal_map = sal.computeSaliency(roi)
                if ok:
                    sal_uint8 = (sal_map * 255).astype(np.uint8)
                    _, sal_bin = cv2.threshold(sal_uint8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                    sal_bin = cv2.morphologyEx(sal_bin, cv2.MORPH_CLOSE, kernel, iterations=2)
                    cnts, _ = cv2.findContours(sal_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if cnts:
                        cnt = max(cnts, key=cv2.contourArea)
                        sal_mask_roi = np.zeros_like(sal_bin)
                        cv2.drawContours(sal_mask_roi, [cnt], -1, 255, thickness=cv2.FILLED)
                    else:
                        sal_mask_roi = sal_bin
                    mask_full[y:y1, x:x1] = sal_mask_roi
                    used_saliency = True
            except Exception:
                used_saliency = False

        if not used_saliency:
            mask_full[y:y1, x:x1] = 255

        gc_mask = np.zeros(img_bgr.shape[:2], np.uint8)
        gc_mask[:] = cv2.GC_BGD
        gc_mask[y:y1, x:x1] = cv2.GC_PR_BGD
        gc_mask[mask_full > 0] = cv2.GC_PR_FGD
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        try:
            cv2.grabCut(img_bgr, gc_mask, None, bgdModel, fgdModel, 3, cv2.GC_INIT_WITH_MASK)
        except Exception:
            pass
        mask2 = np.where((gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD), 255, 0).astype("uint8")
        b, g, r_b = cv2.split(img_bgr)
        rgba = cv2.merge([b, g, r_b, mask2])
        out_pil = Image.fromarray(cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA))
        out_pil = out_pil.crop((x, y, x1, y1))

    out_pil = crop_to_alpha_bbox(out_pil)
    out_pil = enhance_rgba(out_pil)
    return {"image_base64": image_to_b64(out_pil)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

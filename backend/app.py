from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from backend.models.schemas import GenerateRequest, GenerateResponse, ExportDocxRequest
from backend.core.prompts import build_prompt
from backend.core.parser import parse_essay
from backend.core.docx_builder import build_docx
from backend.services.openrouter import chat_complete
import asyncio
import os
import traceback

app = FastAPI(title="DocGen Local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.getcwd(), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse("<h1>DocGen Local</h1><p>frontend/referat.html не найден.</p>", status_code=200)
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

_gen_lock = asyncio.Lock()

@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    async with _gen_lock:
        try:
            ls = 1.5 if req.page_target >= 6 else 1.15
            prompt = build_prompt(
                doc_type=req.doc_type,
                topic=req.topic,
                locale=req.locale,
                style=req.style,
                depth=req.outline_depth,
                requirements=req.requirements,
                lab_meta=req.lab_meta,
                page_target=req.page_target,
                line_spacing=ls,
                font_size=12,
            )
            text = await chat_complete(prompt, req.model or None)
            essay = parse_essay(text)
            return GenerateResponse(essay=essay)
        except ValueError as e:
            raise HTTPException(502, f"Ответ модели не JSON: {e}")
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(502, f"Ошибка генерации: {e}")

@app.post("/export-docx")
async def export_docx(req: ExportDocxRequest):
    try:
        path = build_docx(req)
        if not os.path.exists(path):
            raise HTTPException(500, "DOCX не создан")
        return FileResponse(
            path,
            filename=os.path.basename(path),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"detail": f"DOCX error: {e}"}, status_code=500)

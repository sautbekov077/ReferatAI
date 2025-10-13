from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import os

from schemas import GenerateRequest, ExportDocxRequest
from docx_builder import build_docx_bytes
from parser import to_outline
from openrouter import generate_essay

app = FastAPI(title="ReferatAI Backend", version="1.0.0")

# CORS: список разрешённых источников берётся из ENV:
# CORS_ALLOW_ORIGINS="https://your-pages.pages.dev,https://your-domain.com"
cors_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "")
allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins else [],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
    max_age=86400,
)

@app.post("/generate")
async def generate(req: GenerateRequest):
    try:
        essay = await generate_essay(
            topic=req.topic,
            doc_type=req.doc_type,
            locale=req.locale,
            style=req.style,
            outline_depth=req.outline_depth,
            requirements=req.requirements,
            lab_meta=req.lab_meta,
            model=req.model,
            page_target=req.page_target,
        )
        outline = to_outline(essay)
        return {"essay": outline}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/export-docx")
async def export_docx(req: ExportDocxRequest):
    try:
        docx_bytes = build_docx_bytes(
            topic=req.topic,
            essay=req.essay,
            include_toc=req.include_toc,
            line_spacing=req.line_spacing,
            font_name=req.font_name,
            font_size_pt=req.font_size_pt,
            margins_cm=req.margins_cm,
            doc_type=req.doc_type,
            page_target=req.page_target,
        )
        filename = f"{req.doc_type or 'document'}.docx"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

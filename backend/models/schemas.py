from typing import List, Optional, Literal
from pydantic import BaseModel, Field

DocType = Literal["referat","article_ru","article_en","article_ru_en","lab"]
Style = Literal["academic","concise","explanatory"]

class LabMeta(BaseModel):
    discipline: Optional[str] = None
    variant: Optional[str] = None
    goal: Optional[str] = None
    equipment: Optional[str] = None

class Section(BaseModel):
    title: str
    paragraphs: List[str] = Field(default_factory=list)
    subsections: List["Section"] = Field(default_factory=list)

Section.model_rebuild()

class GenerateRequest(BaseModel):
    topic: str
    doc_type: DocType = "referat"
    locale: str = "ru"
    style: Style = "academic"
    outline_depth: int = 2
    requirements: Optional[str] = None
    lab_meta: Optional[LabMeta] = None
    model: Optional[str] = None
    page_target: int = 8

class GenerateResponse(BaseModel):
    essay: Section

class ExportDocxRequest(BaseModel):
    topic: str
    essay: Section
    include_toc: bool = True
    line_spacing: float = 1.15
    font_name: str = "Times New Roman"
    font_size_pt: int = 12
    margins_cm: float = 2.0
    doc_type: DocType = "referat"
    page_target: int = 8

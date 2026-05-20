from typing import Annotated, Optional, TypedDict, List, Any
from langgraph.graph import add_messages
from pydantic import BaseModel, Field

class SubPartPlan(BaseModel):
    title: str = Field(description="le titre de la sous partie")
    content: str = Field(description="le contenu détailléde cette sous partie")
    diagram: Optional[str] = Field(description="la description d'un diagramme servant à illustrer cette sous partie")

class PartPlan(BaseModel):
    title: str = Field(description="le titre de la partie")
    time: str = Field(description="le temps associé à cette partie")
    topics: List[str] = Field(description="la liste des éléments du programme de terminale scientifique auquel cette partie se rattache")
    content: str = Field(description="Un résumé du contenu de cette partie")
    subparts: List[SubPartPlan] = Field(description="la liste des sous-chapitres qui constituent cette partie")

class GrandOralPlan(BaseModel):
    parts: List[PartPlan] = Field(description="la liste des parties du plan de l'exposé pour le grand oral du bac")

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    subject: str
    pros: List[str]
    cons: List[str]
    topics: List[str]
    is_valid: bool
    plan: Optional[GrandOralPlan]
    diagram_titles: List[str]
    diagram_urls: List[str]

class EvaluationResult(BaseModel):
    topics: List[str] = Field(description="la liste des éléments du programme auquel le sujet se rattache")
    is_valid: bool = Field(description="Ce sujet est il un bon sujet pour le grand oral?")

class ProsArguments(BaseModel):
    pros: List[str] = Field(description="La liste des arguments pour le sujet du grand oral")

class ConsArguments(BaseModel):
    cons: List[str] = Field(description="La liste des arguments contre le sujet du grand oral")

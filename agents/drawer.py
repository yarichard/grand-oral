import base64
import zlib
from langchain_openai import ChatOpenAI, OpenAI
from oral_structs import State, GrandOralPlan
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


class MermaidDiagram(BaseModel):
    mermaid_code: str = Field(description="Valid Mermaid diagram code (mindmap or flowchart TD) illustrating the key concepts of the subject")

class Drawer:
    def __init__(self):
        self.tools = []
        # gpt-4o: more reliable Mermaid syntax than gpt-4o-mini
        self.diagram_llm = ChatOpenAI(model="gpt-4o").with_structured_output(MermaidDiagram)
        self.image_client = OpenAI()

    def generate_mermaid_diagram(self, state: State) -> dict:
        import zlib
        subject = state.get("subject", "")
        plan: GrandOralPlan = state.get("plan", None)

        if not plan:
            return {"diagram_titles": [], "diagram_urls": []}

        # Collect (title, description) pairs from every subpart that has a diagram
        descriptions = [
            (subpart.title, subpart.diagram)
            for part in plan.parts
            for subpart in part.subparts
            if subpart.diagram
        ]

        titles, urls = [], []
        for title, description in descriptions:
            messages = [
                SystemMessage(content=(
                    "You create concise Mermaid diagrams for French baccalaureate students. "
                    "Use mindmap or flowchart TD format. Keep it simple with 6-10 nodes maximum. "
                    "Output only valid Mermaid syntax — no markdown fences, no extra text."
                )),
                HumanMessage(content=(
                    f"Subject: {subject}\n"
                    f"Section: {title}\n"
                    f"Description: {description}"
                ))
            ]
            result: MermaidDiagram = self.diagram_llm.invoke(messages)
            compressed = zlib.compress(result.mermaid_code.encode("utf-8"), level=9)
            encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
            titles.append(title)
            urls.append(f"https://kroki.io/mermaid/png/{encoded}")

        return {"diagram_titles": titles, "diagram_urls": urls}
    
    def generate_image(self, state: State) -> dict:
        subject = state.get("subject", "")
        plan: GrandOralPlan = state.get("plan")

        if not plan:
            return {"diagram_titles": [], "diagram_urls": []}

        descriptions = [
            (subpart.title, subpart.diagram)
            for part in plan.parts
            for subpart in part.subparts
            if subpart.diagram
        ]

        titles, urls = [], []
        for title, description in descriptions:
            prompt = (
                f"Diagramme d'illustration pour le grand oral du bac. Ce diagramme doit pouvoir être dessiné à la main par l'élève lors de la préparation de sa présentation. "
                f"Sujet du grand oral: {subject}. "
                f"Section à illustrer: {title}. {description}. "
                f"Style clair, épuré, pédagogique, fond blanc, étiquettes en français."
            )
            response = self.image_client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024",
                n=1
            )
            titles.append(title)
            urls.append(response.data[0].url)

        return {"diagram_titles": titles, "diagram_urls": urls}
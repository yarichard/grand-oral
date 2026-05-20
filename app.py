import gradio as gr
from oral import GrandOral
from oral_structs import GrandOralPlan
import httpx
import io
import os
from PIL import Image as PILImage

async def setup():
    grand_oral = GrandOral()
    await grand_oral.build_graph()
    return grand_oral

def free_resources(grand_oral):
    print("Cleaning up")
    try:
        if grand_oral:
            grand_oral.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")

async def process_message(grand_oral, message):
    result = await grand_oral.run_superstep(message)
    pros = "\n".join(f"- {p}" for p in result.get("pros", []))
    cons = "\n".join(f"- {c}" for c in result.get("cons", []))
    topics = "\n".join(f"- {t}" for t in result.get("topics", []))
    is_valid = "✅ Oui" if result.get("is_valid") else "❌ Non"
    plan: GrandOralPlan = result.get("plan")

    plan_md = ""
    if plan:
        for part in plan.parts:
            plan_md += f"\n### {part.title} ({part.time})\n{part.content}\n"
            for subpart in part.subparts:
                plan_md += f"\n#### {subpart.title}\n{subpart.content}\n"

    plan_section = f"\n---\n## Plan de l'exposé\n{plan_md}" if plan_md else ""

    markdown = f"""## Évaluation du sujet

**Valide :** {is_valid}

**Arguments pour :**
{pros}

**Arguments contre :**
{cons}

**Éléments du programme :**
{topics}{plan_section}
"""

    gallery_items = []
    titles = result.get("diagram_titles", [])
    urls = result.get("diagram_urls", [])
    async with httpx.AsyncClient(timeout=30) as client:
        for title, url in zip(titles, urls):
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    img = PILImage.open(io.BytesIO(resp.content))
                    gallery_items.append((img, title))
            except Exception:
                pass

    return markdown, gallery_items

with gr.Blocks(theme=gr.themes.Default(primary_hue="emerald")) as grand_oral_ui:
    gr.Markdown("## Evaluation des sujets de grand oral")
    grand_oral = gr.State(delete_callback=free_resources)

    with gr.Row():
        with gr.Column(scale=2):
            message_output = gr.Markdown("## en attente de sujet à analyser")
        with gr.Column(scale=1):
            diagram_output = gr.Gallery(label="Diagrammes conceptuels", columns=2, show_label=True)
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Entrer le sujet à analyser")
    with gr.Row():
        go_button = gr.Button("Go!", variant="primary")
    
    grand_oral_ui.load(setup, [], [grand_oral])
    message.submit(process_message, [grand_oral, message], [message_output, diagram_output])
    go_button.click(process_message, [grand_oral, message], [message_output, diagram_output])

auth = None
app_user = os.environ.get("APP_USER")
app_password = os.environ.get("APP_PASSWORD")
if app_user and app_password:
    auth = (app_user, app_password)

grand_oral_ui.launch(auth=auth)

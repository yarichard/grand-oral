from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langsmith import uuid
from agents.student import Student
from agents.drawer import Drawer
from agents.teacher import Teacher
from oral_structs import EvaluationResult, ProsArguments, ConsArguments, State
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import uuid

from rag import BacDocumentManager

load_dotenv(override=True)


class GrandOral:
    def __init__(self):

        self.rag = BacDocumentManager()        

        self.tools = []
        serper = GoogleSerperAPIWrapper()
        tool_search = Tool(
                name="search",
                func=serper.run,
                description="Use this tool when you want to get the results of an online web search"
            )

        self.tools.append(tool_search)
        self.tools.append(self.rag.retriever_tool)

        self.student_agent = Student()
        self.drawer_agent = Drawer()
        self.teacher = Teacher(self.tools)

        self.thread = str(uuid.uuid4())
        self.memory = MemorySaver()

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Nodes
        graph_builder.add_node("teacher_pros", self.teacher.evaluate_topic_relevant)
        graph_builder.add_node("teacher_cons", self.teacher.evaluate_topic_not_relevant)
        graph_builder.add_node("judge", self.teacher.judge_topic)
        graph_builder.add_node("student", self.student_agent.generate_plan_for_topic)
        graph_builder.add_node("diagram", self.drawer_agent.generate_mermaid_diagram)
        #graph_builder.add_node("image", self.drawer_agent.generate_image)

        graph_builder.add_edge(START, "teacher_pros")
        graph_builder.add_edge(START, "teacher_cons")
        graph_builder.add_edge("teacher_pros", "judge")
        graph_builder.add_edge("teacher_cons", "judge")
        graph_builder.add_conditional_edges("judge", self.student_agent.can_generate_plan, {"student": "student", "END": END})
        graph_builder.add_edge("student", "diagram")
        #graph_builder.add_edge("image", END)
        graph_builder.add_edge("diagram", END)

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message: str):
        config = {"configurable": {"thread_id": self.thread}}

        state = {
            "subject": message,
            "pros": [],
            "cons": [],
            "topics": [],
            "is_valid": False,
            "diagram_titles": [],
            "diagram_urls": [],
        }
        return await self.graph.ainvoke(state, config=config)
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langsmith import uuid
from agents.student import Student
from agents.drawer import Drawer
from oral_structs import EvaluationResult, ProsArguments, ConsArguments, State
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import uuid

load_dotenv(override=True)


class GrandOral:
    def __init__(self):
        self.tools = []

        teacher_llm_base = ChatOpenAI(model="gpt-4o-mini")
        self.judge_llm = teacher_llm_base.bind_tools(self.tools).with_structured_output(EvaluationResult)
        self.teacher_llm_pros = teacher_llm_base.bind_tools(self.tools).with_structured_output(ProsArguments)
        self.teacher_llm_cons = teacher_llm_base.bind_tools(self.tools).with_structured_output(ConsArguments)

        self.student_agent = Student()
        self.drawer_agent = Drawer()
        self.thread = str(uuid.uuid4())
        self.memory = MemorySaver()

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Nodes
        graph_builder.add_node("teacher_pros", self.evaluate_topic_relevant)
        graph_builder.add_node("teacher_cons", self.evaluate_topic_not_relevant)
        graph_builder.add_node("judge", self.judge_topic)
        graph_builder.add_node("student", self.student_agent.generate_plan_for_topic)
        graph_builder.add_node("diagram", self.drawer_agent.generate_diagram)

        # Parallel start → teachers → converge to judge
        graph_builder.add_edge(START, "teacher_pros")
        graph_builder.add_edge(START, "teacher_cons")
        graph_builder.add_edge("teacher_pros", "judge")
        graph_builder.add_edge("teacher_cons", "judge")

        # Judge → student (if valid) or END
        graph_builder.add_conditional_edges("judge", self.student_agent.can_generate_plan, {"student": "student", "END": END})

        # Student → diagram → END
        graph_builder.add_edge("student", "diagram")
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

    def evaluate_topic(self, relevant: bool, state: State) -> State:
        pros_or_cons = "arguments pour" if relevant else "arguments contre"
        system_message = f"Vous êtes un professeur de lycée  de terminale, qui connait parfaitement le programme de mathématiques et de physique chimie de terminale. \
        Votre rôle est d'évaluer les sujets pour le grand oral du bac, en tenant compte des contraintes suivantes: \
        - Le sujet doit être en lien avec les programmes de terminale scientifique, notamment en mathématiques et en physique-chimie\
        - Le sujet doit permettre à l'élève de démontrer sa capacité à construire une argumentation solide et à présenter des connaissances précises.\
        - Le sujet doit être suffisamment large pour permettre une exploration approfondie, mais pas trop vaste pour éviter la superficialité.\
        - Le sujet doit être original et susciter l'intérêt de l'élève, tout en restant pertinent par rapport aux thématiques abordées en terminale scientifique. \
        Vous pouvez également utiliser l'outil search pour rechercher les dernières informations sur internet \
        Votre réponse doit contenir une liste qui donnent les {pros_or_cons}"

        user_message = f"Evaluer le sujet suivant: {state['subject']}"

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]

        if relevant:
            result: ProsArguments = self.teacher_llm_pros.invoke(messages)
            return {"pros": result.pros,
                    "messages": messages
                    }
        else:
            result: ConsArguments = self.teacher_llm_cons.invoke(messages)
            return {"cons": result.cons,
                    "messages": messages
                    }


    def evaluate_topic_relevant(self, state: State) -> State:
        return self.evaluate_topic(True, state)

    def evaluate_topic_not_relevant(self, state: State) -> State:
        return self.evaluate_topic(False, state)

    def judge_topic(self, state: State) -> State:
        system_message = f"Vous êtes un professeur de lycée de terminale, qui connait parfaitement le programme de mathématiques et de physique chimie de terminale. \
        Votre rôle est d'évaluer les sujets pour le grand oral du bac, en tenant compte des contraintes suivantes: \
        - Le sujet doit être en lien avec les programmes de terminale scientifique, notamment en mathématiques et en physique-chimie\
        - Le sujet doit permettre à l'élève de démontrer sa capacité à construire une argumentation solide et à présenter des connaissances précises.\
        - Le sujet doit être suffisamment large pour permettre une exploration approfondie, mais pas trop vaste pour éviter la superficialité.\
        - Le sujet doit être original et susciter l'intérêt de l'élève, tout en restant pertinent par rapport aux thématiques abordées en terminale scientifique. \
        Vous pouvez également utiliser l'outil search pour rechercher les dernières informations sur internet"

        user_message = f"Vous devez évaluer le sujet suivant: {state['subject']}\
            Vous disposez des arguments pour et contre le sujet. \
            Les arguments pour sont les suivants: {state['pros']}\
            Les arguments contre sont les suivants: {state['cons']}\
            Votre réponse doit contenir la liste des arguments pour, la liste des arguments contre, les matières et la liste des sujets du programme de terminale auquel le sujet se rattache. \
            Enfin, une réponse claire: oui ou non sur la pertinence de ce sujet.\
            Le resultat de cette analyse sera sous le format Markdown. Répondez uniquement avec le texte brut du markdown, pas de balise markdown, pas de phrase supplémentaire."
        
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]
        result: EvaluationResult = self.judge_llm.invoke(messages)

        return {
            "topics": result.topics,
            "is_valid": result.is_valid,
        }
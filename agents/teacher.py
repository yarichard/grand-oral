
from langchain_classic.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode

from oral_structs import ConsArguments, EvaluationResult, ProsArguments, State

class Teacher:
    def __init__(self, tools: list):
        self.tools = tools
        self.teacher_llm = ChatOpenAI(model="gpt-4o-mini")
        self.teacher_llm_with_tools = self.teacher_llm.bind_tools(self.tools)  # for tool calling
        self.tool_node = ToolNode(self.tools) 

    def evaluate_topic_relevant(self, state: State) -> State:
        return self.evaluate_topic(True, state)

    def evaluate_topic_not_relevant(self, state: State) -> State:
        return self.evaluate_topic(False, state)
    
    def evaluate_topic(self, relevant: bool, state: State) -> State:
        pros_or_cons = "arguments pour" if relevant else "arguments contre"
        system_message = f"Vous êtes un professeur de lycée de terminale, qui connait parfaitement le programme de mathématiques et de physique chimie de terminale. \
        Votre rôle est d'évaluer les sujets pour le grand oral du bac, en tenant compte des contraintes suivantes: \
        - Le sujet doit être en lien avec les programmes de terminale scientifique, notamment en mathématiques et en physique-chimie\
        - Le sujet doit permettre à l'élève de démontrer sa capacité à construire une argumentation solide et à présenter des connaissances précises.\
        - Le sujet doit être suffisamment large pour permettre une exploration approfondie, mais pas trop vaste pour éviter la superficialité.\
        - Le sujet doit être original et susciter l'intérêt de l'élève, tout en restant pertinent par rapport aux thématiques abordées en terminale scientifique. \
        Votre réponse doit contenir une liste qui donnent les {pros_or_cons}"

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=f"Evaluer le sujet suivant: {state['subject']}")
        ]

        # Pass 1: let the LLM call tools freely
        messages = self.run_with_tools(messages)

        # Pass 2: extract structured output from enriched context
        if relevant:
            result: ProsArguments = self.teacher_llm.with_structured_output(ProsArguments).invoke(messages)
            return {"pros": result.pros}
        else:
            result: ConsArguments = self.teacher_llm.with_structured_output(ConsArguments).invoke(messages)
            return {"cons": result.cons}
        
    def judge_topic(self, state: State) -> State:
        system_message = "Vous êtes un professeur de lycée de terminale, qui connait parfaitement le programme de mathématiques et de physique chimie de terminale. \
        Votre rôle est d'évaluer un sujet pour le grand oral. Vous prenez en compte les arguments Pour et Contre qui vous sont fournis. A partir de ces arguments, vous effectuez une liste des liens avec les programmes scolaires. " \
        "Pour chaque élément du programme que vous identifiez, vous validez qu'il fait bien partie du programme en vérifiant sa présence dans les documents de référence à l'aide de l'outil search_school_programs. " \
        "S'ils ne sont pas présents, vous ne les ajoutez pas dans la liste. " \
        "S'ils sont présents, vous les ajoutez avec le nom du ducument de référence ainsi que le numéro de page"

        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=f"Évaluez le sujet: {state['subject']} en tenant compte des arguments Pour: {state['pros']} et Contre: {state['cons']}")
        ]

        messages = self.run_with_tools(messages)

        result: EvaluationResult = self.teacher_llm.with_structured_output(EvaluationResult).invoke(messages)
        return {"topics": result.topics, "is_valid": result.is_valid}

    def run_with_tools(self, messages: list) -> list:
        """Run the LLM in a loop until it stops calling tools."""
        while True:
            response = self.teacher_llm_with_tools.invoke(messages)
            messages = messages + [response]
            if not response.tool_calls:
                break
            tool_results = self.tool_node.invoke({"messages": messages})
            messages = messages + tool_results["messages"]  # append, don't replace
        return messages
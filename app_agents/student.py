from oral_structs import State, GrandOralPlan
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

GRAND_ORAL_DURATION = 10 # in minutes

class Student:
    def __init__(self):
        self.tools = []
        self.student_llm = ChatOpenAI(model="gpt-5.4").bind_tools(self.tools).with_structured_output(GrandOralPlan)

    def generate_plan_for_topic(self, state: State) -> dict:
        system_message = "Vous êtes un brillant élève de terminale scientifique, et vous préparez le plan de votre grand oral du baccalauréat."
        user_message = f"Le sujet que vous avez choisi est {state['subject']}\
        Les points importants qui valident ce sujet sont les suivants: {state['pros']}\
        Les points de vigilance sont les suivants: {state['cons']}\
        Les sujets du programme auquel il se rattache sont les suivants: {state['topics']}\
        Ecrire le plan de l'exposé en décrivant les chacune des parties cet exposé avec :\
        - le titre\
        - un résumé du contenu\
        - le temps de cette partie\
        - les sujets du programme qui sont abordés\
        - la liste de chacune des sous parties contenant elles mêmes:le titre, le contenu et éventuellement la description d'un diagramme servant à l'illustrer.\
        Le plan doit contenir au minimum 3 parties, avec une introduction et une conclusion. Le total du temps des différentes parties doit être de {GRAND_ORAL_DURATION} minutes"

        messages = [
            SystemMessage(content=system_message), 
            HumanMessage(content=user_message)]
        eval_result: GrandOralPlan = self.student_llm.invoke(messages)
        return {"plan": eval_result,
                "messages": messages
                }
    
    def can_generate_plan(self, state: State) -> str:
        if state["is_valid"]:
            return "student"
        return "END"
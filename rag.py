from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import create_retriever_tool

urls = [
    # Mathematics
    "https://static.data.gouv.fr/resources/programmes-denseignement-de-terminale-generale-reforme-du-baccalaureat-2021/20190830-150235/mene1921264a-spe264-annexe-1158825.pdf",
    "https://static.data.gouv.fr/resources/programmes-denseignement-de-terminale-generale-reforme-du-baccalaureat-2021/20190830-150235/mene1921265a-spe265-annexe-1159134.pdf",
    "https://static.data.gouv.fr/resources/programmes-denseignement-de-terminale-generale-reforme-du-baccalaureat-2021/20190830-150230/mene1921246a-spe246-annexe-1158907.pdf",
    # Physics
    "https://static.data.gouv.fr/resources/programmes-denseignement-de-terminale-generale-reforme-du-baccalaureat-2021/20190830-150230/mene1921249a-spe249-annexe-1158929.pdf",
    # SVT
    "https://static.data.gouv.fr/resources/programmes-denseignement-de-terminale-generale-reforme-du-baccalaureat-2021/20190830-150231/mene1921252a-spe252-annexe-1159114.pdf"
]

class BacDocumentManager:
    def __init__(self):
        self.persist_dir = "./chroma_db"
        vectorstore = self.load_vectorstore()  # or build_vectorstore(urls) on first run
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        self.retriever_tool = create_retriever_tool(
            retriever,
            name="search_school_programs",
            description="Recherche des informations dans les documents PDF du programme du baccalauréat. Utiliser cet outil pour trouver des notions, des thèmes ou des éléments du programme"
        )

    def build_vectorstore(self, urls: list[str]):
        docs = []
        for url in urls:
            loader = PyPDFLoader(url)
            docs.extend(loader.load())

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_documents(docs)

        return Chroma.from_documents(chunks, OpenAIEmbeddings(), persist_directory=self.persist_dir)
    

    def load_vectorstore(self):
        return Chroma(persist_directory=self.persist_dir, embedding_function=OpenAIEmbeddings())
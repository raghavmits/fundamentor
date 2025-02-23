import wikipedia
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings


KEY_TERMS_PROMPT = """
    Identify and list only the **key terms** related to the **fundamental concepts** of the subject discussed in the lecture.  
    - Focus strictly on **core theories, principles, models, and frameworks**.  
    - Do **not** provide definitions, explanations, or examples.  
    - Format the output as a **comma-separated list** of keywords.  
    
    Example Output:  
    Neural Networks, Backpropagation, Attention Mechanism, Gradient Descent, Transformer Models
    """


class EnrichKB:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()

    def get_key_terms(self, vector_store: Chroma) -> str:
        """Get key terms from the vector store"""
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        response = retriever.invoke({"query": KEY_TERMS_PROMPT})
        return response["result"]
    
    
    def enrich_embeddings(self, vector_store: Chroma) -> Chroma:
        """Enrich embeddings by searching key terms in wikipedia using wikipedia api  and adding relevant information to the embeddings"""
        key_terms = self.get_key_terms(vector_store)
        for term in key_terms:
            try:
                # Search Wikipedia for the term
                search_results = wikipedia.search(term)
                if search_results:
                    page = wikipedia.page(search_results[0])
                    summary = page.summary
                    # Add summary to the metadata of the embeddings
                    vector_store.add_texts([summary], [{"source": f"Wikipedia: {term}"}])
            except Exception as e:
                print(f"Error enriching embeddings for {term}: {str(e)}")
        return vector_store
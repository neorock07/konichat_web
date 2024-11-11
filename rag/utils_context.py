
class Utils_context:
    """
    **NOT USED ANYMORE, THE PURPOSE OF THIS CODE HAS BEEN COPIED DIRECTLY
    IN FILE `inference.py`, ALLOWED TO REMOVE OR KEEP THE CODE.** 
    
    kode untuk memberikan context previous chat.
    
    Parameters:
    context_chain : chain dari pipline chat
    """

    def __init__(self, context_chain):
        self.context_chain = context_chain

    def contextualization_question(self,input: dict):
            """
            function contextualization_question
            Parameters:
                input (dict): parameter untuk mengisi nilai return dari runnable prompt-template
            Returns:
            if list chat_history not None <-:  
                context_chain (Any): objek pipeline chain
            else:
                user question
            """
              
            if input.get("chat_history"):
                return self.context_chain
            else:
                return input["question"]
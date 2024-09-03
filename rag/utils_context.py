 # """
    #  kode untuk memberikan context previous chat
    # parameter class Utils_context:
    # context_chain : chain dari pipline chat
    # 
    # function contextualization_question
    # params:
    #     input (dict): parameter untuk mengisi nilai return dari runnable prompt-template
    #  returns:
    #   if list chat_history not None <-:  
    #       context_chain (Any): objek pipeline chain
    #   else:
    #       user question
    # """

class Utils_context:
    def __init__(self, context_chain):
        self.context_chain = context_chain

    def contextualization_question(self,input: dict):
            if input.get("chat_history"):
                return self.context_chain
            else:
                return input["question"]
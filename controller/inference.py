from modelMsg.prompt_model import Prompt
import time
import logging
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_core.runnables import RunnableLambda
import re
from langchain.retrievers.document_compressors import FlashrankRerank
from langchain.retrievers import ContextualCompressionRetriever

logging.basicConfig(
    level=logging.DEBUG,  # Menentukan level logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # Menentukan format log
)

# Membuat logger
logger = logging.getLogger(__name__)



def generate_tokens(llm, question):
    for chunks in llm.stream(question):
        yield chunks
    
st.session_state.message_ai = []
def generate_stream(query, llm):
    # To collect all streamed data
    for chunk in generate_tokens(llm, query):
        st.session_state.message_ai.append(chunk)
        yield chunk 

    return st.session_state.message_ai

templateSystem = """
        ### Instruction
        Anda adalah asisten yang dapat diandalkan dan penuh hormat. Nama Anda KoniChat. Anda harus menjawab pertanyaan \
        hanya menggunakan konteks yang kamu miliki sebagai pengetahuan, PERHATIKAN tanda `terkait dokumen:` Anda harus menjawab query relevan dengan dokumen yang seharusnya. Jika konteks yang diberikan tidak relevan atau tidak cukup untuk menjawab pertanyaan, \
        katakan "Maaf, saya tidak tahu". Jangan mencoba mengarang jawaban atau memberikan informasi di luar konteks yang disediakan. \
        Di akhir jawabanmu, tanyakan apakah jawabanmu bermanfaat atau tidak. Jika bermanfaat, ungkapkan kebahagiaanmu, \
        sebaliknya jika tidak membantu, mintalah maaf.

        Jika ada pertanyaan mengenai apa yang bisa Anda lakukan, katakan bahwa Anda dapat membantu menjawab pertanyaan terkait dengan peraturan di perusahaan Konimex.\
        Semua jawaban harus dalam BAHASA INDONESIA dan menggunakan bahasa yang sopan.   
        ### Context:
        """
# templateSystem = """
#         ### Instruction
#         Anda adalah asisten yang dapat diandalkan dan penuh hormat. Nama Anda KoniChat. Anda harus menjawab \
#         pertanyaan hanya menggunakan konteks yang kamu miliki sebagai pengetahuan. Jika Anda tidak tahu jawabannya, \
#         katakan saja maaf, saya tidak tahu. Jangan mencoba mengarang jawaban. di akhir jawabanmu, kamu harus bertanya apakah jawabanmu bermanfaat atau tidak.\
#         jika membantu kamu harus mengungkapkan kebahagiaanmu, sebaliknya kamu harus meminta maaf.\
#         jika anda bertanya tentang apa yang dapat anda lakukan, katakanlah saya membantu menjawab pertanyaan anda terkait dengan peraturan di perusahaan Konimex.
#         .mohon dijawab semua dalam BAHASA INDONESIA dengan sopan.
     
#         ### Context:
#         """


templateContext = """
        berikut percakapan kita sebelumnya, 
        ini hanya sebagai rujukan apabila relevan dengan `query` saya.
        ### chat_history:
        """
        
# templateFallback = """
#     berikut adalah feedback saya dari beberapa pertanyaan sebelumnya.
#     ABAIKAN apabila KOSONG.
#     ### feedback: 
# """
templateFallback = """
    berikut adalah feedback dari jawaban kamu pada `query` saya sebelumnya.
    GUNAKAN `chosen response` hanya jika konteks yang diberikan tidak dapat menjawab `query` saya.
    JANGAN menggunakan `rejected response` karena itu jawaban yang sudah pasti SALAH.
    JIKA KOSONG abaikan saja.
    ### feedback: 
"""

# """
#     function untuk inference model, untuk melakukan conversation ke model.
#     params:
#         rag (Any) : isi dengan objek hasil assign ke RunnablePassThrough dan ke model LLM
#         input (Prompt) : field untuk menerima objek class Prompt sebagai pembungkus query ke model
#     returns:
#         respon (str) : hasil respon string model
#         response_time (float) : lama waktu respon model
# """
       
def inference(rag, input:Prompt):
    query = input.query
    role = input.role
    id = input.id
    llm = rag['llm']
    # """
    #     cek apakah melanjutkan previous chat, atau mulai baru;
    #     jika lanjut, gunakan sesi previous, jika baru gunakan id session baru
    # """
    if 'continue_history' in st.session_state:
        chat_history = st.session_state[st.session_state.id_sesi_prev]
    else:
        chat_history = st.session_state[f"chat_history_{st.session_state.session_id}"]     
    if rag is None:
        return "error", 0  
    else:
            start_time = time.time()
            respon = ""
            
            logger.debug(f"len : {len(chat_history)} | {chat_history}")
            # """"
            #     mendapatkan dokumen yang relevan sebagai context;
            #     ubah data menjadi string untuk di cetak sebagai sumber rujukan dokumen, 
            #     untuk di tampilkan di UI.
            # """
            doc_retrieve = rag['retriever'].get_relevant_documents(query)
            sumber_dc = ""
            list_doc = []
            for i in doc_retrieve:
                sumber_dc += f"{i.page_content}\n"
                list_doc.append(i.page_content)
            
            #############################################
            #       FILTER  KE 2                        #
            #############################################
            # """
            #     lakukan filter terhadap dokumen yang telah 
            #     diambil untuk diekstrak kembali kalimat,
            #     yang sesuai dengan query pengguna.
            # """
            #model embedding
            
            full_hist = ""
            for i in chat_history:
                full_hist += str(i)
            
            embed = rag['embed']    
            doc_filtered = FAISS.from_texts(list_doc, embed)
            vector_filter_retrieve = doc_filtered.as_retriever(search_type="similarity",
                                            search_kwargs={'k': 3})
            
            bm25 = BM25Retriever.from_texts(list_doc)
            bm25.k = 4
            retrievers = [
            # RunnableLambda(lambda q: hyde_retriever.get_relevant_documents(q)),  
            bm25,  
            vector_filter_retrieve
            ]
            ensemble_retrieve = EnsembleRetriever(retrievers=retrievers, weights=[0.3,0.7])
            
            final_doc = ensemble_retrieve.get_relevant_documents(query)
            
            final_sumber_doc = ""
            count = 0
            
            list_final_doc = []
            for i in final_doc:
                # pre_word = str(i.page_content).replace('•', '\n')
                pre_word = str(i.page_content).replace('', '\n')
                formatted_text_1 = re.sub(r'(\d+\.\d+)', r'\n\1', pre_word)
                formatted_text_1 = re.sub(r'(\d+\.\d+\.\d+)', r'\n\1', formatted_text_1)
                formatted_text_2 = re.sub(r'(\d+\.\d+\.\d+\.\d+)', r'\n\1', formatted_text_1)
                formatted_text = re.sub(r'(\d+\.\d+\.\d+\.\d+.\d+)', r'\n\1', formatted_text_2)
                count += 1                    
                final_sumber_doc += f"index {count}:\n\n{formatted_text} \n\n"
                list_final_doc.append(formatted_text)
                
            logger.debug(final_doc)
            ########################################################
            #                  FIND WORD                           #
            ########################################################
            # doc_filtered = FAISS.from_texts(list_final_doc, embed)
            # doc_filtered.k = 5
            # fix_ret = doc_filtered.max_marginal_relevance_search(query, lambda_mult=0.25)
            # for res in fix_ret:
            #     count +=1
            #     # print(f"* [SIM={score:3f}] {res.page_content} [{res.metadata}]")
            #     final_sumber_doc += f"index {count}:\n\n{res.page_content} \n\n"
            
            
            
            #re-rank document
            # doc_filtered = FAISS.from_texts(list_final_doc, embed)
            # vector_filter_retrieve = doc_filtered.as_retriever(search_type="similarity",
            #                                 search_kwargs={'k': 3})
            
            # bm25 = BM25Retriever.from_texts(list_final_doc)
            # bm25.k = 3
            # retrievers = [
            # # RunnableLambda(lambda q: hyde_retriever.get_relevant_documents(q)),  
            # bm25,  
            # vector_filter_retrieve
            # ]
            # ensemble_retrieve = EnsembleRetriever(retrievers=retrievers, weights=[0.3,0.7])
            
            # final_doc = ensemble_retrieve.get_relevant_documents(query)
            
            
            
            # compressor = FlashrankRerank()
            # logger.debug("sudah flash rank")
            # compression_retriever = ContextualCompressionRetriever(
            #     base_compressor=compressor,
            #     base_retriever=ensemble_retrieve
            # )
            
            
            # ranked_docs = compression_retriever.get_relevant_documents(query)
            # final_sumber_doc = ""
            # count = 0
            # for i in ranked_docs:
            #     # pre_word = str(i.page_content).replace('•', '\n')
            #     pre_word = str(i.page_content).replace('', '\n')
            #     count += 1                    
            #     # post_word = re.sub(r'\d+\.\d+\.\d+', '\n', pre_word)
            #     # final_sumber_doc += f"{pre_word}\n\n"
            #     final_sumber_doc += f"index {count}:\n\n{pre_word} \n\n"
            #     # list_final_doc.append(pre_word)
            
            ###################################################################
            #      mencari history pertanyaan yang relevan untuk fine-tuning  #
            ###################################################################
            doc_fallback = None
            source_fallback = ""
            if rag['retriever_feed'] is not None:
                retrieve_fallback = rag['retriever_feed']
                doc_fallback = retrieve_fallback.get_relevant_documents(query)
                for i in doc_fallback:
                    source_fallback += str(i.page_content)
            
            # """
            #     kirim context beserta query ke llm
            # """ 
            ##########################################################
            #          generate token-by-token response             #
            #########################################################
            
           
            respon = generate_stream(templateSystem + "\n" +
                                     final_sumber_doc + "\n" +
                                     templateContext + "\n" +
                                     full_hist + "\n" +
                                     templateFallback + "\n" +
                                     source_fallback + "\n" +
                                     "###question\n" + query,
                                     llm)
         
            
            # ai_response = get_str_stream(respon)
            # respon = stream_response(final_sumber_doc + "\n" + query, rag['rag_user'])
            #################################################################
            ################################################################
            
            # respon = rag['rag_user'].invoke(
            #             {
                            
            #                 "question": final_sumber_doc + "\n" + query,
            #                 "chat_history": chat_history,
                            
            #             }
            #         )
                     
            if len(chat_history) >= 10:
                    chat_history.pop(0)
            # else:
            #         # """
            #         #     tambahkan percakapan ke history model
            #         # """
     
            #         chat_history.extend(
            #                 [
            #                     f"human question : {query}",
            #                     f"your answer : {ai_m}" 
            #                 ]
            #             )
            # """
            #     hitung lama respon model 
            # """           
            response_time = time.time() - start_time
            logger.debug(f"history : {chat_history}")
            logger.debug(f"len {len(doc_retrieve)} | dokumen ret : {doc_retrieve[0].page_content}")
            logger.debug(f"fallback : {source_fallback}")
    return respon, doc_retrieve, final_sumber_doc, response_time
    # return respon.content, response_time
    
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import TextSplitter
from typing import (
    Iterable,
    List,
)
from langchain_core.documents import BaseDocumentTransformer, Document


def split_docs(_documents, _chunk_size, _chunk_overlap, separator=None):
        """
        kode untuk chunk (memotong dokumen menjadi bagian-bagian yang lebih kecil)
        Parameters:
            documents (List[document]): argument diisi dengan document yang sudah dimuat
            chunk_size (int) : size pembagian data
            chunk_overlap (int): besar data yang diskip (per-kata)
        Returns:
            chunks (List[document]): objek hasil split dokumen    
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=_chunk_size, 
            separators=separator,
            chunk_overlap=_chunk_overlap
        )
        chunks = text_splitter.split_documents(documents=_documents)
        return chunks
    

class EOSSplitter(TextSplitter):
     """
        Merupakan Class untuk chunking dokumen berdasarkan karakter tag `<EOS>`, 
        yang telah disematkan pada dokumen.
     """
    
     def split_text(self, text: str) -> List[str]:
        """Implementasi untuk memecah teks berdasarkan marker <EOS>."""
        # Pisahkan teks berdasarkan karakter <EOS>
        return text.split('<EOS>')
    
     def split_documents(self, documents: Iterable[Document]) -> List[Document]:
        """Memisahkan dokumen ke dalam chunk berdasarkan <EOS> marker."""
        split_docs = []
        
        # Loop untuk setiap dokumen
        for doc in documents:
            # Pisahkan teks dokumen berdasarkan <EOS>
            chunks = self.split_text(doc.page_content)
            
            # Buat dokumen baru dari setiap chunk yang dihasilkan
            for chunk in chunks:
                chunk = chunk.strip()  # Menghilangkan spasi kosong
                if chunk:  # Hanya tambahkan chunk yang tidak kosong
                    split_docs.append(Document(page_content=chunk, metadata=doc.metadata))
        
        return split_docs   

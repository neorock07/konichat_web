from dataclasses import dataclass

@dataclass
class SessionModel:
    id_session:str
    tanggal:str
    title:str
    id_user:int
    
    # "id_session" : "sekalilirikoksajalah",
    # "tanggal" : "2024-09-03",
    # "title" : "namakubento",
    # "id_user" : 1
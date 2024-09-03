from dataclasses import dataclass

@dataclass
class Prompt:
    query:str
    role:int
    id:int

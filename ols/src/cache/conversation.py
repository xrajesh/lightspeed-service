"""A model for defining single conversation ."""

from typing import NamedTuple 

class Conversation(NamedTuple): 
    user: str
    assistant: str
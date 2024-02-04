"""A model for defining single conversation ."""

from typing import NamedTuple 

class Conversation(NamedTuple): 
    userMessage: str
    assistantMessage: str
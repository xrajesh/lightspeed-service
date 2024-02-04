"""Util methods to make chat history objects."""
from  ols.src.cache.conversation import Conversation
from llama_index.llms import ChatMessage, MessageRole
from typing import List

def get_llama_index_chat_history(conversations: List[Conversation]) -> List[ChatMessage]:
    """Produces chat history object using list of Conversions"""
    chat_history=[]
    if conversations is None or len(conversations) <1:
        return chat_history    
    for conversation in conversations:
        user_chat_message=ChatMessage(role=MessageRole.USER,content=conversation.userMessage)
        chat_history.append(user_chat_message)
        assistant_chat_message=ChatMessage(role=MessageRole.ASSISTANT,content=conversation.assistantMessage)
        chat_history.append(assistant_chat_message)
    return chat_history    



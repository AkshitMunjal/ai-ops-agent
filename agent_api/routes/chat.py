from fastapi import APIRouter

from agent_api.schemas import ChatAnswer, ChatQuestion
from chat.assistant import answer_question

router = APIRouter()


# A plain "def" on purpose: FastAPI runs it in its own thread,
# so the assistant can start its own event loop.
@router.post("/chat", response_model=ChatAnswer)
def ask_chat(chat_question: ChatQuestion):
    history = [message.model_dump() for message in chat_question.history]
    result = answer_question(chat_question.question, history)
    return ChatAnswer(**result)

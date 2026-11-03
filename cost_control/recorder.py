from agent_api.database import open_session
from cost_control.models import LlmUsage


def record_usage(model_name, usage):
    usage_row = LlmUsage(
        model=model_name,
        prompt_tokens=usage.get("prompt_tokens") or 0,
        completion_tokens=usage.get("completion_tokens") or 0,
        cost=usage.get("cost") or 0.0,
    )

    with open_session() as database_session:
        database_session.add(usage_row)
        database_session.commit()
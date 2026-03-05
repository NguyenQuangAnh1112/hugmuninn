from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_task: Optional[str]
    search_results: Optional[str]
    discord_sent: Optional[bool]
    errorL: Optional[str]

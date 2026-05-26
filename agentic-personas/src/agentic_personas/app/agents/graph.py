from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph

from agentic_personas.llm_client import OpenAICompatibleClient
from agentic_personas.profiles import PersonaProfile

from ..tools.prompting import build_persona_system_prompt


class PersonaGraphState(TypedDict):
    question: str
    responses: dict[str, str]


def _node_name(profile: PersonaProfile) -> str:
    return f"persona_{profile.cluster_id}"


def build_persona_graph(
    profiles: list[PersonaProfile],
    llm_client: OpenAICompatibleClient,
):
    graph = StateGraph(PersonaGraphState)

    def make_persona_node(profile: PersonaProfile):
        system_prompt = build_persona_system_prompt(profile)

        def persona_node(state: PersonaGraphState) -> PersonaGraphState:
            answer = llm_client.ask(system_prompt=system_prompt, user_message=state["question"])
            updated = dict(state["responses"])
            updated[profile.segment_name] = answer
            return {"question": state["question"], "responses": updated}

        return persona_node

    for profile in profiles:
        graph.add_node(_node_name(profile), make_persona_node(profile))

    def aggregate(state: PersonaGraphState) -> PersonaGraphState:
        return state

    graph.add_node("aggregate", aggregate)

    # Entry goes through the first persona, then fan-out sequentially across personas,
    # ending in a dedicated aggregation step for explicit architecture.
    ordered_nodes = [_node_name(profile) for profile in profiles]
    graph.set_entry_point(ordered_nodes[0])
    for idx, node in enumerate(ordered_nodes):
        if idx + 1 < len(ordered_nodes):
            graph.add_edge(node, ordered_nodes[idx + 1])
        else:
            graph.add_edge(node, "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()


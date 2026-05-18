"""Puzzle type: conversation.

Renders a series of named-speaker exchanges followed by a question.
The player reads the exchange and submits a text answer.

Required content keys:
  exchanges  — list of {speaker: str, text: str}
  question   — str
"""
from puzzle_types.base import PuzzleTypeGenerator


class ConversationGenerator(PuzzleTypeGenerator):
    type_id = "conversation"

    def validate_definition(self, defn: dict) -> None:
        content = defn.get("content", {})

        exchanges = content.get("exchanges")
        if not isinstance(exchanges, list) or len(exchanges) == 0:
            raise ValueError("conversation: 'content.exchanges' must be a non-empty list")

        for i, ex in enumerate(exchanges):
            if not isinstance(ex.get("speaker"), str) or not ex["speaker"].strip():
                raise ValueError(f"conversation: exchange[{i}] missing 'speaker'")
            if not isinstance(ex.get("text"), str) or not ex["text"].strip():
                raise ValueError(f"conversation: exchange[{i}] missing 'text'")

        if not isinstance(content.get("question"), str) or not content["question"].strip():
            raise ValueError("conversation: 'content.question' must be a non-empty string")

    def required_generators(self) -> list[str]:
        return ["rand_int", "rand_choice", "identity", "caesar_encode"]

"""Base class for puzzle type implementations."""
from abc import ABC, abstractmethod


class PuzzleTypeGenerator(ABC):
    """Implement one subclass per puzzle type.

    The subclass is responsible for:
    - Validating that a definition's `content` block is well-formed for this type
    - Declaring which generator function names the type depends on

    The HTML template lives at templates/puzzle-types/<type_id>.html and is
    rendered by the server; it is not produced by this class.
    """

    type_id: str

    @abstractmethod
    def validate_definition(self, defn: dict) -> None:
        """Raise ValueError with a clear message if the definition is malformed."""

    @abstractmethod
    def required_generators(self) -> list[str]:
        """Names of generator functions this type depends on.

        The server checks these are registered before attempting to serve
        any puzzle of this type.
        """

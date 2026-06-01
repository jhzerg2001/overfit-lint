"""AnalysisContext: everything a rule needs about one source file."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field

from ..config import RuleConfig


@dataclass
class AnalysisContext:
    """Parsed view of a single file, handed to every rule.

    A rule receives this read-only context and returns findings. The file is
    parsed exactly once (by the runner) and shared across all rules.
    """

    path: str
    source: str
    tree: ast.AST
    lines: list[str]
    data_days: int | None = None
    config: RuleConfig = field(default_factory=RuleConfig)

    @classmethod
    def from_source(
        cls,
        source: str,
        path: str = "<string>",
        data_days: int | None = None,
        config: RuleConfig | None = None,
    ) -> "AnalysisContext":
        """Parse ``source`` into a context. Raises ``SyntaxError`` on bad input."""
        tree = ast.parse(source, filename=path)
        return cls(
            path=path,
            source=source,
            tree=tree,
            lines=source.splitlines(),
            data_days=data_days,
            config=config or RuleConfig(),
        )

    def snippet(self, node_or_line: ast.AST | int) -> str:
        """Return the stripped source line for an AST node or a 1-based line no."""
        if isinstance(node_or_line, int):
            lineno = node_or_line
        else:
            lineno = getattr(node_or_line, "lineno", 0)
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1].strip()
        return ""

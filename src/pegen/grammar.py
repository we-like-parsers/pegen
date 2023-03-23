from __future__ import annotations

from typing import (
    AbstractSet,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)


class GrammarError(Exception):
    pass


class GrammarVisitor:
    def visit(self, node: Any, *args: Any, **kwargs: Any) -> Any:
        """Visit a node."""
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node, *args, **kwargs)

    def generic_visit(self, node: Iterable[Any], *args: Any, **kwargs: Any) -> Any:
        """Called if no explicit visitor function exists for a node."""
        for value in node:
            if isinstance(value, list):
                for item in value:
                    self.visit(item, *args, **kwargs)
            else:
                self.visit(value, *args, **kwargs)


class NullableVisitor(GrammarVisitor):
    def __init__(self, rules: Dict[str, Rule]) -> None:
        self.rules = rules
        self.visited: Set[Any] = set()
        self.nullables: Set[Union[Rule, NamedItem]] = set()

    def visit_Rule(self, rule: Rule) -> bool:
        if rule in self.visited:
            return False
        self.visited.add(rule)
        if self.visit(rule.rhs):
            self.nullables.add(rule)
        return rule in self.nullables

    def visit_Rhs(self, rhs: Rhs) -> bool:
        for alt in rhs.alts:
            if self.visit(alt):
                return True
        return False

    def visit_Alt(self, alt: Alt) -> bool:
        for item in alt.items:
            if not self.visit(item):
                return False
        return True

    def visit_Forced(self, force: Forced) -> bool:
        return True

    def visit_LookAhead(self, lookahead: Lookahead) -> bool:
        return True

    def visit_Opt(self, opt: Opt) -> bool:
        return True

    def visit_Repeat0(self, repeat: Repeat0) -> bool:
        return True

    def visit_Repeat1(self, repeat: Repeat1) -> bool:
        return False

    def visit_Gather(self, gather: Gather) -> bool:
        return False

    def visit_Cut(self, cut: Cut) -> bool:
        return False

    def visit_Group(self, group: Group) -> bool:
        return self.visit(group.rhs)

    def visit_NamedItem(self, item: NamedItem) -> bool:
        if self.visit(item.item):
            self.nullables.add(item)
        return item in self.nullables

    def visit_NameLeaf(self, node: NameLeaf) -> bool:
        if node.value in self.rules:
            return self.visit(self.rules[node.value])
        # Token or unknown; never empty.
        return False

    def visit_StringLeaf(self, node: StringLeaf) -> bool:
        # The string token '' is considered empty.
        return not node.value


class Grammar:
    def __init__(self, rules: Iterable[Rule], metas: Iterable[Tuple[str, Optional[str]]]):
        self.rules = {rule.name: rule for rule in rules}
        self.metas = dict(metas)
        self.nullables = self.compute_nullables()

    def __str__(self) -> str:
        return "\n".join(str(rule) for name, rule in self.rules.items())

    def __repr__(self) -> str:
        lines = ["Grammar("]
        lines.append("  [")
        for rule in self.rules.values():
            lines.append(f"    {repr(rule)},")
        lines.append("  ],")
        lines.append("  {repr(list(self.metas.items()))}")
        lines.append(")")
        return "\n".join(lines)

    def __iter__(self) -> Iterator[Rule]:
        yield from self.rules.values()

    def compute_nullables(self):
        """Compute which rules in a grammar are nullable.

        Thanks to TatSu (tatsu/leftrec.py) for inspiration."""
        nullable_visitor = NullableVisitor(self.rules)
        for rule in self.rules.values():
            nullable_visitor.visit(rule)

        return nullable_visitor.nullables


# Global flag whether we want actions in __str__() -- default off.
SIMPLE_STR = True


class Rule:
    def __init__(self, name: str, type: Optional[str], rhs: Rhs, memo: Optional[object] = None):
        self.name = name
        self.type = type
        self.rhs = rhs
        self.memo = bool(memo)
        self.left_recursive = False
        self.leader = False

    def is_loop(self) -> bool:
        return self.name.startswith("_loop")

    def is_gather(self) -> bool:
        return self.name.startswith("_gather")

    def __str__(self) -> str:
        if SIMPLE_STR or self.type is None:
            res = f"{self.name}: {self.rhs}"
        else:
            res = f"{self.name}[{self.type}]: {self.rhs}"
        if len(res) < 88:
            return res
        lines = [res.split(":")[0] + ":"]
        lines += [f"    | {alt}" for alt in self.rhs.alts]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Rule({self.name!r}, {self.type!r}, {self.rhs!r})"

    def __iter__(self) -> Iterator[Rhs]:
        yield self.rhs

    def flatten(self) -> Rhs:
        # If it's a single parenthesized group, flatten it.
        rhs = self.rhs
        if (
            not self.is_loop()
            and len(rhs.alts) == 1
            and len(rhs.alts[0].items) == 1
            and isinstance(rhs.alts[0].items[0].item, Group)
        ):
            rhs = rhs.alts[0].items[0].item.rhs
        return rhs


class Leaf:
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return self.value

    def __iter__(self) -> Iterable[str]:
        if False:
            yield


class NameLeaf(Leaf):
    """The value is the name."""

    def __str__(self) -> str:
        if self.value == "ENDMARKER":
            return "$"
        return super().__str__()

    def __repr__(self) -> str:
        return f"NameLeaf({self.value!r})"


class StringLeaf(Leaf):
    """The value is a string literal, including quotes."""

    def __repr__(self) -> str:
        return f"StringLeaf({self.value!r})"


class Rhs:
    def __init__(self, alts: List[Alt]):
        self.alts = alts
        self.memo: Optional[Tuple[Optional[str], str]] = None

    def __str__(self) -> str:
        return " | ".join(str(alt) for alt in self.alts)

    def __repr__(self) -> str:
        return f"Rhs({self.alts!r})"

    def __iter__(self) -> Iterator[List[Alt]]:
        yield self.alts

    @property
    def can_be_inlined(self) -> bool:
        if len(self.alts) != 1 or len(self.alts[0].items) != 1:
            return False
        # If the alternative has an action we cannot inline
        if getattr(self.alts[0], "action", None) is not None:
            return False
        return True


class Alt:
    def __init__(self, items: List[NamedItem], *, icut: int = -1, action: Optional[str] = None):
        self.items = items
        self.icut = icut
        self.action = action

    def __str__(self) -> str:
        core = " ".join(str(item) for item in self.items)
        if not SIMPLE_STR and self.action:
            return f"{core} {{ {self.action} }}"
        else:
            return core

    def __repr__(self) -> str:
        args = [repr(self.items)]
        if self.icut >= 0:
            args.append(f"icut={self.icut}")
        if self.action:
            args.append(f"action={self.action!r}")
        return f"Alt({', '.join(args)})"

    def __iter__(self) -> Iterator[List[NamedItem]]:
        yield self.items


class NamedItem:
    def __init__(self, name: Optional[str], item: Item, type: Optional[str] = None):
        self.name = name
        self.item = item
        self.type = type

    def __str__(self) -> str:
        if not SIMPLE_STR and self.name:
            return f"{self.name}={self.item}"
        else:
            return str(self.item)

    def __repr__(self) -> str:
        return f"NamedItem({self.name!r}, {self.item!r})"

    def __iter__(self) -> Iterator[Item]:
        yield self.item


class Forced:
    def __init__(self, node: Plain):
        self.node = node

    def __str__(self) -> str:
        return f"&&{self.node}"

    def __iter__(self) -> Iterator[Plain]:
        yield self.node


class Lookahead:
    def __init__(self, node: Plain, sign: str):
        self.node = node
        self.sign = sign

    def __str__(self) -> str:
        return f"{self.sign}{self.node}"

    def __iter__(self) -> Iterator[Plain]:
        yield self.node


class PositiveLookahead(Lookahead):
    def __init__(self, node: Plain):
        super().__init__(node, "&")

    def __repr__(self) -> str:
        return f"PositiveLookahead({self.node!r})"


class NegativeLookahead(Lookahead):
    def __init__(self, node: Plain):
        super().__init__(node, "!")

    def __repr__(self) -> str:
        return f"NegativeLookahead({self.node!r})"


class Opt:
    def __init__(self, node: Item):
        self.node = node

    def __str__(self) -> str:
        s = str(self.node)
        # TODO: Decide whether to use [X] or X? based on type of X
        if " " in s:
            return f"[{s}]"
        else:
            return f"{s}?"

    def __repr__(self) -> str:
        return f"Opt({self.node!r})"

    def __iter__(self) -> Iterator[Item]:
        yield self.node


class Repeat:
    """Shared base class for x* and x+."""

    def __init__(self, node: Plain):
        self.node = node
        self.memo: Optional[Tuple[Optional[str], str]] = None

    def __iter__(self) -> Iterator[Plain]:
        yield self.node


class Repeat0(Repeat):
    def __str__(self) -> str:
        s = str(self.node)
        # TODO: Decide whether to use (X)* or X* based on type of X
        if " " in s:
            return f"({s})*"
        else:
            return f"{s}*"

    def __repr__(self) -> str:
        return f"Repeat0({self.node!r})"


class Repeat1(Repeat):
    def __str__(self) -> str:
        s = str(self.node)
        # TODO: Decide whether to use (X)+ or X+ based on type of X
        if " " in s:
            return f"({s})+"
        else:
            return f"{s}+"

    def __repr__(self) -> str:
        return f"Repeat1({self.node!r})"


class Gather(Repeat):
    def __init__(self, separator: Plain, node: Plain):
        self.separator = separator
        self.node = node

    def __str__(self) -> str:
        return f"{self.separator!s}.{self.node!s}+"

    def __repr__(self) -> str:
        return f"Gather({self.separator!r}, {self.node!r})"


class Group:
    def __init__(self, rhs: Rhs):
        self.rhs = rhs

    def __str__(self) -> str:
        return f"({self.rhs})"

    def __repr__(self) -> str:
        return f"Group({self.rhs!r})"

    def __iter__(self) -> Iterator[Rhs]:
        yield self.rhs


class Cut:
    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"Cut()"

    def __str__(self) -> str:
        return f"~"

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        if False:
            yield

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cut):
            return NotImplemented
        return True

    def initial_names(self) -> AbstractSet[str]:
        return set()


Plain = Union[Leaf, Group]
Item = Union[Plain, Opt, Repeat, Forced, Lookahead, Rhs, Cut]
RuleName = Tuple[str, str]
MetaTuple = Tuple[str, Optional[str]]
MetaList = List[MetaTuple]
RuleList = List[Rule]
NamedItemList = List[NamedItem]
LookaheadOrCut = Union[Lookahead, Cut]

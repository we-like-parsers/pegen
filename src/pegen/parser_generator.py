import contextlib
from abc import abstractmethod
from typing import Any, IO, AbstractSet, Dict, Iterator, List, Optional, Set, Text, Tuple

from pegen import sccutils
from pegen.grammar import (
    Alt,
    Cut,
    Forced,
    Gather,
    Grammar,
    GrammarError,
    GrammarVisitor,
    Group,
    Lookahead,
    NamedItem,
    NameLeaf,
    Opt,
    Plain,
    Repeat0,
    Repeat1,
    Rhs,
    Rule,
    StringLeaf,
)


class RuleCheckingVisitor(GrammarVisitor):
    def __init__(self, rules: Dict[str, Rule], tokens: Set[str]):
        self.rules = rules
        self.tokens = tokens

    def visit_NameLeaf(self, node: NameLeaf) -> None:
        if node.value not in self.rules and node.value not in self.tokens:
            # TODO: Add line/col info to (leaf) nodes
            raise GrammarError(f"Dangling reference to rule {node.value!r}")

    def visit_NamedItem(self, node: NamedItem) -> None:
        if node.name and node.name.startswith("_"):
            raise GrammarError(f"Variable names cannot start with underscore: '{node.name}'")
        self.visit(node.item)


class ParserGenerator:
    callmakervisitor: GrammarVisitor

    def __init__(self, grammar: Grammar, tokens: Set[str], file: Optional[IO[Text]]):
        self.grammar = grammar
        self.tokens = tokens
        self.rules = grammar.rules
        self.validate_rule_names()
        if "trailer" not in grammar.metas and "start" not in self.rules:
            raise GrammarError("Grammar without a trailer must have a 'start' rule")
        checker = RuleCheckingVisitor(self.rules, self.tokens)
        for rule in self.rules.values():
            checker.visit(rule)
        self.file = file
        self.level = 0
        compute_nullables(self.rules)
        self.first_graph, self.first_sccs = compute_left_recursives(self.rules)
        self.todo = self.rules.copy()  # Rules to generate
        self.counter = 0  # For name_rule()/name_loop()
        self.all_rules: Dict[str, Rule] = {}  # Rules + temporal rules
        self._local_variable_stack: List[List[str]] = []

    def validate_rule_names(self) -> None:
        for rule in self.rules:
            if rule.startswith("_"):
                raise GrammarError(f"Rule names cannot start with underscore: '{rule}'")

    @contextlib.contextmanager
    def local_variable_context(self) -> Iterator[None]:
        self._local_variable_stack.append([])
        yield
        self._local_variable_stack.pop()

    @property
    def local_variable_names(self) -> List[str]:
        return self._local_variable_stack[-1]

    @abstractmethod
    def generate(self, filename: str) -> None:
        raise NotImplementedError

    @contextlib.contextmanager
    def indent(self) -> Iterator[None]:
        self.level += 1
        try:
            yield
        finally:
            self.level -= 1

    def print(self, *args: object) -> None:
        if not args:
            print(file=self.file)
        else:
            print("    " * self.level, end="", file=self.file)
            print(*args, file=self.file)

    def printblock(self, lines: str) -> None:
        for line in lines.splitlines():
            self.print(line)

    def collect_todo(self) -> None:
        done: Set[str] = set()
        while True:
            alltodo = list(self.todo)
            self.all_rules.update(self.todo)
            todo = [i for i in alltodo if i not in done]
            if not todo:
                break
            for rulename in todo:
                self.todo[rulename].collect_todo(self)
            done = set(alltodo)

    def artifical_rule_from_rhs(self, rhs: Rhs) -> str:
        self.counter += 1
        name = f"_tmp_{self.counter}"  # TODO: Pick a nicer name.
        self.todo[name] = Rule(name, None, rhs)
        return name

    def artificial_rule_from_repeat(self, node: Plain, is_repeat1: bool) -> str:
        self.counter += 1
        if is_repeat1:
            prefix = "_loop1_"
        else:
            prefix = "_loop0_"
        name = f"{prefix}{self.counter}"  # TODO: It's ugly to signal via the name.
        self.todo[name] = Rule(name, None, Rhs([Alt([NamedItem(None, node)])]))
        return name

    def artifical_rule_from_gather(self, node: Gather) -> str:
        self.counter += 1
        name = f"_gather_{self.counter}"
        self.counter += 1
        extra_function_name = f"_loop0_{self.counter}"
        extra_function_alt = Alt(
            [NamedItem(None, node.separator), NamedItem("elem", node.node)],
            action="elem",
        )
        self.todo[extra_function_name] = Rule(
            extra_function_name,
            None,
            Rhs([extra_function_alt]),
        )
        alt = Alt(
            [NamedItem("elem", node.node), NamedItem("seq", NameLeaf(extra_function_name))],
        )
        self.todo[name] = Rule(
            name,
            None,
            Rhs([alt]),
        )
        return name

    def dedupe(self, name: str) -> str:
        origname = name
        counter = 0
        while name in self.local_variable_names:
            counter += 1
            name = f"{origname}_{counter}"
        self.local_variable_names.append(name)
        return name


class NullableVisitor(GrammarVisitor):
    def __init__(self, rules: Dict[str, Rule]) -> None:
        self.rules = rules
        self.visited: Set[Any] = set()

    def visit_Rule(self, rule: Rule) -> bool:
        if rule in self.visited:
            return False
        self.visited.add(rule)
        if self.visit(rule.rhs):
            rule.nullable = True
        return rule.nullable

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
            item.nullable = True
        return item.nullable

    def visit_NameLeaf(self, node: NameLeaf) -> bool:
        if node.value in self.rules:
            return self.visit(self.rules[node.value])
        # Token or unknown; never empty.
        return False

    def visit_StringLeaf(self, node: StringLeaf) -> bool:
        # The string token '' is considered empty.
        return not node.value


def compute_nullables(rules: Dict[str, Rule]) -> None:
    """Compute which rules in a grammar are nullable.

    Thanks to TatSu (tatsu/leftrec.py) for inspiration.
    """
    nullable_visitor = NullableVisitor(rules)
    for rule in rules.values():
        nullable_visitor.visit(rule)


def compute_left_recursives(
    rules: Dict[str, Rule]
) -> Tuple[Dict[str, AbstractSet[str]], List[AbstractSet[str]]]:
    graph = make_first_graph(rules)
    sccs = list(sccutils.strongly_connected_components(graph.keys(), graph))
    for scc in sccs:
        if len(scc) > 1:
            for name in scc:
                rules[name].left_recursive = True
            # Try to find a leader such that all cycles go through it.
            leaders = set(scc)
            for start in scc:
                for cycle in sccutils.find_cycles_in_scc(graph, scc, start):
                    # print("Cycle:", " -> ".join(cycle))
                    leaders -= scc - set(cycle)
                    if not leaders:
                        raise ValueError(
                            f"SCC {scc} has no leadership candidate (no element is included in all cycles)"
                        )
            # print("Leaders:", leaders)
            leader = min(leaders)  # Pick an arbitrary leader from the candidates.
            rules[leader].leader = True
        else:
            name = min(scc)  # The only element.
            if name in graph[name]:
                rules[name].left_recursive = True
                rules[name].leader = True
    return graph, sccs


def make_first_graph(rules: Dict[str, Rule]) -> Dict[str, AbstractSet[str]]:
    """Compute the graph of left-invocations.

    There's an edge from A to B if A may invoke B at its initial
    position.

    Note that this requires the nullable flags to have been computed.
    """
    graph = {}
    vertices: Set[str] = set()
    for rulename, rhs in rules.items():
        graph[rulename] = names = rhs.initial_names()
        vertices |= names
    for vertex in vertices:
        graph.setdefault(vertex, set())
    return graph

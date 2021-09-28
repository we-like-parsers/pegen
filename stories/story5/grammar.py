"""Parser for the grammar file."""

from token import DEDENT, INDENT, NAME, NEWLINE, STRING, ENDMARKER

from story5.parser import Parser

class Rule:

    def __init__(self, name, alts):
        self.name = name
        self.alts = alts

    def __repr__(self):
        return f"Rule({self.name!r}, {self.alts})"

    def __eq__(self, other):
        if not isinstance(other, Rule):
            return NotImplemented
        return self.name == other.name and self.alts == other.alts


class Alt:

    def __init__(self, items, action=None):
        self.items = items
        self.action = action

    def __repr__(self):
        if self.action:
            return f"Alt({self.items!r}, {self.action!r})"
        else:
            return f"Alt({self.items!r})"

    def __str__(self):
        items = " ".join(self.items)
        if self.action:
            return f"{items} {{ {self.action} }}"
        else:
            return items

    def __eq__(self, other):
        if not isinstance(other, Alt):
            return NotImplemented
        return self.items == other.items and self.action == other.action


class GrammarParser(Parser):

    def grammar(self):
        pos = self.mark()
        if rule := self.rule():
            rules = [rule]
            while rule := self.rule():
                rules.append(rule)
            if self.expect(ENDMARKER):
                return rules
        self.reset(pos)
        return None

    def rule(self):
        pos = self.mark()
        if (name := self.expect(NAME)) and self.expect(":"):
            if alts := self.alts_newline():
                pass
            elif self.expect(NEWLINE):
                alts = []
            else:
                self.reset(pos)
                return None
            if alts1 := self.indented_alts():
                alts.extend(alts1)
            if alts:
                return Rule(name.string, alts)
        self.reset(pos)
        return None

    def indented_alts(self):
        pos = self.mark()
        if self.expect(INDENT):
            alts = []
            while alts1 := self.bar_alts_newline():
                alts.extend(alts1)
            if self.expect(DEDENT):
                return alts
        self.reset(pos)
        return None

    def bar_alts_newline(self):
        pos = self.mark()
        if self.expect("|") and (alts := self.alts_newline()):
            return alts
        self.reset(pos)
        return None

    def alts_newline(self):
        pos = self.mark()
        if (alts := self.alts()) and self.expect(NEWLINE):
            return alts
        self.reset(pos)
        return None

    def alts(self):
        pos = self.mark()
        if alt := self.alternative():
            alts = [alt]
            while alt := self.bar_alt():
                alts.append(alt)
            return alts
        self.reset(pos)
        return None

    def bar_alt(self):
        pos = self.mark()
        if self.expect("|") and (alt := self.alternative()):
            return alt
        self.reset(pos)
        return None

    def alternative(self):
        items = []
        while item := self.item():
            items.append(item)
        if not items:
            return None
        # Look for {...}
        action = None
        pos = self.mark()
        if self.expect("{"):
            # Collect arbitrary tokens until "}" found, skipping matching {...} pairs.
            action_tokens = []
            level = 0
            while True:
                token = self.tokenizer.get_token().string
                if token == "{":
                    level += 1
                elif token == "}":
                    level -= 1
                    if level < 0:
                        break
                action_tokens.append(token)
            action = " ".join(action_tokens)
        return Alt(items, action)

    def item(self):
        if name := self.expect(NAME):
            return name.string
        if string := self.expect(STRING):
            return string.string
        return None

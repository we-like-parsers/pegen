class Tokenizer:

    def __init__(self, tokengen, vis=None):
        """Call with tokenize.generate_tokens(...)."""
        self.tokengen = tokengen
        self.vis = vis
        self.tokens = []
        self.pos = 0

    def mark(self):
        return self.pos

    def reset(self, pos):
        if pos == self.pos:
            return
        self.pos = pos
        self.report()

    def get_token(self):
        token = self.peek_token()
        self.pos += 1
        self.report()
        return token

    def peek_token(self):
        if self.pos == len(self.tokens):
            self.tokens.append(next(self.tokengen))
            self.report()
        return self.tokens[self.pos]

    def report(self):
        if self.vis is not None:
            self.vis.vis_tokens(self.tokens, self.pos)

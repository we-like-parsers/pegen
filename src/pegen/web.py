import io
import traceback

from flask import Flask, cli, render_template  # type: ignore
from flask_wtf import FlaskForm  # type: ignore
from wtforms import SubmitField, TextAreaField  # type: ignore
from wtforms.validators import DataRequired  # type: ignore

from pegen.utils import make_parser, parse_string

DEFAULT_GRAMMAR = """\
start: expr NEWLINE? ENDMARKER { expr }
expr:
      | expr '+' term { expr + term }
      | expr '-' term { expr - term}
      | term
term:
      | term '*' factor { term * factor }
      | term '/' factor { term / factor }
      | factor

factor:
       | '(' expr ')' { expr }
       | atom { int(atom.string) }
atom: NUMBER
"""

DEFAULT_SOURCE = "(1 + 2) * (3 - 6)"


app = Flask(__name__)

# Flask-WTF requires an encryption key - the string can be anything
app.config["SECRET_KEY"] = "does_not_matter"


class GrammarForm(FlaskForm):  # type: ignore
    grammar = TextAreaField("PEG GRAMMAR", validators=[DataRequired()], default=DEFAULT_GRAMMAR)
    source = TextAreaField("PROGRAM", validators=[DataRequired()], default=DEFAULT_SOURCE)
    submit = SubmitField("Parse!")


@app.route("/", methods=["GET", "POST"])
def index() -> None:
    # you must tell the variable 'form' what you named the class, above
    # 'form' is the variable name used in this template: index.html
    form = GrammarForm()
    form.grammar(class_="form-control")
    output_text = "\n"
    if form.validate_on_submit():
        grammar_source = form.grammar.data
        program_source = form.source.data
        output = io.StringIO()
        try:
            parser_class = make_parser(grammar_source)
            result = parse_string(program_source, parser_class, verbose=False)
            print(result, file=output)
        except Exception:
            traceback.print_exc(file=output)
        output_text += output.getvalue()
    return render_template("index.html", form=form, output=output_text)


if __name__ == "__main__":
    cli.show_server_banner = lambda *_: None
    app.run(debug=False)

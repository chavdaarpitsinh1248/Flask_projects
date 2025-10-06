from flask import Flask, render_template, request
import math

app = Flask(__name__)

def safe_eval(expr):
    # Replace ^ with ** for Python exponentiation and √ with sqrt
    expr = expr.replace("^", "**").replace("√", "sqrt")

    # Allowed functions
    allowed_funcs = {
        "sin": lambda x: math.sin(math.radians(x)),
        "cos": lambda x: math.cos(math.radians(x)),
        "tan": lambda x: math.tan(math.radians(x)),
        "asin": lambda x: math.degrees(math.asin(x)),
        "acos": lambda x: math.degrees(math.acos(x)),
        "atan": lambda x: math.degrees(math.atan(x)),
        "sqrt": math.sqrt,
        "log": math.log10,  # base 10
        "ln": math.log,     # natural log
    }

    # Evaluate safely
    return eval(expr, {"__builtins__": None}, allowed_funcs)

@app.route("/", methods=["GET", "POST"])
def index():
    expression = ""
    if request.method == "POST":
        expression = request.form.get("expression")
        try:
            expression = str(safe_eval(expression))
        except Exception:
            expression = "Error"
    return render_template("index.html", expression=expression)

if __name__ == "__main__":
    app.run(debug=True)

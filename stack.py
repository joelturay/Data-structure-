
import os
import sys

OPERATORS = "+-*/"


# ---------------------------------------------------------------------------
# Stack
# ---------------------------------------------------------------------------
class Stack:
    """A stack: the last item pushed is the first item popped."""

    def __init__(self):
        self.items = []

    def push(self, item):
        """Put an item on top of the stack."""
        self.items.append(item)

    def pop(self):
        """Remove and return the top item."""
        if self.is_empty():
            raise IndexError("Cannot pop from an empty stack")
        return self.items.pop()

    def peek(self):
        """Look at the top item without removing it."""
        if self.is_empty():
            raise IndexError("Cannot peek at an empty stack")
        return self.items[-1]

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)

    def to_list(self):
        """Return the items from bottom to top (does not change the stack)."""
        return list(self.items)


def is_operator(token):
    return isinstance(token, str) and token in OPERATORS


def pretty(number):
    """Show 17.0 as 17 and 2.5 as 2.5."""
    if number == int(number):
        return str(int(number))
    return f"{number:.4f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------
# Step 1: tokens
# ---------------------------------------------------------------------------
def tokenize(text):
    """Turn the text into a list of numbers (floats) and symbols (strings)."""
    tokens = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == " ":
            i += 1
        elif ch.isdigit() or ch == ".":
            start = i
            while i < len(text) and (text[i].isdigit() or text[i] == "."):
                i += 1
            piece = text[start:i]
            try:
                tokens.append(float(piece))
            except ValueError:
                raise ValueError(f"'{piece}' is not a valid number")
        elif ch in OPERATORS or ch in "()":
            tokens.append(ch)
            i += 1
        else:
            raise ValueError(f"Unknown character '{ch}' - only numbers, + - * / and brackets are allowed")
    return tokens


# ---------------------------------------------------------------------------
# Step 2: check the brackets match
# ---------------------------------------------------------------------------
def check_brackets(tokens):
    stack = Stack()
    for token in tokens:
        if token == "(":
            stack.push(token)
        elif token == ")":
            if stack.is_empty():
                raise ValueError("Extra closing bracket ')' - there is no '(' to match it")
            stack.pop()
    if not stack.is_empty():
        raise ValueError("Missing closing bracket ')' - an opening bracket '(' was never closed")


# ---------------------------------------------------------------------------
# Step 4: solve an expression that has NO brackets
# ---------------------------------------------------------------------------
def join_signs(tokens):
    """
    Join a sign to its number when it is a sign and not a calculation.
    Examples:  - 5 + 2  ->  -5 + 2      and      9 - - 4  ->  9 - -4
    """
    result = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        sign_position = len(result) == 0 or is_operator(result[-1])
        if token in ("+", "-") and sign_position:
            if i + 1 < len(tokens) and isinstance(tokens[i + 1], float):
                value = tokens[i + 1]
                result.append(-value if token == "-" else value)
                i += 2
                continue
            raise ValueError(f"The sign '{token}' must be followed by a number")
        result.append(token)
        i += 1
    return result


def check_pattern(tokens):
    """The tokens must look like: number operator number operator number ..."""
    if len(tokens) == 0:
        raise ValueError("The expression is empty")
    for position, token in enumerate(tokens):
        if position % 2 == 0 and is_operator(token):
            raise ValueError(f"Operator '{token}' is in the wrong place - a number was expected here")
        if position % 2 == 1 and not is_operator(token):
            raise ValueError("Two numbers are next to each other - an operator is missing between them")
    if is_operator(tokens[-1]):
        raise ValueError(f"The expression ends with '{tokens[-1]}' - a number is missing after it")


def solve_flat(tokens):
    tokens = join_signs(tokens)
    check_pattern(tokens)

    # Pass 1: do * and / straight away, keep + and - for later
    stack = Stack()
    stack.push(tokens[0])
    i = 1
    while i < len(tokens):
        operator = tokens[i]
        right = tokens[i + 1]
        if operator == "*":
            stack.push(stack.pop() * right)
        elif operator == "/":
            if right == 0:
                raise ValueError(f"Division by zero: {pretty(stack.peek())} / 0 is not allowed")
            stack.push(stack.pop() / right)
        else:
            stack.push(operator)
            stack.push(right)
        i += 2

    # Pass 2: only + and - are left, so go from left to right
    items = stack.to_list()
    total = items[0]
    j = 1
    while j < len(items):
        if items[j] == "+":
            total = total + items[j + 1]
        else:
            total = total - items[j + 1]
        j += 2
    return total


# ---------------------------------------------------------------------------
# Step 3 + 4 together: remove brackets, then solve
# ---------------------------------------------------------------------------
def evaluate(text):
    tokens = tokenize(text)
    check_brackets(tokens)

    # Keep solving the innermost brackets until none are left
    while "(" in tokens:
        stack = Stack()                    # remembers where each "(" is
        for index, token in enumerate(tokens):
            if token == "(":
                stack.push(index)
            elif token == ")":
                start = stack.pop()        # the matching "("
                inside = tokens[start + 1:index]
                if len(inside) == 0:
                    raise ValueError("Empty brackets '()' - there is nothing to calculate inside them")
                answer = solve_flat(inside)
                tokens = tokens[:start] + [answer] + tokens[index + 1:]
                break                      # start again with the shorter list

    return solve_flat(tokens)


# ---------------------------------------------------------------------------
# Files
# ---------------------------------------------------------------------------
def is_separator(line):
    line = line.strip()
    return len(line) >= 2 and all(ch == "-" for ch in line)


def process_file(input_path, output_path):
    with open(input_path, "r") as f:
        lines = f.read().splitlines()

    output = []
    solved = 0
    failed = 0
    for line in lines:
        if is_separator(line):
            output.append(line.strip())
        elif line.strip() == "":
            continue
        else:
            try:
                output.append(pretty(evaluate(line)))
                solved += 1
            except ValueError as error:
                output.append(f"Error: {error}")
                failed += 1

    with open(output_path, "w") as f:
        f.write("\n".join(output) + "\n")
    return solved, failed


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    input_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "input.txt")
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "output.txt")

    if not os.path.isfile(input_path):
        print(f"Error: the input file '{input_path}' was not found")
        sys.exit(1)

    solved, failed = process_file(input_path, output_path)
    print(f"Finished: {solved} solved, {failed} with errors.")
    print(f"Results saved in {output_path}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Fix unescaped double quotes inside Python string literals.
Heuristic: a '"' that closes a string is immediately followed by
  , ) ] \n or a comma+spaces pattern (i.e. end of string argument).
A '"' inside Chinese content is followed by Chinese chars or spaces or more content.
"""

with open('generate_ppt.py', encoding='utf-8') as f:
    src = f.read()

# Approach: work line by line.
# For each line, count double-quote chars.
# Lines with > 2 double quotes in a string context need fixing.
# Strategy: for each line, manually parse the string regions.

def is_string_closer(src, pos):
    """
    Given that we just encountered a '"' at src[pos], decide if it's a
    string-closing quote or an inner content quote.
    A string closer is followed (possibly after whitespace) by:
        , ) ] \n = (function call syntax)
    An inner quote is followed by non-whitespace content chars (Chinese etc.)
    """
    if pos + 1 >= len(src):
        return True
    next_char = src[pos + 1]
    # Definitely a closer if followed by these
    if next_char in (',', ')', ']', '\n', '\r', ' ', '"', ':'):
        # But if followed by space then more content chars it might not be
        # Look ahead past spaces
        j = pos + 1
        while j < len(src) and src[j] == ' ':
            j += 1
        if j < len(src) and src[j] in (',', ')', ']', '\n', '\r', '#', '+', ':'):
            return True
        if j < len(src) and src[j] == '"':
            # Could be start of new string concatenation OR just another quote
            # In our code, double-quote after space in string content means content
            return False
    # If next char is Chinese or alphanumeric or other content -> inner quote
    return False


def fix_string_literals(src):
    result = []
    i = 0
    n = len(src)

    while i < n:
        c = src[i]

        # Handle comments
        if c == '#':
            # Find end of line
            j = i
            while j < n and src[j] != '\n':
                j += 1
            result.append(src[i:j])
            i = j
            continue

        # Handle triple-quoted strings
        if src[i:i+3] in ('"""', "'''"):
            q3 = src[i:i+3]
            end = src.find(q3, i + 3)
            if end != -1:
                result.append(src[i:end + 3])
                i = end + 3
            else:
                result.append(src[i:])
                i = n
            continue

        # Handle single-quoted strings
        if c == "'":
            result.append(c)
            i += 1
            while i < n:
                ch = src[i]
                if ch == '\\':
                    result.append(ch)
                    i += 1
                    if i < n:
                        result.append(src[i])
                        i += 1
                    continue
                if ch == "'":
                    result.append(ch)
                    i += 1
                    break
                result.append(ch)
                i += 1
            continue

        # Handle double-quoted strings
        if c == '"':
            # We're starting a double-quoted string
            string_start = i
            result.append('"')
            i += 1
            while i < n:
                ch = src[i]
                if ch == '\\':
                    result.append(ch)
                    i += 1
                    if i < n:
                        result.append(src[i])
                        i += 1
                    continue
                if ch == '"':
                    # Is this the closing quote or an inner quote?
                    if is_string_closer(src, i):
                        result.append('"')
                        i += 1
                        break
                    else:
                        # Inner quote - escape it
                        result.append('\\')
                        result.append('"')
                        i += 1
                        continue
                if ch == '\n':
                    # Unterminated string - just close it
                    result.append('"')
                    break
                result.append(ch)
                i += 1
            continue

        result.append(c)
        i += 1

    return ''.join(result)


fixed = fix_string_literals(src)

import ast
try:
    ast.parse(fixed)
    print('Syntax OK')
    with open('generate_ppt.py', 'w', encoding='utf-8') as f:
        f.write(fixed)
    print('File written successfully.')
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}: {e.msg}')
    lines = fixed.split('\n')
    if e.lineno and e.lineno <= len(lines):
        print(f'Line content: {lines[e.lineno - 1][:120]}')
    # Show context
    for li in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
        print(f'  {li+1}: {lines[li][:100]}')

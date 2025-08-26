import re
from html.parser import HTMLParser
import random
import base64
import clipboard

class NameGenerator:
    def __init__(self):
        self.index = 0

    def _to_name(self, n):
        name = ''
        while True:
            name = chr(97 + n % 26) + name
            n = n // 26 - 1
            if n < 0:
                break
        return name

    def next(self):
        name = self._to_name(self.index)
        self.index += 1
        return name

def encode_string_dynamic(s: str) -> str:
    parts = []
    for c in s:
        base = ord(c) + random.randint(-5, 5)
        diff = ord(c) - base
        op = '+' if diff >= 0 else '-'
        diff = abs(diff)
        parts.append(f"String.fromCharCode('\\u{base:04x}'.charCodeAt(0) {op} {diff})")
    return ' + '.join(parts)

def junk_code() -> str:
    val = random.randint(100, 999)
    return f"if('' === String.fromCharCode({val})) return;"

class HTMLToJSParser(HTMLParser):
    def __init__(self, parent_var, name_gen: NameGenerator):
        super().__init__()
        self.js_lines = []
        self.stack = [parent_var]
        self.ns_stack = [None]
        self.name_gen = name_gen

    def handle_starttag(self, tag, attrs):
        el_var = self.name_gen.next()
        ns = "http://www.w3.org/2000/svg" if (self.ns_stack[-1] or tag == "svg") else None
        self.ns_stack.append(ns)

        tag_encoded = encode_string_dynamic(tag)
        if ns:
            ns_encoded = encode_string_dynamic(ns)
            self.js_lines.append(f"var {el_var} = document.createElementNS({ns_encoded}, {tag_encoded});")
        else:
            self.js_lines.append(f"var {el_var} = document.createElement({tag_encoded});")

        for (attr, val) in attrs:
            val = val or ""
            encoded_attr = encode_string_dynamic(attr)
            encoded_val = encode_string_dynamic(val)
            self.js_lines.append(f"{el_var}.setAttribute({encoded_attr}, {encoded_val});")

        self.js_lines.append(f"{self.stack[-1]}.appendChild({el_var});")
        self.stack.append(el_var)

    def handle_endtag(self, tag):
        self.stack.pop()
        self.ns_stack.pop()

    def handle_data(self, data):
        text = data.strip()
        if text:
            el_var = self.name_gen.next()
            encoded = encode_string_dynamic(text)
            self.js_lines.append(junk_code())
            self.js_lines.append(f"var {el_var} = document.createTextNode({encoded});")
            self.js_lines.append(f"{self.stack[-1]}.appendChild({el_var});")

def obfuscate_html_body_to_js(html: str) -> str:
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    if not body_match:
        raise ValueError("No <body> found")

    body_content = body_match.group(1)
    name_gen = NameGenerator()
    main_var = name_gen.next()

    parser = HTMLToJSParser(main_var, name_gen)
    parser.feed(body_content)

    js_lines = [f"(function() {{", f"  var {main_var} = document.body;"]
    js_lines.extend("  " + l for l in parser.js_lines)
    js_lines.append("})();")

    final_code = "\n".join(js_lines)
    final_code_encoded = base64.b64encode(final_code.encode('utf-8')).decode('ascii')

    script = f"<script>eval(atob('{final_code_encoded}'))</script>"

    def repl(match):
        return match.group(1) + "\n" + script + "\n" + match.group(2)

    new_html = re.sub(r'(<body[^>]*>).*?(</body>)', repl, html, flags=re.DOTALL | re.IGNORECASE)
    return new_html

if __name__ == "__main__":
    example_html = """
    # 코드 여기에
    """

    result = obfuscate_html_body_to_js(example_html)

    with open("obfuscated_result.html", "w", encoding="utf-8") as f:
        f.write(result)

    print(result)
    clipboard.copy(result)
    print("클립보드에 복사 완료! 이제 Ctrl+V ㄱ")
    input("\n=== 난독화 + base64 + eval 완료 === Press Enter to exit...")

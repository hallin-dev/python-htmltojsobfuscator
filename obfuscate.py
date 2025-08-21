import re, random
from html.parser import HTMLParser

def random_name(length=10):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return '_' + ''.join(random.choices(chars, k=length))

def encode_string(s: str) -> str:
    codes = ",".join(str(ord(c)) for c in s)
    return f"String.fromCharCode({codes})"

def junk_code() -> str:
    fname = random_name()
    val = random.randint(1000, 9999)
    return f"function {fname}() {{ var x = {val}; return x * x; }}"

class HTMLToJSParser(HTMLParser):
    def __init__(self, parent_var):
        super().__init__()
        self.js_lines = []
        self.stack = [parent_var]
        self.ns_stack = [None]

    def handle_starttag(self, tag, attrs):
        el_var = random_name()
        ns = "http://www.w3.org/2000/svg" if (self.ns_stack[-1] or tag == "svg") else None
        self.ns_stack.append(ns)

        if ns:
            self.js_lines.append(f"var {el_var} = document.createElementNS('{ns}', '{tag}');")
        else:
            self.js_lines.append(f"var {el_var} = document.createElement('{tag}');")

        for (attr, val) in attrs:
            val = val or ""
            self.js_lines.append(f"{el_var}.setAttribute('{attr}', {encode_string(val)});")

        self.js_lines.append(f"{self.stack[-1]}.appendChild({el_var});")
        self.stack.append(el_var)

    def handle_endtag(self, tag):
        self.stack.pop()
        self.ns_stack.pop()

    def handle_data(self, data):
        text = data.strip()
        if text:
            el_var = random_name()
            encoded = encode_string(text)

            if random.random() < 0.5:
                self.js_lines.append(junk_code())

            self.js_lines.append(f"var {el_var} = document.createTextNode({encoded});")
            self.js_lines.append(f"{self.stack[-1]}.appendChild({el_var});")

            if random.random() < 0.5:
                self.js_lines.append(f"return {el_var};")

def obfuscate_html_body_to_js(html: str) -> str:
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    if not body_match:
        raise ValueError("No <body> found")

    body_content = body_match.group(1)
    main_var = random_name()

    parser = HTMLToJSParser(main_var)
    parser.feed(body_content)

    js_lines = [f"(function() {{", f"  var {main_var} = document.body;"]
    js_lines.extend("  " + l for l in parser.js_lines)
    js_lines.append("})();")

    script = "<script>\n" + "\n".join(js_lines) + "\n</script>"

    def repl(match):
        return match.group(1) + "\n" + script + "\n" + match.group(2)

    new_html = re.sub(r'(<body[^>]*>).*?(</body>)', repl, html, flags=re.DOTALL | re.IGNORECASE)
    return new_html

if __name__ == "__main__":
    example_html = """
    <body>
        <h1>안녕하세요</h1>
        <p>테스트입니다</p>
        <li>여기다가 난독화 할 코드 넣으시면 됍니다</li>
    </body>
    """

    result = obfuscate_html_body_to_js(example_html)

    print(result)

    try:
        input("\n=== 난독화 완료 === Press Enter to exit...")
    except EOFError:
        import time
        print("\n[자동 대기 중 - 콘솔 창 닫히지 않도록]")
        time.sleep(30)

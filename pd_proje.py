import tkinter as tk
import re

""" TOKEN TANIMLARI yapılıyor ve bu kategorilere uygun regüler ifadeler ile neyin ne olduğunu belirleyecek kurallar hazırlanıyor. 
(kodun hangi kelimeleri nasıl tanıyacağını tanımlıyoruz) """
KEYWORDS = ["if", "else", "while", "int", "return", "String"]
OPERATORS = ["=", "+", "-", "*", "/"]
DELIMITERS = [";", ":", "(", ")", "{", "}"]
COMMENT_PATTERN = r'//.*?$|/\*.*?\*/'
STRING_PATTERN = r'"[^"\n]*"'
NUMBER_PATTERN = r'\b\d+\b'
ID_PATTERN = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'

KEYWORD_PATTERN = r'\b(?:' + '|'.join(KEYWORDS) + r')\b'
OPERATOR_PATTERN = r'(?:' + '|'.join(re.escape(op) for op in OPERATORS) + r')'
DELIMITER_PATTERN = r'(?:' + '|'.join(re.escape(d) for d in DELIMITERS) + r')'


# PARSER (Top-Down) -->  token'ları analiz ederek dilbilgisine uygunluğu ve tip hatalarını kontrol eder.
class Parser:
    # Token listesi, sembol tablosu ve hata listesi başlatılır.
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.symbol_table = {}
        self.errors = []

    def current(self):
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        return None
    
    # Beklenen token türü ve değeriyle eşleşme kontrolü yapar.
    def match(self, expected_type, expected_value=None):
        token = self.current()
        if token and token[0] == expected_type and (expected_value is None or token[1] == expected_value):
            self.index += 1
            return token
        return None
    
    # Yazılan kodu satır satır ayrıştırı, hata varsa false döndürür.
    def parse(self):
        success = True
        while self.current():
            if not self.statement():
                success = False
                break
        return success and not self.errors
    
    """ 49-125 arası; değişken tanımlamaları, atamalar, if-while blokları gibi yapılar ayrıştırılır. 
     Sembol tablosu (symbol_table) burada devreye girer. Tanımlanan değişkenlerin tipi burada tutulur. 
     Type error kontrolü; yanlış veya eksik atama durumlarını ya da unutulan noktalı virgül durumlarını tespit eder. """
    def statement(self):
        if self.match("KEYWORD", "int") or self.match("KEYWORD", "String"):
            self.index -= 1
            return self.declaration()
        elif self.match("KEYWORD", "return"):
            return self.expression() and self.match("DELIMITER", ";")
        elif self.match("KEYWORD", "if"):
            return self.if_statement()
        elif self.match("KEYWORD", "while"):
            return self.while_statement()
        elif self.current() and self.current()[0] == "IDENTIFIER":
            return self.assignment()
        return False
    
    def declaration(self):
        type_token = self.tokens[self.index]
        self.index += 1
        id_token = self.match("IDENTIFIER")
        if not id_token:
            self.errors.append("Expected identifier")
            return False
        if not self.match("OPERATOR", "="):
            self.errors.append("Expected '=' in declaration")
            return False
        value_token = self.current()
        if value_token[0] not in ("NUMBER", "STRING"):
            self.errors.append("Invalid initializer value")
            return False
        # Tip kontrolü
        if type_token[1] == "int" and value_token[0] != "NUMBER":
            self.errors.append("Type error: int cannot be assigned a string")
        elif type_token[1] == "String" and value_token[0] != "STRING":
            self.errors.append("Type error: String cannot be assigned a number")
        self.index += 1
        if not self.match("DELIMITER", ";"):
            self.errors.append("Missing semicolon")
            return False
        self.symbol_table[id_token[1]] = type_token[1]
        return True

    def assignment(self):
        id_token = self.match("IDENTIFIER")
        if not self.match("OPERATOR", "="):
           return False
        value_token = self.current()
        if value_token is None:
           return False

        var_type = self.symbol_table.get(id_token[1], None)
        if var_type is None:
            self.errors.append(f"Undeclared variable '{id_token[1]}' used in assignment")
        else:
            if var_type == "int" and value_token[0] != "NUMBER":
               self.errors.append("Type error: int cannot be assigned a string")
            elif var_type == "String" and value_token[0] != "STRING":
               self.errors.append("Type error: String cannot be assigned a number")

        self.index += 1
        if not self.match("DELIMITER", ";"):
            self.errors.append("Missing semicolon")
            return False
        return True

    def if_statement(self):
        if self.match("DELIMITER", "(") and self.expression() and self.match("DELIMITER", ")") and self.block():
            return True
        return False

    def while_statement(self):
        if self.match("DELIMITER", "(") and self.expression() and self.match("DELIMITER", ")") and self.block():
            return True
        return False
    
    # { ... } içeriğini işler.
    def block(self):
        if not self.match("DELIMITER", "{"):
            return False
        while self.current() and self.current()[1] != "}":
            if not self.statement():
                return False
        return self.match("DELIMITER", "}")
    
    # Basit ifadeleri (a + b, "abc") parse eder.
    def expression(self):
        if self.current() and self.current()[0] in ("IDENTIFIER", "NUMBER", "STRING"):
            self.index += 1
            while self.current() and self.current()[0] == "OPERATOR":
                self.index += 1
                if not self.current() or self.current()[0] not in ("IDENTIFIER", "NUMBER", "STRING"):
                    return False
                self.index += 1
            return True
        return False

# GUI 
class SyntaxHighlighter(tk.Tk):
    # Arayüz elemanları (kod girişi(text), analiz butonu ve sonuç ekranı) oluşturulur. Renklendirme için farklı tag'ler(keyword, string) tanımlanır.
    def __init__(self):
        super().__init__()
        self.title("Real-Time Grammar-Based Syntax Highlighter")
        self.geometry("900x600")

        self.code_area = tk.Text(self, font=("Consolas", 12), wrap=tk.NONE, height=20)
        self.code_area.pack(fill=tk.X, expand=False)

        self.analyze_button = tk.Button(self, text="Tokenize & Analyze", command=self.analyze_code)
        self.analyze_button.pack(fill=tk.X)

        self.result_area = tk.Text(self, font=("Consolas", 12), wrap=tk.NONE, height=15, bg="#f0f0f0")
        self.result_area.pack(fill=tk.BOTH, expand=True)

        # Renklendirme tag'ları
        self.code_area.tag_configure("keyword", foreground="red")
        self.code_area.tag_configure("number", foreground="blue")
        self.code_area.tag_configure("identifier", foreground="purple")
        self.code_area.tag_configure("operator", foreground="green")
        self.code_area.tag_configure("delimiter", foreground="orange")
        self.code_area.tag_configure("comment", foreground="gray")
        self.code_area.tag_configure("string", foreground="brown")

        self.code_area.bind("<KeyRelease>", self.on_key_release)

    # Klavye tuşuna basıldığında highlight() fonksiyonu çağrılır yani anlık renklendirme yapılır.
    def on_key_release(self, event=None):
        self.highlight(self.code_area.get("1.0", tk.END))

    # Girilen koddaki keyword, string, number vb. yapıları tanır ve uygun renkle renklendirir.
    def highlight(self, content):
        for tag in ["keyword", "number", "identifier", "operator", "delimiter", "comment", "string"]:
            self.code_area.tag_remove(tag, "1.0", tk.END)

        def apply_pattern(pattern, tag):
            for match in re.finditer(pattern, content, re.DOTALL | re.MULTILINE):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.code_area.tag_add(tag, start, end)

        apply_pattern(COMMENT_PATTERN, "comment")
        apply_pattern(STRING_PATTERN, "string")
        apply_pattern(KEYWORD_PATTERN, "keyword")
        apply_pattern(NUMBER_PATTERN, "number")
        apply_pattern(OPERATOR_PATTERN, "operator")
        apply_pattern(DELIMITER_PATTERN, "delimiter")

        for match in re.finditer(ID_PATTERN, content):
            if match.group() not in KEYWORDS:
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.code_area.tag_add("identifier", start, end)
    
    # Girilen kod satır satır alınır ve her satır token'lara ayrılır. Parser ile analiz edilir, Hatalı satır varsa GUI’de ❌ ile gösterilir; geçerli satırlar ✅ ile gösterilir.
    def analyze_code(self):
        content = self.code_area.get("1.0", tk.END).strip()
        self.result_area.delete("1.0", tk.END)
        if not content:
            return

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            tokens = self.tokenize(line)
            parser = Parser(tokens)
            result = parser.parse()
            if parser.errors:
                for err in parser.errors:
                    self.result_area.insert(tk.END, f"Line {idx}: ❌ {err}\n")
            else:
                self.result_area.insert(tk.END, f"Line {idx}: ✅ Valid\n")
    
    # Regex kullanarak gelen metni token listesine çevirir ve tanımlı kurallara uymayan karakterleri "ERROR" olarak işaretler.
    def tokenize(self, content):
        token_specs = [
            ("COMMENT", r'//.*?$|/\*.*?\*/'),
            ("STRING", r'"[^"\n]*"'),
            ("KEYWORD", r'\b(?:if|else|while|int|return|String)\b'),
            ("NUMBER", r'\b\d+\b'),
            ("OPERATOR", r'(?:=|\+|\-|\*|/)'),
            ("DELIMITER", r'(?:;|\(|\)|\{|\})'),
            ("IDENTIFIER", r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
            ("SKIP", r'[ \t\n]+'),
            ("MISMATCH", r'.'),
        ]

        tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_specs)
        tokens = []

        for mo in re.finditer(tok_regex, content, re.MULTILINE | re.DOTALL):
            kind = mo.lastgroup
            value = mo.group()
            if kind == "SKIP" or kind == "COMMENT":
                continue
            elif kind == "MISMATCH":
                tokens.append(("ERROR", value))
            else:
                tokens.append((kind, value))

        return tokens

# Program doğrudan çalıştırıldığında GUI başlatılır.
if __name__ == "__main__":
    app = SyntaxHighlighter()
    app.mainloop()

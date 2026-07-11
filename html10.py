#!/usr/bin/env python3
"""
HTML10 - Leitor Inteligente de Código Multilíngue
Um único arquivo com todas as funcionalidades integradas
Suporta: Python, Java, JavaScript, Lua e detecção de idiomas humanos
"""

import re
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod

try:
    from langdetect import detect, detect_langs
    import chardet
except ImportError:
    print("Instalando dependências necessárias...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "langdetect", "chardet"])
    from langdetect import detect, detect_langs
    import chardet


# ============================================================================
# DETECTORS - Detecção de Linguagens
# ============================================================================

class LanguageDetector:
    """Detecta a linguagem de programação do código"""
    
    LANGUAGE_PATTERNS = {
        "python": {
            "extensions": [".py"],
            "keywords": ["def ", "import ", "class ", "if __name__", "except ", "@"],
        },
        "java": {
            "extensions": [".java"],
            "keywords": ["public class", "public static void", "import java", "throws"],
        },
        "javascript": {
            "extensions": [".js", ".jsx"],
            "keywords": ["function ", "const ", "let ", "var ", "=>", "require(", "export"],
        },
        "lua": {
            "extensions": [".lua"],
            "keywords": ["function ", "local ", "end", "if ", "then", "require"],
        },
        "cpp": {
            "extensions": [".cpp", ".cc", ".cxx"],
            "keywords": ["#include", "std::", "void ", "int main", "template"],
        },
        "go": {
            "extensions": [".go"],
            "keywords": ["package ", "func ", "import (", "defer ", "go "],
        },
        "rust": {
            "extensions": [".rs"],
            "keywords": ["fn ", "let ", "mod ", "use ", "impl ", "match"],
        },
        "csharp": {
            "extensions": [".cs"],
            "keywords": ["using ", "namespace ", "public class", "public static"],
        },
        "typescript": {
            "extensions": [".ts", ".tsx"],
            "keywords": ["interface ", "type ", "enum ", "namespace ", ": "],
        },
    }
    
    @staticmethod
    def detect_from_extension(filename: str) -> Optional[str]:
        """Detecta linguagem pela extensão do arquivo"""
        for lang, patterns in LanguageDetector.LANGUAGE_PATTERNS.items():
            for ext in patterns["extensions"]:
                if filename.endswith(ext):
                    return lang
        return None
    
    @staticmethod
    def detect_from_content(code: str) -> str:
        """Detecta linguagem pela análise de palavras-chave no código"""
        scores = {}
        code_lower = code.lower()
        
        for lang, patterns in LanguageDetector.LANGUAGE_PATTERNS.items():
            score = 0
            for keyword in patterns["keywords"]:
                score += code_lower.count(keyword.lower())
            scores[lang] = score
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "unknown"
    
    @staticmethod
    def detect(code: str, filename: str = "") -> Dict[str, Any]:
        """Detecta a linguagem de programação"""
        lang_ext = LanguageDetector.detect_from_extension(filename) if filename else None
        lang_content = LanguageDetector.detect_from_content(code)
        
        language = lang_ext or lang_content
        confidence = 0.9 if lang_ext else 0.6
        
        return {
            "language": language,
            "confidence": confidence,
            "method": "extension" if lang_ext else "content"
        }


class IDDetector:
    """Detecta o idioma humano do código"""
    
    @staticmethod
    def extract_comments_and_strings(code: str) -> str:
        """Extrai comentários e strings do código"""
        code = re.sub(r'["\'].*?["\']', '', code)
        code = re.sub(r'#.*?$', '', code, flags=re.MULTILINE)
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code
    
    @staticmethod
    def detect(code: str) -> Dict[str, Any]:
        """Detecta o idioma humano do código"""
        text = IDDetector.extract_comments_and_strings(code)
        
        if not text or len(text.strip()) < 10:
            return {
                "language": "unknown",
                "confidence": 0.0,
                "reason": "insufficient_text"
            }
        
        try:
            lang = detect(text)
            confidence = 0.8
            return {
                "language": lang,
                "confidence": confidence,
            }
        except Exception as e:
            return {
                "language": "unknown",
                "confidence": 0.0,
                "error": str(e)
            }
    
    @staticmethod
    def detect_encoding(code_bytes: bytes) -> Dict[str, Any]:
        """Detecta a codificação do arquivo"""
        result = chardet.detect(code_bytes)
        return {
            "encoding": result.get("encoding", "utf-8"),
            "confidence": result.get("confidence", 0.0)
        }


# ============================================================================
# PARSERS - Analisadores por Linguagem
# ============================================================================

class BaseLanguageParser(ABC):
    """Classe base para parsers de linguagens específicas"""
    
    def __init__(self, language_name: str):
        self.language_name = language_name
    
    @abstractmethod
    def parse(self, code: str) -> Dict[str, Any]:
        """Parse o código e retorna análise"""
        pass
    
    @abstractmethod
    def extract_structure(self, code: str) -> Dict[str, List]:
        """Extrai estrutura (funções, classes, etc)"""
        pass
    
    def extract_functions(self, code: str) -> List[Dict[str, Any]]:
        return []
    
    def extract_classes(self, code: str) -> List[Dict[str, Any]]:
        return []
    
    def extract_imports(self, code: str) -> List[str]:
        return []
    
    def extract_comments(self, code: str) -> List[str]:
        return []
    
    def extract_variables(self, code: str) -> List[Dict[str, str]]:
        return []


class PythonParser(BaseLanguageParser):
    """Parser para código Python"""
    
    def __init__(self):
        super().__init__("Python")
    
    def parse(self, code: str) -> Dict[str, Any]:
        return {
            "language": self.language_name,
            "functions": self.extract_functions(code),
            "classes": self.extract_classes(code),
            "imports": self.extract_imports(code),
            "comments": self.extract_comments(code),
            "variables": self.extract_variables(code),
        }
    
    def extract_structure(self, code: str) -> Dict[str, List]:
        return {
            "functions": self.extract_functions(code),
            "classes": self.extract_classes(code),
            "imports": self.extract_imports(code),
        }
    
    def extract_functions(self, code: str) -> List[Dict[str, Any]]:
        functions = []
        pattern = r"^def\s+([a-zA-Z_]\w*)\s*\((.*?)\).*?:"
        
        for match in re.finditer(pattern, code, re.MULTILINE):
            name = match.group(1)
            params = match.group(2).split(",")
            functions.append({
                "name": name,
                "params": [p.strip() for p in params if p.strip()],
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return functions
    
    def extract_classes(self, code: str) -> List[Dict[str, Any]]:
        classes = []
        pattern = r"^class\s+([a-zA-Z_]\w*)\s*(?:\((.*?)\))?.*?:"
        
        for match in re.finditer(pattern, code, re.MULTILINE):
            name = match.group(1)
            parent = match.group(2) or "object"
            classes.append({
                "name": name,
                "parent": parent,
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return classes
    
    def extract_imports(self, code: str) -> List[str]:
        imports = []
        patterns = [
            r"^import\s+([^\n]+)",
            r"^from\s+([^\s]+)\s+import\s+([^\n]+)",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                imports.append(match.group(0).strip())
        
        return imports
    
    def extract_comments(self, code: str) -> List[str]:
        comments = []
        pattern = r"#\s*(.*?)$"
        
        for match in re.finditer(pattern, code, re.MULTILINE):
            comment = match.group(1).strip()
            if comment:
                comments.append(comment)
        
        return comments
    
    def extract_variables(self, code: str) -> List[Dict[str, str]]:
        variables = []
        pattern = r"^([a-zA-Z_]\w*)\s*=\s*(.+?)$"
        
        for match in re.finditer(pattern, code, re.MULTILINE):
            name = match.group(1)
            value = match.group(2).strip()[:50]
            variables.append({
                "name": name,
                "value": value,
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return variables


class JavaParser(BaseLanguageParser):
    """Parser para código Java"""
    
    def __init__(self):
        super().__init__("Java")
    
    def parse(self, code: str) -> Dict[str, Any]:
        return {
            "language": self.language_name,
            "functions": self.extract_functions(code),
            "classes": self.extract_classes(code),
            "imports": self.extract_imports(code),
            "comments": self.extract_comments(code),
            "variables": self.extract_variables(code),
        }
    
    def extract_structure(self, code: str) -> Dict[str, List]:
        return {
            "functions": self.extract_functions(code),
            "classes": self.extract_classes(code),
            "imports": self.extract_imports(code),
        }
    
    def extract_functions(self, code: str) -> List[Dict[str, Any]]:
        methods = []
        pattern = r"(public|private|protected)?\s+\w+\s+([a-zA-Z_]\w*)\s*\((.*?)\)"
        
        for match in re.finditer(pattern, code):
            name = match.group(2)
            params = match.group(3).split(",")
            methods.append({
                "name": name,
                "params": [p.strip() for p in params if p.strip()],
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return methods
    
    def extract_classes(self, code: str) -> List[Dict[str, Any]]:
        classes = []
        pattern = r"(public\s+)?class\s+([a-zA-Z_]\w*)\s*(?:extends\s+([^\s{]+))?"
        
        for match in re.finditer(pattern, code):
            name = match.group(2)
            parent = match.group(3) or "Object"
            classes.append({
                "name": name,
                "parent": parent,
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return classes
    
    def extract_imports(self, code: str) -> List[str]:
        imports = []
        pattern = r"^import\s+([^\n;]+);"
        
        for match in re.finditer(pattern, code, re.MULTILINE):
            imports.append(match.group(1).strip())
        
        return imports
    
    def extract_comments(self, code: str) -> List[str]:
        comments = []
        pattern = r"//\s*(.*?)$"
        for match in re.finditer(pattern, code, re.MULTILINE):
            comment = match.group(1).strip()
            if comment:
                comments.append(comment)
        
        pattern = r"/\*\s*(.*?)\s*\*/"
        for match in re.finditer(pattern, code, re.DOTALL):
            comment = match.group(1).strip()
            if comment:
                comments.append(comment)
        
        return comments
    
    def extract_variables(self, code: str) -> List[Dict[str, str]]:
        variables = []
        pattern = r"(public|private|protected)?\s+\w+\s+([a-zA-Z_]\w*)\s*(?:=\s*(.+?))?;"
        
        for match in re.finditer(pattern, code):
            name = match.group(2)
            value = (match.group(3) or "").strip()[:50]
            variables.append({
                "name": name,
                "value": value,
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return variables


class JavaScriptParser(BaseLanguageParser):
    """Parser para código JavaScript/TypeScript"""
    
    def __init__(self):
        super().__init__("JavaScript")
    
    def parse(self, code: str) -> Dict[str, Any]:
        return {
            "language": self.language_name,
            "functions": self.extract_functions(code),
            "classes": self.extract_classes(code),
            "imports": self.extract_imports(code),
            "comments": self.extract_comments(code),
            "variables": self.extract_variables(code),
        }
    
    def extract_structure(self, code: str) -> Dict[str, List]:
        return {
            "functions": self.extract_functions(code),
            "classes": self.extract_classes(code),
            "imports": self.extract_imports(code),
        }
    
    def extract_functions(self, code: str) -> List[Dict[str, Any]]:
        functions = []
        
        pattern = r"function\s+([a-zA-Z_]\w*)\s*\((.*?)\)"
        for match in re.finditer(pattern, code):
            name = match.group(1)
            params = match.group(2).split(",")
            functions.append({
                "name": name,
                "type": "declaration",
                "params": [p.strip() for p in params if p.strip()],
                "line": code[:match.start()].count("\n") + 1,
            })
        
        pattern = r"(const|let|var)\s+([a-zA-Z_]\w*)\s*=\s*(?:\(([^)]*)\)\s*)?=>"
        for match in re.finditer(pattern, code):
            name = match.group(2)
            params = (match.group(3) or "").split(",")
            functions.append({
                "name": name,
                "type": "arrow",
                "params": [p.strip() for p in params if p.strip()],
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return functions
    
    def extract_classes(self, code: str) -> List[Dict[str, Any]]:
        classes = []
        pattern = r"class\s+([a-zA-Z_]\w*)\s*(?:extends\s+([^\s{]+))?"
        
        for match in re.finditer(pattern, code):
            name = match.group(1)
            parent = match.group(2) or None
            classes.append({
                "name": name,
                "parent": parent,
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return classes
    
    def extract_imports(self, code: str) -> List[str]:
        imports = []
        
        pattern = r"import\s+(?:{[^}]+}|[^'\"\n]+)\s+from\s+['\"]([^'\"]+)['\"]"
        for match in re.finditer(pattern, code):
            imports.append(f"import from {match.group(1)}")
        
        pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        for match in re.finditer(pattern, code):
            imports.append(f"require {match.group(1)}")
        
        return imports
    
    def extract_comments(self, code: str) -> List[str]:
        comments = []
        
        pattern = r"//\s*(.*?)$"
        for match in re.finditer(pattern, code, re.MULTILINE):
            comment = match.group(1).strip()
            if comment:
                comments.append(comment)
        
        pattern = r"/\*\s*(.*?)\s*\*/"
        for match in re.finditer(pattern, code, re.DOTALL):
            comment = match.group(1).strip()
            if comment:
                comments.append(comment)
        
        return comments
    
    def extract_variables(self, code: str) -> List[Dict[str, str]]:
        variables = []
        pattern = r"(const|let|var)\s+([a-zA-Z_]\w*)\s*(?:=\s*(.+?))?(?:;|$)"
        
        for match in re.finditer(pattern, code):
            name = match.group(2)
            value = (match.group(3) or "").strip()[:50]
            variables.append({
                "name": name,
                "type": match.group(1),
                "value": value,
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return variables


class LuaParser(BaseLanguageParser):
    """Parser para código Lua"""
    
    def __init__(self):
        super().__init__("Lua")
    
    def parse(self, code: str) -> Dict[str, Any]:
        return {
            "language": self.language_name,
            "functions": self.extract_functions(code),
            "tables": self.extract_tables(code),
            "requires": self.extract_requires(code),
            "comments": self.extract_comments(code),
            "variables": self.extract_variables(code),
        }
    
    def extract_structure(self, code: str) -> Dict[str, List]:
        return {
            "functions": self.extract_functions(code),
            "tables": self.extract_tables(code),
            "requires": self.extract_requires(code),
        }
    
    def extract_functions(self, code: str) -> List[Dict[str, Any]]:
        functions = []
        
        pattern = r"function\s+([a-zA-Z_]\w*)\s*\((.*?)\)"
        for match in re.finditer(pattern, code):
            name = match.group(1)
            params = match.group(2).split(",")
            functions.append({
                "name": name,
                "params": [p.strip() for p in params if p.strip()],
                "line": code[:match.start()].count("\n") + 1,
            })
        
        pattern = r"local\s+function\s+([a-zA-Z_]\w*)\s*\((.*?)\)"
        for match in re.finditer(pattern, code):
            name = match.group(1)
            params = match.group(2).split(",")
            functions.append({
                "name": name,
                "scope": "local",
                "params": [p.strip() for p in params if p.strip()],
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return functions
    
    def extract_tables(self, code: str) -> List[Dict[str, Any]]:
        tables = []
        pattern = r"([a-zA-Z_]\w*)\s*=\s*\{"
        
        for match in re.finditer(pattern, code):
            name = match.group(1)
            tables.append({
                "name": name,
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return tables
    
    def extract_requires(self, code: str) -> List[str]:
        requires = []
        pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"
        
        for match in re.finditer(pattern, code):
            requires.append(match.group(1))
        
        return requires
    
    def extract_comments(self, code: str) -> List[str]:
        comments = []
        
        pattern = r"--\s*(.*?)$"
        for match in re.finditer(pattern, code, re.MULTILINE):
            comment = match.group(1).strip()
            if comment:
                comments.append(comment)
        
        pattern = r"--\[\[\s*(.*?)\s*--\]\]"
        for match in re.finditer(pattern, code, re.DOTALL):
            comment = match.group(1).strip()
            if comment:
                comments.append(comment)
        
        return comments
    
    def extract_variables(self, code: str) -> List[Dict[str, str]]:
        variables = []
        pattern = r"(local)?\s+([a-zA-Z_]\w*)\s*(?:=\s*(.+?))?(?:\n|,)"
        
        for match in re.finditer(pattern, code):
            name = match.group(2)
            value = (match.group(3) or "").strip()[:50]
            variables.append({
                "name": name,
                "scope": "local" if match.group(1) else "global",
                "value": value,
                "line": code[:match.start()].count("\n") + 1,
            })
        
        return variables


# ============================================================================
# EXPORTERS - Exportadores para Diferentes Formatos
# ============================================================================

class JSONExporter:
    """Exporta análise em formato JSON"""
    
    @staticmethod
    def export(analysis: Dict[str, Any], pretty: bool = True) -> str:
        indent = 2 if pretty else None
        return json.dumps(analysis, indent=indent, ensure_ascii=False)
    
    @staticmethod
    def export_to_file(analysis: Dict[str, Any], filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)


class HTMLExporter:
    """Exporta análise em formato HTML"""
    
    @staticmethod
    def export(analysis: Dict[str, Any]) -> str:
        filename = analysis.get("filename", "code")
        prog_lang = analysis.get("programming_language", {})
        human_lang = analysis.get("human_language", {})
        stats = analysis.get("statistics", {})
        struct = analysis.get("structure", {})
        
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTML10 - Análise: {filename}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .info-card {{
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            border-radius: 4px;
        }}
        .info-card h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .stats-table th {{
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        .stats-table td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        .list-section ul {{
            list-style: none;
            padding: 0;
        }}
        .list-section li {{
            padding: 10px;
            background: #f8f9fa;
            margin: 5px 0;
            border-radius: 4px;
            border-left: 3px solid #3498db;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 HTML10 - Análise de Código</h1>
        <p><strong>Arquivo:</strong> {filename}</p>
        
        <h2>🔍 Detecção de Linguagens</h2>
        <div class="info-grid">
            <div class="info-card">
                <h3>🖥️ Linguagem de Programação</h3>
                <p><strong>{prog_lang.get('language', 'Desconhecida')}</strong></p>
                <p>Confiança: {prog_lang.get('confidence', 0)*100:.1f}%</p>
            </div>
            <div class="info-card">
                <h3>🌍 Idioma Humano</h3>
                <p><strong>{human_lang.get('language', 'Desconhecido')}</strong></p>
                <p>Confiança: {human_lang.get('confidence', 0)*100:.1f}%</p>
            </div>
        </div>
        
        <h2>📈 Estatísticas</h2>
        <table class="stats-table">
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Total de Linhas</td><td><strong>{stats.get('total_lines', 0)}</strong></td></tr>
            <tr><td>Total de Caracteres</td><td><strong>{stats.get('total_characters', 0)}</strong></td></tr>
            <tr><td>Total de Palavras</td><td><strong>{stats.get('total_words', 0)}</strong></td></tr>
        </table>
        
        <h2>🏗️ Estrutura do Código</h2>
        <div class="list-section">
            <h3>Funções ({len(struct.get('functions', []))})</h3>
            <ul>{HTMLExporter._render_list(struct.get('functions', []))}</ul>
        </div>
        <div class="list-section">
            <h3>Classes ({len(struct.get('classes', []))})</h3>
            <ul>{HTMLExporter._render_list(struct.get('classes', []))}</ul>
        </div>
        <div class="list-section">
            <h3>Imports ({len(struct.get('imports', []))})</h3>
            <ul>{HTMLExporter._render_list(struct.get('imports', []))}</ul>
        </div>
    </div>
</body>
</html>
        """
        return html
    
    @staticmethod
    def _render_list(items):
        if not items:
            return "<li>Nenhum item encontrado</li>"
        
        html = ""
        for item in items:
            if isinstance(item, dict):
                name = item.get('name', 'Sem nome')
                html += f"<li><strong>{name}</strong></li>"
            else:
                html += f"<li>{item}</li>"
        return html
    
    @staticmethod
    def export_to_file(analysis: Dict[str, Any], filepath: str) -> None:
        html = HTMLExporter.export(analysis)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)


class MarkdownExporter:
    """Exporta análise em formato Markdown"""
    
    @staticmethod
    def export(analysis: Dict[str, Any]) -> str:
        filename = analysis.get("filename", "code")
        prog_lang = analysis.get("programming_language", {})
        human_lang = analysis.get("human_language", {})
        stats = analysis.get("statistics", {})
        struct = analysis.get("structure", {})
        
        md = f"""# 📊 HTML10 - Análise de Código

**Arquivo:** `{filename}`

---

## 🔍 Detecção de Linguagens

### 🖥️ Linguagem de Programação
- **Linguagem:** {prog_lang.get('language', 'Desconhecida')}
- **Confiança:** {prog_lang.get('confidence', 0)*100:.1f}%

### 🌍 Idioma Humano
- **Idioma:** {human_lang.get('language', 'Desconhecido')}
- **Confiança:** {human_lang.get('confidence', 0)*100:.1f}%

---

## 📈 Estatísticas

| Métrica | Valor |
|---------|-------|
| Total de Linhas | {stats.get('total_lines', 0)} |
| Total de Caracteres | {stats.get('total_characters', 0)} |
| Total de Palavras | {stats.get('total_words', 0)} |

---

## 🏗️ Estrutura do Código

### Funções ({len(struct.get('functions', []))})
{MarkdownExporter._render_list_md(struct.get('functions', []))}

### Classes ({len(struct.get('classes', []))})
{MarkdownExporter._render_list_md(struct.get('classes', []))}

### Imports ({len(struct.get('imports', []))})
{MarkdownExporter._render_list_md(struct.get('imports', []))}

---

*Gerado por HTML10 - Leitor Inteligente de Código*
"""
        return md
    
    @staticmethod
    def _render_list_md(items: List) -> str:
        if not items:
            return "> Nenhum item encontrado"
        
        md = ""
        for item in items:
            if isinstance(item, dict):
                name = item.get('name', 'Sem nome')
                md += f"- **{name}**\n"
            else:
                md += f"- {item}\n"
        return md if md else "> Nenhum item encontrado"
    
    @staticmethod
    def export_to_file(analysis: Dict[str, Any], filepath: str) -> None:
        md = MarkdownExporter.export(analysis)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)


# ============================================================================
# MAIN CODE READER
# ============================================================================

class CodeReader:
    """Leitor principal de código com análise completa"""
    
    def __init__(self):
        """Inicializa o CodeReader"""
        self.language_detector = LanguageDetector()
        self.id_detector = IDDetector()
        self.parsers = {
            "python": PythonParser(),
            "java": JavaParser(),
            "javascript": JavaScriptParser(),
            "lua": LuaParser(),
        }
    
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analisa um arquivo de código completo"""
        path = Path(filepath)
        
        if not path.exists():
            return {"error": f"File not found: {filepath}"}
        
        with open(filepath, "rb") as f:
            code_bytes = f.read()
        
        code = code_bytes.decode("utf-8", errors="ignore")
        
        return self.analyze(code=code, filename=path.name)
    
    def analyze(self, code: str, filename: str = "code.txt") -> Dict[str, Any]:
        """Análise completa de código"""
        prog_lang = self.language_detector.detect(code, filename)
        human_lang = self.id_detector.detect(code)
        language_analysis = self._analyze_language(code, prog_lang["language"])
        
        result = {
            "filename": filename,
            "programming_language": prog_lang,
            "human_language": human_lang,
            "statistics": {
                "total_lines": len(code.split("\n")),
                "total_characters": len(code),
                "total_words": len(code.split()),
            },
            "analysis": language_analysis,
            "structure": self._extract_structure(code, prog_lang["language"]),
        }
        
        return result
    
    def _analyze_language(self, code: str, language: str) -> Dict[str, Any]:
        """Análise específica por linguagem"""
        if language in self.parsers:
            parser = self.parsers[language]
            return parser.parse(code)
        
        return {
            "language": language,
            "message": f"Parser para {language} não disponível ainda",
            "raw_lines": len(code.split("\n"))
        }
    
    def _extract_structure(self, code: str, language: str) -> Dict[str, List]:
        """Extrai estrutura do código"""
        if language in self.parsers:
            parser = self.parsers[language]
            return parser.extract_structure(code)
        
        return {"functions": [], "classes": [], "imports": []}
    
    def batch_analyze(self, directory: str) -> List[Dict[str, Any]]:
        """Analisa múltiplos arquivos em um diretório"""
        results = []
        path = Path(directory)
        
        for file in path.rglob("*"):
            if file.is_file():
                try:
                    result = self.analyze_file(str(file))
                    results.append(result)
                except Exception as e:
                    results.append({
                        "file": str(file),
                        "error": str(e)
                    })
        
        return results
    
    def export_json(self, analysis: Dict[str, Any]) -> str:
        """Exporta análise em JSON"""
        return JSONExporter.export(analysis)
    
    def export_html(self, analysis: Dict[str, Any]) -> str:
        """Exporta análise em HTML"""
        return HTMLExporter.export(analysis)
    
    def export_markdown(self, analysis: Dict[str, Any]) -> str:
        """Exporta análise em Markdown"""
        return MarkdownExporter.export(analysis)


# ============================================================================
# CLI - Interface de Linha de Comando
# ============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="HTML10 - Leitor Inteligente de Código Multilíngue",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python html10.py analyze code.py
  python html10.py analyze code.py -o output.json
  python html10.py analyze code.py --format html -o output.html
  python html10.py batch src/ --format markdown
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comando a executar")
    
    # Comando analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analisa um arquivo de código")
    analyze_parser.add_argument("file", help="Arquivo a analisar")
    analyze_parser.add_argument("-o", "--output", help="Arquivo de saída")
    analyze_parser.add_argument(
        "-f", "--format",
        choices=["json", "html", "markdown"],
        default="json",
        help="Formato de exportação (padrão: json)"
    )
    
    # Comando batch
    batch_parser = subparsers.add_parser("batch", help="Analisa múltiplos arquivos")
    batch_parser.add_argument("directory", help="Diretório a analisar")
    batch_parser.add_argument("-o", "--output", help="Arquivo de saída")
    batch_parser.add_argument(
        "-f", "--format",
        choices=["json", "html", "markdown"],
        default="json",
        help="Formato de exportação (padrão: json)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    reader = CodeReader()
    
    try:
        if args.command == "analyze":
            handle_analyze(reader, args)
        elif args.command == "batch":
            handle_batch(reader, args)
    except Exception as e:
        print(f"❌ Erro: {e}", file=sys.stderr)
        sys.exit(1)


def handle_analyze(reader: CodeReader, args):
    """Handle analyze command"""
    print(f"📖 Analisando: {args.file}")
    
    analysis = reader.analyze_file(args.file)
    
    if "error" in analysis:
        print(f"❌ {analysis['error']}", file=sys.stderr)
        return
    
    output = export_analysis(analysis, args.format)
    
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ Análise salva em: {args.output}")
    else:
        print(output)


def handle_batch(reader: CodeReader, args):
    """Handle batch command"""
    print(f"📦 Analisando diretório: {args.directory}")
    
    results = reader.batch_analyze(args.directory)
    
    print(f"✅ {len(results)} arquivo(s) analisado(s)")
    
    output = export_analysis(results, args.format)
    
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"✅ Resultados salvos em: {args.output}")
    else:
        print(output[:500] + "..." if len(output) > 500 else output)


def export_analysis(analysis, format_type: str) -> str:
    """Exporta análise no formato especificado"""
    if format_type == "json":
        return JSONExporter.export(analysis)
    elif format_type == "html":
        if isinstance(analysis, list):
            return "<html><body><h1>Resultados</h1>" + \
                   "".join(HTMLExporter.export(a) for a in analysis) + \
                   "</body></html>"
        return HTMLExporter.export(analysis)
    elif format_type == "markdown":
        if isinstance(analysis, list):
            return "# Resultados\n\n" + \
                   "\n\n---\n\n".join(MarkdownExporter.export(a) for a in analysis)
        return MarkdownExporter.export(analysis)


if __name__ == "__main__":
    main()

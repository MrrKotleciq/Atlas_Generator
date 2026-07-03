import ast
import sys
import os
import shutil
import json
from pathlib import Path
from collections import defaultdict

# ================= CONFIGURATION ENGINE =================
# Determine the project root so the configuration file can be found inside it
PROJECT_ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()

def load_settings(project_root):
    """Loads settings from .atlas_config in the project folder or creates a default template."""
    settings_file = project_root / ".atlas_config"
    defaults = {
        "obsidian_vault_path": "C:\\obsidian\\YourVault\\Project_Atlas",
        "ignore_dirs": ['.obsidian', '.vscode', '__pycache__', 'venv', '.git']
    }

    if not settings_file.exists():
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(defaults, f, indent=4)
        print(f"⚠️  Configuration file {settings_file} was not found. A default template has been created in the project folder.")
        print("👉 Please edit .atlas_config in the project folder, set the vault path, and run the script again.")
        exit(1)

    with open(settings_file, 'r', encoding='utf-8') as f:
        return json.load(f)

# Load project-specific settings
settings = load_settings(PROJECT_ROOT)
print(f"🔍 Analyzing project at: {PROJECT_ROOT}")
OBSIDIAN_VAULT_PATH = Path(settings.get("obsidian_vault_path"))
IGNORE_DIRS = set(settings.get("ignore_dirs", []))
# ========================================================

class ProjectAnalyzer(ast.NodeVisitor):
    def __init__(self, file_path, source_code):
        self.file_path = file_path
        self.source_code = source_code
        self.results = {
            'classes': {},
            'functions': {},
            'module_calls': [],
            'imports': {}
        }
        self.current_class = None
        self.current_element = None

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.results['imports'][name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module if node.module else 'unknown'
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.results['imports'][name] = module
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        docstring = ast.get_docstring(node) or "Brak opisu."
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)

        self.results['classes'][node.name] = {
            'doc': docstring,
            'methods': {},
            'lineno': node.lineno,
            'bases': bases
        }
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        docstring = ast.get_docstring(node) or "No description."
        func_data = {
            'doc': docstring,
            'lineno': node.lineno,
            'args': [f"{arg.arg}: {ast.unparse(arg.annotation) if arg.annotation else 'Any'}" for arg in node.args.args],
            'returns': ast.unparse(node.returns) if node.returns else 'Any',
            'calls': [],
            'source': ast.get_source_segment(self.source_code, node)
        }

        if self.current_class:
            self.results['classes'][self.current_class]['methods'][node.name] = func_data
        else:
            self.results['functions'][node.name] = func_data

        previous_element = self.current_element
        self.current_element = func_data
        self.generic_visit(node)
        self.current_element = previous_element

    def visit_Call(self, node):
        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr

        if name:
            full_call = name
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                full_call = f"{node.func.value.id}.{name}"

            if self.current_element is not None:
                self.current_element['calls'].append(full_call)
            else:
                self.results['module_calls'].append(full_call)
        self.generic_visit(node)

def generate_vscode_link(path, line=None):
    link = f"vscode://file/{path}"
    if line:
        link += f":{line}"
    return f"[KOD 💻]({link})"

def create_obsidian_note(path, title, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def run_atlas_generator():
    graph_dir = OBSIDIAN_VAULT_PATH / "graph"
    if graph_dir.exists() and graph_dir.is_dir():
        shutil.rmtree(graph_dir)

    all_py_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            if file.endswith('.py') and file != 'generate_atlas.py':
                all_py_files.append(Path(root) / file)

    global_registry = {}

    module_data = {}
    for py_file in all_py_files:
        with open(py_file, 'r', encoding='utf-8') as f:
            try:
                source = f.read()
                tree = ast.parse(source)
                analyzer = ProjectAnalyzer(py_file, source)
                analyzer.visit(tree)

                rel_path = py_file.relative_to(PROJECT_ROOT)
                module_data[str(rel_path)] = analyzer.results

                for name in analyzer.results['classes']:
                    global_registry.setdefault(name, []).append({'type': 'Class', 'id': f'Class_{name}'})
                for cls_name, cls_info in analyzer.results['classes'].items():
                    for m_name in cls_info['methods']:
                        global_registry.setdefault(m_name, []).append({'type': 'Method', 'id': f'Method_{cls_name}_{m_name}'})
                for name in analyzer.results['functions']:
                    global_registry.setdefault(name, []).append({'type': 'Func', 'id': f'Func_{name}'})
            except Exception as e:
                print(f"Błąd analizy {py_file}: {e}")

    # Backlinks

    backlinks = defaultdict(list)
    for mod_path, data in module_data.items():
        mod_id = f"Module_{mod_path.replace(os.sep, '_')}"
        for called in data.get('module_calls', []):
            name_only = called.split('.')[-1]
            if name_only in global_registry:
                for entry in global_registry[name_only]:
                    backlinks[entry['id']].append(mod_id)
        for fn_name, fn_info in data['functions'].items():
            fn_id = f"Func_{fn_name}"
            for called in fn_info.get('calls', []):
                name_only = called.split('.')[-1]
                if name_only in global_registry:
                    for entry in global_registry[name_only]:
                        backlinks[entry['id']].append(fn_id)
        for cls_name, cls_info in data['classes'].items():
            for m_name, m_info in cls_info['methods'].items():
                m_id = f"Method_{cls_name}_{m_name}"
                for called in m_info.get('calls', []):
                    name_only = called.split('.')[-1]
                    if name_only in global_registry:
                        for entry in global_registry[name_only]:
                            backlinks[entry['id']].append(m_id)

    # Note for the MOC - Map Of Content

    moc_content = "---\ntype: moc\n---\n\n# 🗺️ Project Atlas\n#project-moc\n\n## Modules\n"
    for mod in module_data:
        moc_content += f"- [[Module_{mod.replace(os.sep, '_')}]] ({mod})\n"
    create_obsidian_note(OBSIDIAN_VAULT_PATH / "graph" / "00_Project_MOC.md", "MOC", moc_content)

    # Notatka dla modułu
    
    for mod_path, data in module_data.items():
        full_path = PROJECT_ROOT / mod_path
        mod_name = f"Module_{mod_path.replace(os.sep, '_')}"
        tag = "#project-main" if mod_path.endswith("main.py") else "#project-module"

        yaml = f"---\ntype: module\nfile: {mod_path}\n---\n\n"
        mod_content = yaml + f"# Module: {mod_path}\n{tag}\n\n{generate_vscode_link(full_path)}\n\n"

        if data.get('module_calls'):
            mod_content += "### 📞 Calls (module level):\n"
            for called in set(data['module_calls']):
                name_only = called.split('.')[-1]
                if name_only in global_registry:
                    for entry in global_registry[name_only]:
                        mod_content += f"- [[{entry['id']}]] ({entry['type']})\n"
                elif '.' in called and called.split('.')[0] in data.get('imports', {}):
                    lib = data['imports'][called.split('.')[0]]
                    mod_content += f"- {called} (Library: {lib})\n"
                else:
                    mod_content += f"- {called} (External/Unknown)\n"
            mod_content += "\n"

        if data['classes']:
            mod_content += "## 📦 Classes\n"
            for cls in data['classes']:
                mod_content += f"- [[Class_{cls}]]\n"
        if data['functions']:
            mod_content += "## ⚙️ Functions\n"
            for fn in data['functions']:
                mod_content += f"- [[Func_{fn}]]\n"

        create_obsidian_note(OBSIDIAN_VAULT_PATH / "graph" / "module" / f"{mod_name}.md", mod_name, mod_content)

        # Note for classes

        for cls_name, cls_info in data['classes'].items():
            yaml = f"---\ntype: class\nfile: {mod_path}\nline: {cls_info['lineno']}\nbases: {', '.join(cls_info['bases']) if cls_info['bases'] else 'None'}\n---\n\n"
            cls_content = yaml + f"# 📦 Class: {cls_name}\n#project-class\n\n{generate_vscode_link(full_path, cls_info['lineno'])}\n\n**File:** [[Module_{mod_path.replace(os.sep, '_')}]]\n\n"
            if cls_info.get('bases'):
                bases_links = ', '.join([f"[[Class_{b}]]," for b in cls_info['bases']])
                cls_content += f"**Inherits from:** {bases_links}\n\n"
            cls_content += f"### Description\n{cls_info['doc']}\n\n"
            if cls_info['methods']:
                cls_content += "### Methods\n"
                for m in cls_info['methods']:
                    cls_content += f"- [[Method_{cls_name}_{m}]]\n"
            create_obsidian_note(OBSIDIAN_VAULT_PATH / "graph" / "class" / f"Class_{cls_name}.md", f"Class_{cls_name}", cls_content)

        # Note for functions
        
        for fn_name, fn_info in data['functions'].items():
            yaml = f"---\ntype: function\nfile: {mod_path}\nline: {fn_info['lineno']}\nreturns: {fn_info['returns']}\n---\n\n"
            fn_content = yaml + f"# ⚙️ Function: {fn_name}\n#project-func\n\n{generate_vscode_link(full_path, fn_info['lineno'])}\n\n**File:** [[Module_{mod_path.replace(os.sep, '_')}]]\n\n"
            fn_content += f"### Description\n{fn_info['doc']}\n\n"
            fn_content += f"**Arguments:** `{', '.join(fn_info['args'])}`\n"
            fn_content += f"**Returns:** `{fn_info['returns']}`\n"
            if fn_info.get('calls'):
                fn_content += "\n### 📞 Calls:\n"
                for called in set(fn_info['calls']):
                    name_only = called.split('.')[-1]
                    if name_only in global_registry:
                        for entry in global_registry[name_only]:
                            fn_content += f"- [[{entry['id']}]] ({entry['type']})\n"
                    elif '.' in called and called.split('.')[0] in data.get('imports', {}):
                        lib = data['imports'][called.split('.')[0]]
                        fn_content += f"- {called} (Library: {lib})\n"
                    else:
                        fn_content += f"- {called} (External/Unknown)\n"
            if fn_info.get('source') and len(fn_info['source'].splitlines()) <= 20:
                fn_content += f"\n### 📜 Code preview\n\n```python\n{fn_info['source']}\n```\n"
            fn_id = f"Func_{fn_name}"
            if backlinks[fn_id]:
                fn_content += "\n### ⬅️ Called by:\n"
                for caller in set(backlinks[fn_id]):
                    fn_content += f"- [[{caller}]]\n"
            create_obsidian_note(OBSIDIAN_VAULT_PATH / "graph" / "func" / f"Func_{fn_name}.md", f"Func_{fn_name}", fn_content)

        # Note for methods

        for cls_name, cls_info in data['classes'].items():
            for m_name, m_info in cls_info['methods'].items():
                yaml = f"---\ntype: method\nclass: {cls_name}\nfile: {mod_path}\nline: {m_info['lineno']}\nreturns: {m_info['returns']}\n---\n\n"
                m_content = yaml + f"# 🛠️ Method: {cls_name}.{m_name}\n#project-method\n\n{generate_vscode_link(full_path, m_info['lineno'])}\n\n**Class:** [[Class_{cls_name}]]\n**File:** [[Module_{mod_path.replace(os.sep, '_')}]]\n\n"
                m_content += f"### Description\n{m_info['doc']}\n\n"
                m_content += f"**Arguments:** `{', '.join(m_info['args'])}`\n"
                m_content += f"**Returns:** `{m_info['returns']}`\n"
                if m_info.get('calls'):
                    m_content += "\n### 📞 Calls:\n"
                    for called in set(m_info['calls']):
                        name_only = called.split('.')[-1]
                        if name_only in global_registry:
                            for entry in global_registry[name_only]:
                                m_content += f"- [[{entry['id']}]] ({entry['type']})\n"
                        elif '.' in called and called.split('.')[0] in data.get('imports', {}):
                            lib = data['imports'][called.split('.')[0]]
                            m_content += f"- {called} (Library: {lib})\n"
                        else:
                            m_content += f"- {called} (External/Unknown)\n"
                if m_info.get('source') and len(m_info['source'].splitlines()) <= 20:
                    m_content += f"\n### 📜 Code preview\n\n```python\n{m_info['source']}\n```\n"
                m_id = f"Method_{cls_name}_{m_name}"
                if backlinks[m_id]:
                    m_content += "\n### ⬅️ Called by:\n"
                    for caller in set(backlinks[m_id]):
                        m_content += f"- [[{caller}]]\n"
                create_obsidian_note(OBSIDIAN_VAULT_PATH / "graph" / "method" / f"Method_{cls_name}_{m_name}.md", f"Method_{cls_name}_{m_name}", m_content)

    print(f"✅ Atlas generated successfully at: {OBSIDIAN_VAULT_PATH}")

if __name__ == "__main__":
    run_atlas_generator()
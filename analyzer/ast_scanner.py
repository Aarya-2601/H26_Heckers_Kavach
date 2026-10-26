"""
Person 2: AST scanner.

Finds every real use of the target dependency (ignores comments and strings):
  - call         requests.get(...)
  - reference    except requests.exceptions.Timeout  /  class Site(BaseModel)
  - assign       requests.Session.request = patched   (monkeypatching)
Each hit also says if it touches a private API (name starting with "_").

Test files are scanned too, but their hits go into "test_call_sites" and are NOT
counted in the blast radius, the hero file, or context_code (Blue Team can't edit tests).

Output matches contracts/ast_output.json, plus extra keys:
  call_sites[*]: symbol, kind, private_api      and      test_call_sites

Run:
    python analyzer/ast_scanner.py                      # scans ./demo_repo for 'requests'
    python analyzer/ast_scanner.py <repo> <package>     # scan any repo
    python analyzer/ast_scanner.py <repo> <package> out.json   # also save JSON
"""
import ast
import json
import os
import sys
import textwrap
import warnings

try:
    from analyzer.blast_radius import compute_blast_radius
    from analyzer.auditor import is_test_path
except ImportError:  # running the file directly
    from blast_radius import compute_blast_radius
    from auditor import is_test_path

# pip package name -> import name(s)
IMPORT_ALIASES = {
    "pyyaml": ["yaml"],
    "pillow": ["PIL"],
    "beautifulsoup4": ["bs4"],
    "scikit-learn": ["sklearn"],
    "opencv-python": ["cv2"],
    "python-dateutil": ["dateutil"],
    "setuptools": ["setuptools", "pkg_resources"],
    "attrs": ["attr", "attrs"],
    "python-dotenv": ["dotenv"],
    "pyjwt": ["jwt"],
    "pycryptodome": ["Crypto"],
    "psycopg2-binary": ["psycopg2"],
    "mysqlclient": ["MySQLdb"],
    "pyserial": ["serial"],
    "python-magic": ["magic"],
    "ruamel.yaml": ["ruamel"],
    "protobuf": ["google"],
}
SKIP_DIRS = {".git", "venv", ".venv", "env", "node_modules", "__pycache__", "build", "dist", ".tox", ".locked_tests"}
MAX_CONTEXT_CHARS = 8000  # keeps Gemma's input small


def import_names(pkg):
    p = pkg.lower()
    return set(IMPORT_ALIASES.get(p, [p.replace("-", "_")]))


def dotted(node):
    """a.b.c -> 'a.b.c'. Returns None for anything else (e.g. f().x)."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = dotted(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


def is_private(symbol):
    """True if any part of the dotted name is private (_name, but not __dunder__)."""
    for part in symbol.replace("()", "").split("."):
        if part.startswith("_") and not (part.startswith("__") and part.endswith("__")):
            return True
    return False


def contains(outer, inner):
    return outer is not inner and outer.lineno <= inner.lineno and inner.end_lineno <= outer.end_lineno


class FileScanner(ast.NodeVisitor):
    def __init__(self, src, rel_path, names):
        self.src = src
        self.lines = src.splitlines()
        self.rel_path = rel_path
        self.names = names
        self.local = {}          # MODULE scope: local name -> where it really comes from
        self.scopes = [self.local]   # one dict per function; None value = "shadowed, not ours"
        self.attrs = {}          # tracked attributes, e.g. 'Client::self.session' -> 'requests.Session()'
        self.imported = set()    # local names bound directly by an import
        self.func_stack = []
        self.class_stack = []
        self.call_sites = []
        self.import_texts = []
        self.used_funcs = {}     # lineno -> FunctionDef node
        self.used_classes = {}   # lineno -> ClassDef node
        self.module_lines = []   # snippets of hits made outside any function/class

    # ---- imports ----
    def visit_Import(self, node):
        found = False
        for a in node.names:
            top = a.name.split(".")[0]
            if top in self.names:
                bound = a.asname or top
                self.local[bound] = a.name if a.asname else top
                self.imported.add(bound)
                found = True
        if found:
            self._note_import(node)

    def visit_ImportFrom(self, node):
        if node.level == 0 and node.module and node.module.split(".")[0] in self.names:
            for a in node.names:
                bound = a.asname or a.name
                self.local[bound] = f"{node.module}.{a.name}"
                self.imported.add(bound)
            self._note_import(node)

    def _note_import(self, node):
        text = ast.get_source_segment(self.src, node)
        if text and text not in self.import_texts:
            self.import_texts.append(text)

    # ---- functions and classes (to know where a hit lives) ----
    def _visit_func(self, node):
        # Each function gets its own variable table so 'resp' in one function
        # is not confused with 'resp' in another. Parameters shadow outer names;
        # an annotation like `s: requests.Session` makes the parameter tracked.
        a = node.args
        params = a.posonlyargs + a.args + a.kwonlyargs + [x for x in (a.vararg, a.kwarg) if x]
        scope = {}
        for p in params:
            o = self._origin(p.annotation) if p.annotation is not None else None
            scope[p.arg] = (o + "()") if o else None
        self.func_stack.append(node)
        self.scopes.append(scope)
        self.generic_visit(node)
        self.scopes.pop()
        self.func_stack.pop()

    visit_FunctionDef = _visit_func
    visit_AsyncFunctionDef = _visit_func

    def visit_ClassDef(self, node):
        self.class_stack.append(node)
        self.generic_visit(node)
        self.class_stack.pop()

    # ---- tracking names that hold dependency objects ----
    def _lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]      # may be None (shadowed)
        return None

    def _attr_key(self, d):
        return f"{self.class_stack[-1].name}::{d}" if self.class_stack else d

    def _value_origin(self, value):
        if isinstance(value, ast.Call):
            o = self._origin(value.func)            # s = requests.Session()
            return (o + "()") if o else None
        if dotted(value):
            return self._origin(value)              # orig = requests.Session.request
        return None

    def _bind_target(self, target, origin):
        if isinstance(target, ast.Name):
            if target.id in self.imported:          # keep `requests = None` fallbacks from wiping tracking
                return
            self.scopes[-1][target.id] = origin     # None = this name is no longer ours
        elif isinstance(target, ast.Attribute):     # self.session = requests.Session()
            d = dotted(target)
            if d:
                key = self._attr_key(d)
                if origin:
                    self.attrs[key] = origin
                else:
                    self.attrs.pop(key, None)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts:
                self._bind_target(e, None)

    def visit_Assign(self, node):
        self.generic_visit(node)
        origin = self._value_origin(node.value)
        for t in node.targets:
            self._bind_target(t, origin)

    def visit_AnnAssign(self, node):
        self.generic_visit(node)
        if node.value is not None:
            self._bind_target(node.target, self._value_origin(node.value))

    def visit_With(self, node):
        self.generic_visit(node)
        for item in node.items:
            if item.optional_vars is not None:
                self._bind_target(item.optional_vars, self._value_origin(item.context_expr))

    visit_AsyncWith = visit_With

    # ---- hits ----
    def _origin(self, node):
        d = dotted(node)
        if not d:
            return None
        parts = d.split(".")
        for i in range(len(parts), 0, -1):          # longest match first
            key = ".".join(parts[:i])
            base = self._lookup(key) if i == 1 else self.attrs.get(self._attr_key(key))
            if base:
                rest = ".".join(parts[i:])
                return base + (f".{rest}" if rest else "")
        return None

    def _record(self, node, origin, kind):
        func = self.func_stack[-1] if self.func_stack else None
        klass = self.class_stack[-1] if self.class_stack else None
        snippet = self.lines[node.lineno - 1].strip()
        if func:
            where = func.name
            self.used_funcs[func.lineno] = func
        elif klass:
            where = f"class {klass.name}"
            self.used_classes[klass.lineno] = klass
        else:
            where = "<module>"
            if snippet not in self.module_lines:
                self.module_lines.append(snippet)
        self.call_sites.append({
            "file": self.rel_path,
            "line": node.lineno,
            "calling_function": where,
            "code_snippet": snippet,
            "symbol": origin,
            "kind": kind,
            "private_api": is_private(origin),
        })

    def visit_Call(self, node):
        origin = self._origin(node.func)
        if origin:
            self._record(node, origin, "call")
            for a in node.args:
                self.visit(a)
            for k in node.keywords:
                self.visit(k)
        else:
            self.generic_visit(node)

    def visit_Attribute(self, node):
        if dotted(node) is None:      # e.g. f().x -> look inside
            self.generic_visit(node)
            return
        origin = self._origin(node)
        if origin:
            kind = "assign" if isinstance(node.ctx, (ast.Store, ast.Del)) else "reference"
            self._record(node, origin, kind)

    def visit_Name(self, node):
        if node.id in self.imported and isinstance(node.ctx, ast.Load):
            origin = self._lookup(node.id)
            if origin:
                self._record(node, origin, "reference")

    # ---- context for Gemma ----
    def _segment(self, node):
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])  # keep decorators
        return textwrap.dedent("\n".join(self.lines[start - 1:node.end_lineno]))

    def context_block(self):
        parts = list(self.import_texts)
        nodes = list(self.used_funcs.values()) + list(self.used_classes.values())
        nodes = [n for n in nodes if not any(contains(o, n) for o in nodes)]
        for n in sorted(nodes, key=lambda n: n.lineno):
            parts.append(self._segment(n))
        parts.extend(self.module_lines)
        return f"# file: {self.rel_path}\n" + "\n\n".join(parts)


_PARSE_CACHE = {}   # (path, mtime, size) -> (src, tree or None); each file is parsed once across all packages


def _load_tree(path, rel_path):
    try:
        st = os.stat(path)
        key = (path, st.st_mtime_ns, st.st_size)
    except OSError:
        return None, None
    if key in _PARSE_CACHE:
        return _PARSE_CACHE[key]
    try:
        with open(path, "r", encoding="utf-8-sig") as f:    # -sig: tolerate a BOM
            src = f.read()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")                  # e.g. invalid escape sequences in fixtures
            tree = ast.parse(src, filename=rel_path)
        result = (src, tree)
    except (SyntaxError, UnicodeDecodeError, OSError, ValueError, MemoryError, RecursionError):
        result = (None, None)
    if len(_PARSE_CACHE) > 4000:
        _PARSE_CACHE.clear()
    _PARSE_CACHE[key] = result
    return result


def scan_file(path, rel_path, names):
    """Returns (call_sites, context_block, parsed_ok)."""
    src, tree = _load_tree(path, rel_path)
    if tree is None:
        return [], "", False
    if not any(n in src for n in names):      # cannot contain a hit: skip the full visit
        return [], "", True
    scanner = FileScanner(src, rel_path, names)
    scanner.visit(tree)
    if not scanner.call_sites:
        return [], "", True
    return scanner.call_sites, scanner.context_block(), True


def build_context(blocks):
    """blocks: [(hit_count, text)]. Busiest files first; cut only between files."""
    parts, used, omitted = [], 0, 0
    for _, text in sorted(blocks, key=lambda b: -b[0]):
        if len(text) > MAX_CONTEXT_CHARS:
            text = text[:MAX_CONTEXT_CHARS] + "\n# ... truncated"
        if parts and used + len(text) > MAX_CONTEXT_CHARS:
            omitted += 1
            continue
        parts.append(text)
        used += len(text) + 2
    if omitted:
        parts.append(f"# ... {omitted} more file(s) omitted (context limit)")
    return "\n\n".join(parts), omitted > 0


def scan_repo(repo_path, target_pkg):
    if not os.path.isdir(repo_path):
        raise SystemExit(f"ERROR: repo folder not found: {os.path.abspath(repo_path)}")
    names = import_names(target_pkg)
    call_sites, test_call_sites, blocks, unparsed = [], [], [], []
    scanned = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(root, fname)
            rel = os.path.relpath(path, repo_path).replace(os.sep, "/")
            sites, block, ok = scan_file(path, rel, names)
            scanned += ok
            if not ok:
                unparsed.append(rel)      # never silently skip a file: report it
                continue
            if is_test_path(rel):
                test_call_sites.extend(sites)
            else:
                call_sites.extend(sites)
                if block:
                    blocks.append((len(sites), block))

    radius = compute_blast_radius(call_sites)
    context, truncated = build_context(blocks)

    return {
        "target_package": target_pkg,
        "blast_radius_score": radius["score"],
        "hero_file": radius["hero_file"],
        "call_sites": call_sites,
        "test_call_sites": test_call_sites,
        "context_code": context,
        "context_truncated": truncated,
        "unparsed_files": unparsed,
        "files_scanned": scanned,
    }


if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "demo_repo"
    pkg = sys.argv[2] if len(sys.argv) > 2 else "requests"

    result = scan_repo(repo, pkg)
    print(f"[Person 2] Scanned '{repo}' for '{pkg}'")
    print(f"Hero file:    {result['hero_file']}")
    print(f"Blast radius: {result['blast_radius_score']}/100")
    print(f"Call sites:   {len(result['call_sites'])}  (+ {len(result['test_call_sites'])} in test files, not scored)")
    print(f"Python files scanned: {result['files_scanned']}")
    if result["files_scanned"] == 0:
        print(f"WARNING: no .py files found under {os.path.abspath(repo)} - wrong folder? (unzipped into a nested folder?)")
    if result["unparsed_files"]:
        print(f"WARNING could not parse (NOT scanned): {', '.join(result['unparsed_files'])}")
    for cs in result["call_sites"]:
        flag = "  [PRIVATE API]" if cs["private_api"] else ""
        print(f"  {cs['file']}:{cs['line']}  {cs['kind']:<9} {cs['calling_function']}  ->  {cs['symbol']}{flag}")

    if len(sys.argv) > 3:
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"Saved -> {sys.argv[3]}")
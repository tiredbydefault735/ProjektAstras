import os
import ast


def get_python_files(root_dir):
    python_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        if (
            "venv" in dirpath
            or ".git" in dirpath
            or "__pycache__" in dirpath
            or "build" in dirpath
            or "dist" in dirpath
        ):
            continue
        for filename in filenames:
            if filename.endswith(".py"):
                python_files.append(os.path.join(dirpath, filename))
    return python_files


def analyze_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return None

    classes = {}
    functions = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(item.name)
            classes[node.name] = methods
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)

    return classes, functions


def generate_markdown(root_dir, output_file):
    files = get_python_files(root_dir)
    exclude_files = ["tools\\generate_docs.py", "generate_docs.py"]

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("# Projekt Dokumentation - Klassen und Funktionen\n\n")

        for filepath in sorted(files):
            if any(filepath.endswith(exc) for exc in exclude_files):
                continue

            rel_path = os.path.relpath(filepath, root_dir)
            result = analyze_file(filepath)
            if not result:
                continue

            classes, functions = result

            if not classes and not functions:
                continue

            out.write(f"## Datei: `{rel_path}`\n\n")

            if classes:
                for cls_name, methods in classes.items():
                    out.write(f"### Klasse: `{cls_name}`\n")
                    if methods:
                        for method in methods:
                            out.write(f"- `{method}`\n")
                    else:
                        out.write("- *(Keine Methoden)*\n")
                    out.write("\n")

            if functions:
                out.write("### Modul-Funktionen\n")
                for func in functions:
                    out.write(f"- `{func}`\n")
                out.write("\n")

            out.write("---\n\n")


if __name__ == "__main__":
    generate_markdown(".", "docs/API_Reference.md")
    print("Dokumentation wurde in docs/API_Reference.md erstellt.")

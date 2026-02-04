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


def get_id_from_node(node):
    """Helper to extract identifier from various AST nodes."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return node.attr
    return None


def analyze_file_for_mermaid(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return []

    classes_info = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = []
            relationships = set()

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    visibility = (
                        "-"
                        if item.name.startswith("_") and not item.name.startswith("__")
                        else "+"
                    )
                    methods.append(f"{visibility}{item.name}()")

                    # Check arguments for Type Hints (Association)
                    for arg in item.args.args:
                        if arg.annotation:
                            type_name = get_id_from_node(arg.annotation)
                            if type_name:
                                relationships.add((type_name, "association"))

                    # Check body for Instantiation/Usage (Composition/Dependency)
                    for stmt in ast.walk(item):  # Walk recursively in function
                        # self.attr = ClassName(...)
                        if isinstance(stmt, ast.Assign):
                            for target in stmt.targets:
                                if (
                                    isinstance(target, ast.Attribute)
                                    and isinstance(target.value, ast.Name)
                                    and target.value.id == "self"
                                ):
                                    if isinstance(stmt.value, ast.Call):
                                        func_name = get_id_from_node(stmt.value.func)
                                        if func_name:
                                            relationships.add(
                                                (func_name, "composition")
                                            )

                        # Calling a class directly could also be a dependency
                        if isinstance(stmt, ast.Call):
                            func_name = get_id_from_node(stmt.func)
                            if func_name:
                                # Differentiate between simple calls and instantiation is hard without deep analysis,
                                # but if it matches a class name, it's a relationship.
                                # "dependency" .>
                                relationships.add((func_name, "dependency"))

            bases = []
            for base in node.bases:
                base_id = get_id_from_node(base)
                if base_id:
                    bases.append(base_id)

            classes_info.append(
                {
                    "name": node.name,
                    "methods": methods,
                    "bases": bases,
                    "relationships": relationships,
                }
            )

    return classes_info


def generate_mermaid(root_dir, output_file):
    files = get_python_files(root_dir)
    all_classes = []

    for filepath in sorted(files):
        infos = analyze_file_for_mermaid(filepath)
        if infos:
            all_classes.extend(infos)

    known_class_names = {c["name"] for c in all_classes}

    with open(output_file, "w", encoding="utf-8") as out:
        out.write("```mermaid\n")
        out.write("classDiagram\n")

        # Write classes definitions
        for info in all_classes:
            out.write(f"    class {info['name']} {{\n")
            for m in info["methods"]:
                out.write(f"        {m}\n")
            out.write("    }\n")

        out.write("\n")

        for info in all_classes:
            # Inheritance
            for base in info["bases"]:
                if base in known_class_names:
                    out.write(f"    {base} <|-- {info['name']}\n")

            # Relationships
            # Use a set to avoid dupes for this class
            processed_rels = set()
            for target_cls, rel_type in info["relationships"]:
                if target_cls in known_class_names and target_cls != info["name"]:
                    rel_key = (target_cls, rel_type)
                    if rel_key in processed_rels:
                        continue
                    processed_rels.add(rel_key)

                    if rel_type == "composition":
                        out.write(f"    {info['name']} *-- {target_cls}\n")
                    elif rel_type == "association":
                        out.write(f"    {info['name']} --> {target_cls}\n")
                    elif rel_type == "dependency":
                        # If we already have composition or association, don't draw dependency (less specific)
                        if (target_cls, "composition") not in processed_rels and (
                            target_cls,
                            "association",
                        ) not in processed_rels:
                            out.write(f"    {info['name']} ..> {target_cls}\n")

        out.write("```\n")


if __name__ == "__main__":
    generate_mermaid(".", "docs/class_diagram.mermaid")
    print("Mermaid diagram generated in docs/class_diagram.mermaid")

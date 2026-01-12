import json, re


def inspect_file(path):
    try:
        json.load(open(path, encoding="utf-8-sig"))
        print(f"{path}: OK")
    except Exception as e:
        print(f"{path}: ERR {repr(e)}")
        try:
            with open(path, encoding="utf-8-sig") as fh:
                lines = fh.readlines()
        except Exception:
            print("Could not read file for context")
            return
        m = re.search(r"line (\d+)", repr(e))
        err_line = int(m.group(1)) if m else None
        if err_line:
            start = max(0, err_line - 6)
            end = min(len(lines), err_line + 4)
            print("---", path, "lines", start + 1, "-", end, "---")
            for i in range(start, end):
                print(f"{i+1:4d}: {lines[i].rstrip()}")


if __name__ == "__main__":
    inspect_file("i18n/en.json")
    inspect_file("i18n/de.json")

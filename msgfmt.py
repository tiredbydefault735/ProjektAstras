#!/usr/bin/env python3
"""Simple msgfmt: compile a .po file to a .mo file.
Creates output suitable for gettext.translation(domain, localedir).
Usage: python msgfmt.py input.po output.mo
"""
import sys, os, struct


def parse_po(filename):
    entries = {}
    msgid = None
    msgstr = None
    state = None
    with open(filename, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if line.startswith("#") or line.strip() == "":
                continue
            if line.startswith("msgid "):
                msgid = eval(line[6:])
                msgstr = ""
                state = "id"
            elif line.startswith("msgstr "):
                msgstr = eval(line[7:])
                state = "str"
            elif line.startswith('"'):
                txt = eval(line)
                if state == "id":
                    msgid += txt
                elif state == "str":
                    msgstr += txt
            else:
                # On any other non-string token, flush current pair
                if msgid is not None:
                    entries[msgid] = msgstr
                msgid = None
                msgstr = None
                state = None
    if msgid is not None:
        entries[msgid] = msgstr
    # Remove header entry if empty msgid
    if "" in entries:
        entries.pop("")
    return entries


def write_mo(translations, filename):
    """Write translations (dict) to a GNU .mo file."""
    keys = sorted(translations.keys())
    ids = "\0".join(keys).encode("utf-8") + b"\0"
    strs = "\0".join(translations[k] for k in keys).encode("utf-8") + b"\0"
    import io
    import struct

    n = len(keys)
    # Offsets
    # header = 7*4 bytes
    # original table: each entry is (length, offset) * n -> 8*n bytes
    # translation table: same -> 8*n bytes
    # original strings start after header + 16*n
    off_orig_table = 7 * 4
    off_trans_table = off_orig_table + 8 * n
    off_ids = off_trans_table + 8 * n
    ids_block = ids
    strs_block = strs
    # build tables
    orig_table = b""
    trans_table = b""
    cur = off_ids
    for k in keys:
        kb = k.encode("utf-8")
        orig_table += struct.pack("<II", len(kb), cur)
        cur += len(kb) + 1
    cur = off_ids + len(ids_block)
    for k in keys:
        sb = translations[k].encode("utf-8")
        trans_table += struct.pack("<II", len(sb), cur)
        cur += len(sb) + 1
    # header fields
    magic = 0x950412DE
    version = 0
    hash_size = 0
    hash_offset = 0
    header = struct.pack(
        "<Iiiiiii",
        magic,
        version,
        n,
        off_orig_table,
        off_trans_table,
        hash_size,
        hash_offset,
    )
    with open(filename, "wb") as f:
        f.write(header)
        f.write(orig_table)
        f.write(trans_table)
        f.write(ids_block)
        f.write(strs_block)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python msgfmt.py input.po output.mo")
        sys.exit(2)
    inp = sys.argv[1]
    out = sys.argv[2]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    translations = parse_po(inp)
    write_mo(translations, out)
    print("Wrote", out)

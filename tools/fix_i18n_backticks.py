files = ["i18n/en.json", "i18n/de.json"]
for f in files:
    try:
        b = open(f, "rb").read()
        s = b.decode("utf-8-sig")
    except Exception as e:
        print("ERR read", f, e)
        continue
    s2 = s.replace("`n", "")
    if s2 != s:
        open(f, "w", encoding="utf-8").write(s2)
        print("fixed", f)
    else:
        print("nochange", f)

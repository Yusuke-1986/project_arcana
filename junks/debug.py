def debug_braces(lines):
    depth = 0
    for ln, raw in enumerate(lines, 1):
        # strip inline comment '///' outside strings
        s = raw.rstrip("\n")
        in_s = in_d = False
        esc = False
        i = 0
        cut = len(s)
        while i < len(s):
            ch = s[i]
            if esc:
                esc = False; i += 1; continue
            if ch == "\\":
                esc = True; i += 1; continue
            if ch == "'" and not in_d:
                in_s = not in_s; i += 1; continue
            if ch == '"' and not in_s:
                in_d = not in_d; i += 1; continue
            if not in_s and not in_d and s.startswith("///", i):
                cut = i
                break
            i += 1
        s = s[:cut]

        # count braces outside strings
        in_s = in_d = False
        esc = False
        for ch in s:
            if esc:
                esc = False; continue
            if ch == "\\":
                esc = True; continue
            if ch == "'" and not in_d:
                in_s = not in_s; continue
            if ch == '"' and not in_s:
                in_d = not in_d; continue
            if not in_s and not in_d:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth < 0:
                        print("extra } at line", ln, raw)
                        return
        if in_s or in_d:
            print("unclosed quote at line", ln, raw)
            return

    print("final depth =", depth)
    if depth != 0:
        print("missing", depth, "closing }")

with open("sample.arkhe", "r", encoding="utf-8") as f:
    debug_braces(f.readlines())

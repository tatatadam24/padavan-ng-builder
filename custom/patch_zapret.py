import re
import sys

ASP = "padavan-ng/trunk/user/www/n56u_ribbon_fixed/Advanced_Services_Zapret.asp"
SH = "padavan-ng/trunk/user/zapret/zapret.sh"
VARS = "padavan-ng/trunk/user/httpd/variables.c"
INDEX = "custom/zapret/strategies.list"
UI_LIMIT = 8192


def die(msg):
    print(f"::error::patch_zapret: {msg}")
    sys.exit(1)


def sub(text, pattern, repl, count, what):
    new, n = re.subn(pattern, lambda m: m.expand(repl), text, flags=re.M)
    if n != count:
        die(f"{what}: expected {count} match(es), got {n}")
    return new


def rw(path, fn):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    text = fn(text)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


extra = []
for line in open(INDEX, encoding="utf-8"):
    line = line.strip()
    if line:
        slug, label = line.split("|", 1)
        if not re.fullmatch(r"_[a-z0-9_]+", slug):
            die(f"bad slug {slug!r}")
        extra.append((slug, label))
extra.sort(key=lambda s: s[0] != "_general")
suffixes = ["", "5"] + [s for s, _ in extra]
js_array = "[" + ", ".join(f'"{s}"' for s in suffixes) + "]"


def patch_asp(asp):
    asp = sub(asp, r'^function textarea_zapret_enabled\(v\)\{$',
              f"const ZAPRET_STRATEGIES = {js_array};\n\n" + r"\g<0>", 1, "strategies const")
    asp = sub(asp, r'\["", 0, 1, 2, 3, 4, 5, 6, 7, 8, 9\]', "ZAPRET_STRATEGIES", 2, "js strategy loops")

    # post only the selected strategy: all of them together may not fit into httpd post buffer
    asp = sub(asp, r'(document\.form\.current_page\.value = "/Advanced_Services_Zapret\.asp";\n\t\tdocument\.form\.next_page\.value = "";\n)',
              r"\1\t\tfor (const i of ZAPRET_STRATEGIES)\n"
              r"\t\t\tif (i != document.form.zapret_strategy.value) document.form['zapretc.strategy' + i].disabled = true;\n",
              1, "apply: post selected strategy only")

    asp = sub(asp, r"rm -f \./strategy \./strategy\[0-9\];", "rm -f ./strategy ./strategy[0-9] ./strategy_*;", 1, "restore command")

    asp = sub(asp, r'^[ \t]*<option value="[0-46-9]" <% nvram_match_x\("", "zapret_strategy".*\n', "", 9, "strategy options")
    asp = sub(asp, r'(<option value="" <% nvram_match_x\("", "zapret_strategy", "","selected"\); %>>)<#ZapretDefaultProfile#>', r"\1ALT9", 1, "ALT9 option")
    options = "".join(
        f'\n\\1<option value="{s}" <% nvram_match_x("", "zapret_strategy", "{s}","selected"); %>>{label}</option>'
        for s, label in extra)
    asp = sub(asp, r'^([ \t]*)(<option value="5" <% nvram_match_x\("", "zapret_strategy", "5","selected"\); %>>)<#ZapretStrategyProfile#> #5</option>',
              r"\1\2Router 5</option>" + options, 1, "Router 5 + extra options")

    asp = sub(asp, r'^[ \t]*<textarea [^\n]*name="zapretc\.strategy[0-46-9]"[^\n]*\n', "", 9, "strategy textareas")
    asp = sub(asp, r'(<textarea [^\n]*)maxlength="4096"([^\n]*name="zapretc\.strategy5?")', rf'\1maxlength="{UI_LIMIT}"\2', 2, "textarea maxlength")
    areas = "".join(
        f'\n\\1<textarea rows="20" spellcheck="false" maxlength="{UI_LIMIT}" class="span12 strategy" id="zapretc.strategy{s}" '
        f'name="zapretc.strategy{s}"><% nvram_dump("zapretc.strategy{s}",""); %></textarea>'
        for s, _ in extra)
    asp = sub(asp, r'^([ \t]*)(<textarea [^\n]*name="zapretc\.strategy5"[^\n]*</textarea>)$', r"\1\2" + areas, 1, "extra textareas")
    return asp


def patch_vars(c):
    entries = "".join(f'\n\\1{{"zapretc.strategy{s}", "File", NULL, EVM_RESTART_ZAPRET}},' for s, _ in extra)
    return sub(c, r'^([ \t]*)(\{"zapretc\.strategy9", "File", NULL, EVM_RESTART_ZAPRET\},)$', r"\1\2" + entries, 1, "httpd variables")


def patch_sh(sh):
    return sub(sh, r'^(STRATEGY_FILE="\$\{STRATEGY_FILE\}\$\(nvram get zapret_strategy\)"\n)',
               r'\1[ -s "$STRATEGY_FILE" ] || STRATEGY_FILE="$CONF_DIR/strategy"\n', 1, "strategy fallback")


rw(ASP, patch_asp)
rw(VARS, patch_vars)
rw(SH, patch_sh)
print(f"patch_zapret: ok, {len(suffixes)} strategies in web UI")

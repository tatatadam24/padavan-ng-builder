import re
import sys

ASP = "padavan-ng/trunk/user/www/n56u_ribbon_fixed/Advanced_Services_Zapret.asp"
SH = "padavan-ng/trunk/user/zapret/zapret.sh"


def die(msg):
    print(f"::error::patch_zapret: {msg}")
    sys.exit(1)


def sub(text, pattern, repl, count, what):
    new, n = re.subn(pattern, repl, text, flags=re.M)
    if n != count:
        die(f"{what}: expected {count} match(es), got {n}")
    return new


with open(ASP, encoding="utf-8") as f:
    asp = f.read()

asp = sub(asp, r'\["", 0, 1, 2, 3, 4, 5, 6, 7, 8, 9\]', '["", 5]', 2, "js strategy loops")
asp = sub(asp, r'^[ \t]*<option value="[0-46-9]" <% nvram_match_x\("", "zapret_strategy".*\n', "", 9, "strategy options")
asp = sub(asp, r'(<option value="" <% nvram_match_x\("", "zapret_strategy", "","selected"\); %>>)<#ZapretDefaultProfile#>', r"\1ALT9", 1, "ALT9 option")
asp = sub(asp, r'(<option value="5" <% nvram_match_x\("", "zapret_strategy", "5","selected"\); %>>)<#ZapretStrategyProfile#> #5', r"\1Router 5", 1, "Router 5 option")
asp = sub(asp, r'^[ \t]*<textarea [^\n]*name="zapretc\.strategy[0-46-9]"[^\n]*\n', "", 9, "strategy textareas")

with open(ASP, "w", encoding="utf-8") as f:
    f.write(asp)

with open(SH, encoding="utf-8") as f:
    sh = f.read()

sh = sub(sh, r'^(STRATEGY_FILE="\$\{STRATEGY_FILE\}\$\(nvram get zapret_strategy\)"\n)',
         r'\1[ -s "$STRATEGY_FILE" ] || STRATEGY_FILE="$CONF_DIR/strategy"\n', 1, "strategy fallback")

with open(SH, "w", encoding="utf-8") as f:
    f.write(sh)

print("patch_zapret: ok")

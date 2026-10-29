"""Convert Flowseal zapret-discord-youtube general*.bat strategies to padavan nfqws strategy files.

usage: python convert_flowseal.py <zapret-discord-youtube dir> <custom/zapret dir>
"""
import glob
import os
import re
import shutil
import sys

LISTS = "/usr/share/zapret/lists/"
FAKE = "/usr/share/zapret/fake/flowseal/"
USER_HOSTLIST = "/etc/storage/zapret/user.list"
USER_EXCLUDE = "/etc/storage/zapret/exclude.list"
USER_IPSET = "/etc/storage/zapret/ipset.list"
LIST_FILES = ["ipset-all.txt", "list-general.txt", "list-google.txt", "list-exclude.txt"]
GAME_PORTS = "1024-65535"
DEFAULT = "ALT9"
UI_LIMIT = 8192


def label_of(bat):
    m = re.match(r"general(?: \((.+)\))?\.bat$", os.path.basename(bat))
    return m.group(1) or "general"


def slug_of(label):
    return "_" + re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def winws_args(text):
    text = re.sub(r"\^\r?\n", " ", text)
    m = re.search(r'winws\.exe"\s+([^\r\n]+)', text)
    if not m:
        raise ValueError("winws.exe command line not found")
    return re.findall(r'(?:[^\s"]+|"[^"]*")+', m.group(1))


def convert_arg(t, used_fakes):
    t = t.replace('"', "")
    name, _, val = t.partition("=")
    base = os.path.basename(val.replace("%LISTS%", "").replace("%BIN%", ""))
    if name == "--ipset-exclude":
        return []  # private nets are excluded by zapret.sh via iptables
    if base == "list-general-user.txt":
        return [f"{name}={USER_HOSTLIST}"]
    if base == "list-exclude-user.txt":
        return [f"{name}={USER_EXCLUDE}"]
    if "%LISTS%" in val:
        if base not in LIST_FILES:
            raise ValueError(f"unknown list {base}")
        out = [f"{name}={LISTS}{base}"]
        if name == "--ipset" and base == "ipset-all.txt":
            out.append(f"--ipset={USER_IPSET}")
        return out
    if "%BIN%" in val:
        used_fakes.add(base)
        return [f"{name}={FAKE}{base}"]
    if "%GameFilter" in val:
        return [f"{name}={val.replace('%GameFilterTCP%', GAME_PORTS).replace('%GameFilterUDP%', GAME_PORTS)}"]
    if "%" in t:
        raise ValueError(f"unresolved variable in {t}")
    return [t]


def convert(bat, used_fakes):
    tokens = winws_args(open(bat, encoding="utf-8", errors="replace").read())
    profiles, cur = [], []
    for t in tokens:
        if t.startswith("--wf-"):
            continue
        if t == "--new":
            profiles.append(cur)
            cur = []
        else:
            cur.append(t)
    profiles.append(cur)

    blocks = []
    for p in (p for p in profiles if p):
        game = any("%GameFilter" in t for t in p)
        args = [a for t in p for a in convert_arg(t, used_fakes)]
        blocks.append((game, args))

    label = label_of(bat)
    out = [f"### Flowseal zapret-discord-youtube \"{label}\""]
    first, game_header = True, False
    for game, args in blocks:
        if game:
            if not game_header:
                out.append("### games (Game Filter), disabled: remove leading # to enable")
                game_header = True
            out += ["#--new"] + ["#" + a for a in args]
            continue
        if not first:
            out.append("--new")
        out += args
        first = False
    return "\n".join(out) + "\n"


def main():
    src, dst = sys.argv[1], sys.argv[2]
    strat_dir = os.path.join(dst, "strategies")
    fake_dir = os.path.join(dst, "fake", "flowseal")
    for d in (strat_dir, fake_dir, os.path.join(dst, "lists")):
        os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(strat_dir, "strategy_*")):
        os.remove(f)

    used_fakes, index = set(), []
    for bat in sorted(glob.glob(os.path.join(src, "general*.bat")), key=lambda b: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", label_of(b))]):
        label = label_of(bat)
        content = convert(bat, used_fakes)
        if len(content) > UI_LIMIT:
            raise ValueError(f"{label}: {len(content)} chars, web UI limit is {UI_LIMIT}")
        fn = "strategy" if label == DEFAULT else "strategy" + slug_of(label)
        path = os.path.join(dst if label == DEFAULT else strat_dir, fn)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        if label != DEFAULT:
            index.append(f"{slug_of(label)}|{label}")
        print(f"{fn:34} {len(content):5}  {label}")

    with open(os.path.join(dst, "strategies.list"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(index) + "\n")

    for name in sorted(used_fakes):
        shutil.copyfile(os.path.join(src, "bin", name), os.path.join(fake_dir, name))
    for name in LIST_FILES:
        data = open(os.path.join(src, "lists", name), "rb").read().replace(b"\r\n", b"\n")
        open(os.path.join(dst, "lists", name), "wb").write(data)
    print("fakes:", ", ".join(sorted(used_fakes)))


if __name__ == "__main__":
    main()

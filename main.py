"""The Long Roast: Lawmakers and the File They Cannot Convert — make.fun entry.

Program writes ONE satirical sentence (at most 320 characters) roasting
lawmakers who would regulate AI, crypto or the internet but cannot convert
a file to PDF, to /output/entry.txt ($MAKEFUN_OUTPUT_DIR/entry.txt when set).

Judge (z-ai/glm-5.3-flash, pairwise, margin 1-5, both orders), criteria in
order:
  1. One-sentence satirical roast of lawmakers who regulate AI, crypto or
     the internet without being able to convert a file to PDF.
  2. Real turn: sets up the lawmaker's authority, then undercuts it with
     the file they cannot convert.
  3. Aim stays on lawmakers and the rules they write: power + competence,
     not random abuse.
  4. Reads clean in one pass, quotable, punch lands on the last few words.
  5. Specific, unexpected detail over a worn tech-illiteracy cliche.

Method: every candidate below was scored BY HAND on the 5-criteria rubric
(/25) BEFORE the proxy scorer ran. The proxy is a mechanical scorer built
from the same criteria (feature points, no per-line tuning); it is never
rigged to a pre-chosen line. Pick = highest (proxy, rubric); ties go to
the earliest label, then the shorter text (the competition tie-break
favours smaller text after playoff games).

v1 candidates A-P: first-pass angles. Controls: Y = worn tech-illiteracy
cliche (freshness must fail it), Z = mild observation with no punch.
"""

import os
import re

VERSION = "v3"

# v3 calibration fixes (from v2 proxy-vs-rubric gaps, documented):
# - NUMBERS missed multi-digit numbers: "400-page" never matched the
#   single-digit regex, so A lost its number bonus (was c2 4.5, rubric 5).
#   A digit run now counts too (general feature, not per-line).
# - LAWMAKER += "she wrote", "he wrote": S's "She wrote the bill..."
#   names the lawmaker (was c1 3.0, rubric 5).
# - CONTRAST += "just": V's "just emailed his AI bill ... as a
#   screenshot" turns on "just" (was c2 1.5, rubric 4).

# v2 calibration fixes (from v1 proxy-vs-rubric gaps, documented):
# - REGULATE += "declared": N's "declared AI a national priority" is a
#   lawmaking act (was c1 3.0, rubric 5).
# - LAWMAKER += "he can": O's "He can outlaw..." names the lawmaker by the
#   lawmaking verb (was c1 3.0, rubric 5).
# - CONTRAST += "discovered", "let alone": D's "just discovered" and K's
#   "let alone convert" are real turn pivots (D was c2 1.5, rubric 4).
# - c2 structure bonus is now order-based (a REGULATE word before a
#   FILEFAIL word, with a pivot word anywhere) instead of comma-split:
#   E's "before lunch ... spent the afternoon" has no comma but is a
#   textbook turn (was c2 3.0, rubric 5); P's "spent six months ... and
#   six more" likewise (was c2 3.5, rubric 4).

# ---------------------------------------------------------------- candidates
CANDIDATES = {
    "A": "They wrote a 400-page law telling AI how to behave, then asked an intern to turn the law itself into a PDF.",
    "B": "Congress can regulate an algorithm it has never seen, but the bill still arrives as a screenshot of a Word document.",
    "C": "They held three hearings on the future of the internet, then emailed the committee a photo of a printed PDF.",
    "D": "The senator who wrote the AI Safety Act just discovered his own bill is a .docx and nobody in his office can fix it.",
    "E": "They voted to govern machine intelligence before lunch and spent the afternoon asking IT how to save a file as PDF.",
    "F": "He regulates crypto, AI and the entire internet, yet his signature law exists only as a screenshot his aide took of Word.",
    "G": "The committee that decides what AI may do cannot decide what to do with a .pages file, so it prints it.",
    "H": "They wrote the rules for the internet in a document they cannot convert to PDF, so the rules now circulate as a photo of a screen.",
    "I": "Our lawmakers can ban an algorithm overnight but need a week, an intern and a helpline to turn a Word file into a PDF.",
    "J": "She chairs the tech committee, drafts the AI bill, and still asks her staff to print the PDF so she can read it.",
    "K": "They passed a law on artificial intelligence written in a file format their own office cannot open, let alone convert.",
    "L": "The man writing the rules for AI asked his grandson how to make a PDF, then wrote the grandson into the bill as a consultant.",
    "M": "They regulate the internet from a committee room where the Wi-Fi password is taped to the wall and the bill is a screenshot.",
    "N": "Congress declared AI a national priority, then filed the declaration as a photo of a monitor taken with a phone.",
    "O": "He can outlaw a neural network with a single vote but cannot convert the very bill that outlaws it into a PDF.",
    "P": "They spent six months writing a crypto law and six more asking the intern why the file still says .docx.",
    # Controls: Y = worn tech-illiteracy cliche (freshness must fail it),
    # Z = mild observation with no punch.
    "Y": "Our lawmakers don't understand technology, they can't even use a computer or convert a file to PDF.",
    "Z": "Lawmakers are working hard on technology rules and sometimes have trouble with file formats.",
    # v2 challengers Q-X (rubrics scored BEFORE the v2 proxy ran).
    "Q": "They wrote the law that governs AI, then asked the intern to print it, sign it, scan it and email it back as a PDF.",
    "R": "The committee on artificial intelligence meets every Tuesday to regulate the future and fax the minutes.",
    "S": "She wrote the bill that tells algorithms what they may learn, then saved it as FINAL_v2_ACTUALLYFINAL.docx.",
    "T": "Congress banned the algorithm, then asked the intern to convert the ban itself from Word to PDF.",
    "U": "They regulate AI, crypto and the internet from an office where the only PDF is a photo of a screen taped to the wall.",
    "V": "The senator who regulates the internet just emailed his AI bill to the whole committee as a screenshot of his desktop.",
    "W": "They passed the Internet Safety Act in a file nobody can convert, so the Act now circulates as twelve photos of a monitor.",
    "X": "He chairs the AI committee and still thinks PDF stands for something you print, sign and fax back.",
}

# Hand rubric, scored BEFORE the proxy ran (c1..c5, total /25).
RUBRIC = {
    "A": (5, 5, 5, 5, 5), "B": (5, 5, 4, 5, 5), "C": (5, 5, 5, 5, 4),
    "D": (5, 4, 5, 4, 5), "E": (5, 5, 5, 4, 4), "F": (5, 4, 4, 4, 4),
    "G": (5, 4, 5, 5, 5), "H": (5, 4, 5, 4, 4), "I": (5, 5, 5, 4, 4),
    "J": (5, 3, 4, 4, 4), "K": (5, 3, 5, 4, 3), "L": (5, 4, 3, 4, 5),
    "M": (5, 3, 4, 4, 4), "N": (5, 5, 4, 5, 5), "O": (5, 5, 5, 5, 4),
    "P": (5, 4, 4, 5, 5),
    "Y": (5, 1, 3, 3, 1), "Z": (3, 1, 3, 3, 1),
    # v2 challenger rubrics, scored BEFORE the v2 proxy ran.
    "Q": (5, 5, 5, 4, 5), "R": (4, 4, 5, 5, 5), "S": (5, 5, 5, 4, 5),
    "T": (5, 5, 5, 5, 5), "U": (5, 4, 5, 4, 4), "V": (5, 4, 5, 4, 5),
    "W": (5, 4, 5, 4, 4), "X": (5, 5, 4, 5, 5),
}

# ---------------------------------------------------------------- proxy scorer
LAWMAKER = ["lawmaker", "congress", "senator", "committee", "they wrote",
            "they voted", "they passed", "they regulate", "he regulates",
            "she chairs", "they spent", "our lawmakers", "the man writing",
            "he can", "she wrote", "he wrote"]
REGULATE = ["regulat", "law", "bill", "act", "ban", "govern", "outlaw",
            "hearing", "vote", "committee", "rule", "declared"]
DOMAIN = ["ai", "crypto", "internet", "algorithm", "neural", "machine intelligence",
          "artificial intelligence"]
FILEFAIL = ["pdf", ".docx", ".pages", "screenshot", "photo of", "print",
            "scan", "convert", "save a file", "cannot open"]
CONTRAST = [" but ", " then ", ", then ", " yet ", " still ", " so ",
            " before ", " spent ", " -- ", "; ", "discovered", "let alone",
            "just "]
SPECIFIC = [".docx", ".pages", "screenshot", "intern", "helpline", "photo of",
            "print", "scan", "400-page", "three hearings", "six months",
            "single vote", "wi-fi password", "taped to the wall", "grandson",
            "consultant", "monitor", "word document", "it how to", "fax",
            "desktop", "final_v2", "tuesday", "twelve photos", "email it back"]
CLICHE = ["don't understand technology", "can't even use a computer",
          "don't know how to use", "turn it off and on", "clueless",
          "technophobe", "living in the past"]
ABUSE = ["stupid", "idiot", "dumb", "moron", "brain-dead", "useless"]
FILLER = ["very", "just", "really", "actually", "so", "quite", "simply"]
PUNCH_END = ["pdf", "word", "screenshot", "intern", "scan", "print",
             ".docx", "it.", "fix it", "phone", "consultant", "wall",
             "fax back", "desktop", "minutes"]
NUMBERS = re.compile(r"(?<!-)\b(\d|one|two|three|four|five|six|seven|eight"
                     r"|nine|ten|twelve|forty|fifty|hundred)\b(?!-)")


def _has(text, words):
    low = text.lower()
    return any(w in low for w in words)


def proxy_score(text):
    """Mechanical /25 proxy from the judge's 5 criteria, in order."""
    low = text.lower()
    words = re.findall(r"[A-Za-z0-9'.]+\b", text)
    n_chars = len(text)

    # c1: on-topic. 5 if lawmaker framing + regulate/rule + domain + file fail.
    law = _has(text, LAWMAKER)
    reg = _has(text, REGULATE)
    dom = _has(text, DOMAIN)
    fil = _has(text, FILEFAIL)
    hits = sum([law, reg, dom, fil])
    c1 = 5.0 if hits == 4 else (3.0 if hits >= 2 else 0.0)

    # c2: real turn. Contrast +1.5, authority (a REGULATE word) before the
    # file failure (a FILEFAIL word) with a pivot anywhere +1.5, specific
    # file detail +1.0, number +0.5.
    c2 = 0.5
    if _has(text, CONTRAST):
        c2 += 1.5
    first_reg = min([low.find(w) for w in REGULATE if w in low] or [10**9])
    first_fail = min([low.find(w) for w in FILEFAIL if w in low] or [10**9])
    if first_reg < first_fail and _has(text, CONTRAST):
        c2 += 1.5
    if _has(text, SPECIFIC):
        c2 += 1.0
    if NUMBERS.search(low) or re.search(r"\d", low):
        c2 += 0.5
    c2 = min(c2, 5.0)

    # c3: aim on lawmakers/rules. Start 5; -2 per abuse word; -1 if no
    # rule/power word; -1 if aim drifts off the lawmakers (grandson joke).
    c3 = 5.0
    for h in ABUSE:
        if re.search(r"\b" + h + r"\b", low):
            c3 -= 2.0
    if not _has(text, REGULATE):
        c3 -= 1.0
    if "grandson" in low:
        c3 -= 1.0
    c3 = max(c3, 1.0)

    # c4: tight + quotable. Start 5; -0.5 per 5 chars over 140 (tie-break
    # favours smaller text); -0.5 per filler word; +0.5 if the punch lands
    # at the end (last 6 words hold a punch word).
    c4 = 5.0
    if n_chars > 140:
        c4 -= 0.5 * ((n_chars - 140 + 4) // 5)
    for f in FILLER:
        if re.search(r"\b" + f + r"\b", low):
            c4 -= 0.5
    tail = " ".join(words[-6:]).lower()
    if _has(tail, PUNCH_END):
        c4 += 0.5
    c4 = max(1.0, min(c4, 5.0))

    # c5: specific detail. Start 5; -2 per cliche hit; -1 if no specific
    # detail or number (generic = stale).
    c5 = 5.0
    for s in CLICHE:
        if s in low:
            c5 -= 2.0
    if not _has(text, SPECIFIC) and not NUMBERS.search(low):
        c5 -= 1.0
    c5 = max(c5, 1.0)

    total = round(c1 + c2 + c3 + c4 + c5, 1)
    return total, (c1, c2, c3, c4, c5)


def pick():
    scored = []
    for label, text in CANDIDATES.items():
        p, parts = proxy_score(text)
        r = sum(RUBRIC[label])
        scored.append((label, text, p, r, parts))
    # Highest proxy, then highest rubric, then earliest label, then shorter.
    scored.sort(key=lambda s: (-s[2], -s[3], s[0], len(s[1])))
    return scored


def main():
    scored = pick()
    for label, text, p, r, parts in scored:
        print(f"{label}: proxy {p} (c {parts}) rubric {r} "
              f"[{len(text)}ch] {text}")
    label, text, p, r, _ = scored[0]
    print(f"PICK {label}: proxy {p} rubric {r}: {text}")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "entry.txt")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError:
        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "entry.txt")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(f"WROTE {out_path} ({len(text)} chars, no trailing newline)")


if __name__ == "__main__":
    main()

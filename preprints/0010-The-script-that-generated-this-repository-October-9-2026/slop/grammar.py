import re
from pathlib import Path

# nonterminals always start with a capital letter
NONTERMINAL_PATTERN = re.compile(r"<([A-Z][A-Za-z]*)>")

# markers filled from context after expansion
MARKER_PATTERN = re.compile(r"@@([A-Za-z]+)@@")
MARKERS = {"Cite", "EqRef", "FigRef", "SecRef", "ResultRef"}

# tex prefix, markdown fallback and context key for each reference marker
REFERENCE_FORMS = {"EqRef": ("Eq.~\\eqref{", "Eq. (1)", "equation_labels"), "FigRef": ("Fig.~\\ref{", "Fig. 1", "figure_labels"), "SecRef": ("Section~\\ref{", "Section 2", "section_labels")}

# depth past which only the plainest production is used
MAXIMUM_DEPTH = 6

# share of titles that are backronyms
ACRONYM_RATE = 0.3

# words left lowercase inside titles
SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to", "via", "with", "vs"}

# article followed by the next word
ARTICLE_PATTERN = re.compile(r"\b([Aa]n?) (\S+)")


# whether the next word takes an
def needs_an(word):

    core = word.lstrip("\"'(")
    if not core or core[0] in "$\\":
        return False

    # acronyms read letter by letter
    if core[0].isupper() and (len(core) == 1 or core[1].isupper() or core[1].isdigit() or core[1] == "-"):
        return core[0] in "AEFHILMNORSX"

    # vowel letters with consonant sounds
    lower = core.lower()
    if lower.startswith(("one", "uni", "use", "eu")):
        return False
    return lower[0] in "aeiou"


# article agreement with case kept
def fix_article(match):

    replacement = "an" if needs_an(match.group(2)) else "a"
    if match.group(1)[0].isupper():
        replacement = replacement.capitalize()
    return replacement + " " + match.group(2)


# spacing and articles without capitals
def polish_fragment(text):

    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r" ([,.:;?])", r"\1", text)

    # a word drawn twice in a row is kept once
    text = re.sub(r"\b([\w-]+) \1\b", r"\1", text)
    return ARTICLE_PATTERN.sub(fix_article, text)


# full cleanup with sentence capitals
def polish(text):

    text = polish_fragment(text)
    return re.sub(r"(^|[.?!] )([a-z])", lambda match: match.group(1) + match.group(2).upper(), text)


# headline capitals that leave acronyms and symbols alone
def title_case(text):

    cased_words = []
    force_capital = True
    for word in text.split(" "):

        # hyphen and slash parts are cased separately
        parts = re.split(r"([-/])", word)
        cased_parts = []
        for index, part in enumerate(parts):
            is_lower_word = part.replace("'", "").rstrip(",:;?!").isalpha() and part.islower()
            keep_small = part in SMALL_WORDS and not (force_capital and index == 0)
            cased_parts.append(part[0].upper() + part[1:] if is_lower_word and not keep_small else part)

        # the word after a colon is capitalized
        cased_words.append("".join(cased_parts))
        force_capital = word.endswith(":")

    return " ".join(cased_words)


# capital first letter only
def sentence_case(text):

    return text[:1].upper() + text[1:]


# GitHub inline math and plain spaces for ties
def to_markdown(text):

    text = re.sub(r"\$([^$]+)\$", r"$`\1`$", text)
    return text.replace("~", " ")


class Grammar:

    def __init__(self, directory):

        # one production per line across every grammar file
        self.productions = {}
        for path in sorted(Path(directory).glob("*.txt")):
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                name, right_side = stripped.split(" -> ", 1)
                self.productions.setdefault(name.strip("<>"), []).append(right_side)

        # plainest production of each nonterminal for the depth cutoff
        self.plainest = {}
        for name, options in self.productions.items():
            self.plainest[name] = min(options, key=lambda option: len(NONTERMINAL_PATTERN.findall(option)))

    # production weights are the model parameters
    def parameter_count(self):

        return sum(len(options) for options in self.productions.values())

    def expand(self, symbol, rng, depth=0):

        # markers survive expansion
        if symbol in MARKERS:
            return "@@" + symbol + "@@"

        # random production until the depth cutoff
        if depth > MAXIMUM_DEPTH:
            production = self.plainest[symbol]
        else:
            production = rng.choice(self.productions[symbol])

        # recursive substitution left to right
        return NONTERMINAL_PATTERN.sub(lambda match: self.expand(match.group(1), rng, depth + 1), production)

    def reference(self, marker, rng, context):

        # markdown never carries live references
        is_tex = context.get("mode", "tex") == "tex"
        if marker == "Cite":
            keys = context.get("cite_keys") or []
            return "~\\cite{" + rng.choice(keys) + "}" if is_tex and keys else ""

        # result numbers from the family list
        if marker == "ResultRef":
            numbers = context.get("family_numbers") or [1]
            return "result " + str(rng.choice(numbers)).zfill(3)

        # equation, figure and section references
        prefix, fallback, key = REFERENCE_FORMS[marker]
        labels = context.get(key) or []
        if is_tex and labels:
            return prefix + rng.choice(labels) + "}"
        return fallback

    # every marker in the text replaced
    def fill(self, text, rng, context):

        return MARKER_PATTERN.sub(lambda match: self.reference(match.group(1), rng, context), text)

    # expanded, filled and polished sentence
    def sentence(self, symbol, rng, context):

        return polish(self.fill(self.expand(symbol, rng), rng, context))

    # expanded fragment without sentence capitals
    def phrase(self, symbol, rng):

        return polish_fragment(self.expand(symbol, rng))

    def title(self, rng):

        # backronym titles at a fixed rate
        if rng.random() < ACRONYM_RATE:
            return self.acronym_title(rng)
        return title_case(polish_fragment(self.expand("Title", rng)))

    def acronym_title(self, rng):

        # adjectives for every letter but the last, then a noun
        acronym = self.expand("Acronym", rng)
        letters = [letter for letter in acronym.upper() if letter.isalpha()]
        words = []
        for attempt in range(200):
            words = [self.expand("AcronymAdjective" + letter, rng) for letter in letters[:-1]]
            words.append(self.expand("AcronymNoun" + letters[-1], rng))
            stems = [stem for word in words for stem in word.lower().replace(" ", "-").split("-")]
            if len(set(stems)) == len(stems):
                break

        return acronym + ": " + title_case(" ".join(words))

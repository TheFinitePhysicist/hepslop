import re
import textwrap

from .grammar import polish_fragment, sentence_case

# lines across all tex files of one manuscript
MINIMUM_LINES = 250
MAXIMUM_LINES = 300

# figure kinds drawn by slop/pdfs.py
FIGURE_KINDS = ["curve", "histogram", "filled", "stack", "band", "scan", "taggers", "heatmap", "ratio", "bars", "panels", "scatter", "contour", "boxes"]

# words left out of section file names
SLUG_STOP_WORDS = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to", "via", "with"}

# packages that do not exist anywhere
FAKE_PACKAGES = ["qcdsymbols", "jetphys", "pertqcd", "loopintegrals", "colliderfonts", "feynhep", "sudakovmacros", "hepjetmacros"]

# section files that are never written
MISSING_SECTIONS = ["05-appendix", "discussion", "appendix-two-loop", "supplementary", "06-outlook", "appendix-proofs"]

# macros nobody defined
UNDEFINED_MACROS = [r"\SudakovButMore", r"\CFbar", r"\asbar", r"\Pqqreg", r"\NNLLprime", r"\softfunc"]

# macros the equation grammar relies on
MACRO_LINES = [r"\newcommand{\as}{\alpha_s}", r"\newcommand{\CF}{C_F}", r"\newcommand{\CA}{C_A}", r"\newcommand{\TF}{T_F}", r"\newcommand{\Nf}{n_f}", r"\newcommand{\Pqq}{P_{qq}}", r"\newcommand{\Pgq}{P_{gq}}", r"\newcommand{\Pgg}{P_{gg}}", r"\newcommand{\muR}{\mu_R}", r"\newcommand{\muF}{\mu_F}", r"\newcommand{\dPhi}{d\Phi}", r"\newcommand{\sij}{s_{ij}}", r"\newcommand{\kT}{k_T}", r"\newcommand{\Li}{\mathrm{Li}}", r"\newcommand{\softmax}{\mathrm{softmax}}", r"\newcommand{\EMD}{\mathrm{EMD}}", r"\newcommand{\LQCD}{\Lambda_{\rm QCD}}", r"\newcommand{\zcut}{z_{\rm cut}}", r"\newcommand{\Neff}{N_{\rm eff}}"]

# theorem environments in the house style
THEOREM_LINES = [r"\setlength{\emergencystretch}{2em}", r"\numberwithin{equation}{section}", r"\newtheorem{theorem}{Theorem}[section]", r"\newtheorem{lemma}[theorem]{Lemma}", r"\newtheorem{proposition}[theorem]{Proposition}", r"\newtheorem{corollary}[theorem]{Corollary}", r"\theoremstyle{definition}", r"\newtheorem{definition}[theorem]{Definition}", r"\theoremstyle{remark}", r"\newtheorem{remark}[theorem]{Remark}"]

# packages in the house style
PACKAGE_LINES = [r"\def\DoNotLoadEpstopdf{}", r"\usepackage[T1]{fontenc}", r"\usepackage{lmodern}", r"\usepackage[margin=1in]{geometry}", r"\usepackage{amsmath,amssymb,amsthm,mathtools}", r"\usepackage{enumitem,microtype,xcolor,tikz}", r"\usepackage{graphicx}", r"\usepackage[nottoc]{tocbibind}", r"\usepackage[colorlinks=true,linkcolor=blue!45!black,citecolor=blue!45!black,urlcolor=blue!45!black]{hyperref}"]

# sentence pools for each part of the paper
INTRODUCTION_SYMBOLS = ["ContextSentence", "MotivationSentence", "GapSentence", "ClaimSentence", "MethodSentence"]
BODY_SYMBOLS = ["BodySentence"]
CLOSING_SYMBOLS = ["ClosingSentence", "ResultSentence", "FutureSentence", "LimitationSentence"]


# delimiter and operator glyphs for the unicode map
def glyph_table():

    # delimiters in four sizes
    table = []
    for size in ["big", "Big", "bigg", "Bigg"]:
        for stem, code in [("parenleft", "0028"), ("parenright", "0029"), ("bracketleft", "005B"), ("bracketright", "005D"), ("braceleft", "007B"), ("braceright", "007D"), ("radical", "221A")]:
            table.append((stem + size, code))

    # large operators in text and display sizes
    for stem, code in [("summation", "2211"), ("integral", "222B"), ("product", "220F"), ("contintegral", "222E"), ("union", "22C3"), ("intersection", "22C2"), ("circleplus", "2A01"), ("circlemultiply", "2A02"), ("coproduct", "2210")]:
        table.append((stem + "text", code))
        table.append((stem + "display", code))

    return table


# prose wrapped like a hand-written source file
def wrap(text):

    return textwrap.wrap(text, width=72, break_on_hyphens=False, break_long_words=False)


# lines joined into file text
def to_text(lines):

    return "\n".join(lines) + "\n"


# characters that break a title in tex
def latex_safe(text):

    for character in "&%#_":
        text = text.replace(character, "\\" + character)
    return text


# short lowercase slug from the first words
def slugify(text, word_count):

    words = [word for word in re.sub(r"[^a-z0-9 ]", "", text.lower()).split() if word not in SLUG_STOP_WORDS]
    return "-".join(words[:word_count]) or "section"


# expanded fragment with markers filled and a capital first letter
def clean(grammar, symbol, rng, context):

    return sentence_case(polish_fragment(grammar.fill(grammar.expand(symbol, rng), rng, context)))


# packages, glyph map, theorems and macros
def preamble_lines(rng, title):

    lines = list(PACKAGE_LINES)
    lines.append(r"\hypersetup{pdftitle={" + title + r"},pdfauthor={The Physics Community}}")
    lines.extend([r"\pdfinfoomitdate=1", r"\pdftrailerid{}", r"\pdfsuppressptexinfo=15", "", r"\pdfgentounicode=1"])

    # a random-length slice of the glyph map
    glyphs = glyph_table()
    for name, code in glyphs[:rng.randint(20, len(glyphs))]:
        lines.append(r"\pdfglyphtounicode{tfm:lmex10/" + name + "}{" + code + "}")

    # theorem environments and macros
    lines.extend(THEOREM_LINES)
    lines.extend(MACRO_LINES)
    return lines


# title block, abstract, section inputs and bibliography
def document_lines(manuscript, inputs, bib_stem):

    lines = ["", r"\title{" + latex_safe(manuscript["title"]) + "}", r"\author{The Physics Community}", r"\date{" + manuscript["date_text"] + "}", r"\begin{document}", r"\maketitle", r"\begin{abstract}"]
    lines.extend(wrap(manuscript["abstract"]))
    lines.extend([r"\end{abstract}", r"\tableofcontents"])
    lines.extend([r"\input{" + name + "}" for name in inputs])
    lines.extend([r"\nocite{*}", r"\bibliographystyle{plain}", r"\bibliography{" + bib_stem + "}", r"\end{document}"])
    return lines


# self-citations to other manuscripts in the collection
def bib_text(cite_entries):

    lines = []
    for entry in cite_entries:
        lines.append("@misc{" + entry["key"] + ",")
        lines.append("  author = {{The Physics Community}},")
        lines.append("  title = {{" + latex_safe(entry["title"]) + "}},")
        lines.append("  howpublished = {hepslop preprint},")
        lines.append("  year = {2026}")
        lines.append("}")
        lines.append("")

    return to_text(lines)


# several sentences as one wrapped paragraph
def paragraph_block(grammar, rng, symbols, count, context):

    sentences = []
    for index in range(count):

        # redraw sentences that repeat or open like an earlier one
        sentence = grammar.sentence(rng.choice(symbols), rng, context)
        for attempt in range(5):
            openings = [" ".join(earlier.split()[:4]) for earlier in sentences]
            if " ".join(sentence.split()[:4]) not in openings:
                break
            sentence = grammar.sentence(rng.choice(symbols), rng, context)
        sentences.append(sentence)

    return wrap(" ".join(sentences))


# single displayed equation
def equation_block(grammar, rng, label):

    return [r"\begin{equation}", "  " + grammar.expand("Equation", rng), r"  \label{" + label + "}", r"\end{equation}"]


# two-line aligned equation
def align_block(grammar, rng, label):

    first = "  " + grammar.expand("EquationLeft", rng) + " &= " + grammar.expand("EquationTerm", rng) + r" \nonumber \\"
    second = r"  &\quad + " + grammar.expand("EquationTerm", rng) + r" + \mathcal{O}(\as^3) \label{" + label + "}"
    return [r"\begin{align}", first, second, r"\end{align}"]


# theorem-like statement with a short proof
def theorem_block(grammar, rng, context, label):

    environment = rng.choice(["theorem", "proposition", "lemma", "corollary"])
    name = clean(grammar, "TheoremName", rng, context)
    lines = [r"\begin{" + environment + "}[" + name + r"]\label{" + label + "}"]
    lines.extend(wrap(grammar.sentence("TheoremStatement", rng, context)))
    lines.extend([r"\end{" + environment + "}", "", r"\begin{proof}"])
    lines.extend(paragraph_block(grammar, rng, ["ProofSentence"], rng.randint(2, 3), context))
    lines.append(r"\end{proof}")
    return lines


# bullet list of three claims
def itemize_block(grammar, rng, context):

    lines = [r"\begin{itemize}"]
    for index in range(3):
        lines.append(r"  \item " + grammar.sentence("ItemSentence", rng, context))
    lines.append(r"\end{itemize}")
    return lines


# figure environment and the spec its pdf is drawn from
def figure_block(grammar, rng, name, context):

    caption = grammar.sentence("Caption", rng, context)
    width = rng.choice(["0.5", "0.6", "0.7", "0.8", "0.9"])
    lines = [r"\begin{figure}[t]", r"\centering", r"\includegraphics[width=" + width + r"\textwidth]{figures/" + name + ".pdf}", r"\caption{" + caption + "}", r"\label{fig:" + name + "}", r"\end{figure}"]

    # three different method names for figures with several series
    legends = []
    while len(legends) < 3:
        legend = grammar.expand("FigureLegend", rng)
        if legend not in legends:
            legends.append(legend)

    # everything the drawing needs, with its own seed
    spec = {"name": name, "kind": rng.choice(FIGURE_KINDS), "x_label": grammar.expand("FigureXLabel", rng), "y_label": grammar.expand("FigureYLabel", rng), "legend": legends[0], "legends": legends, "stamp_title": grammar.expand("FigureStampTitle", rng), "stamp_detail": grammar.expand("FigureStampDetail", rng), "shape": rng.choice(["sudakov", "peak", "roc", "wiggle"]), "parameters": [rng.uniform(0.5, 3.0), rng.uniform(0.5, 3.0)], "seed": rng.randint(0, 2147483647)}
    return lines, spec


# one random body block with its labels recorded
def random_block(grammar, rng, context):

    kind = rng.choices(["paragraph", "equation", "align", "theorem", "itemize"], weights=[45, 18, 10, 12, 8])[0]

    # displayed math gets the next equation label
    if kind in ("equation", "align"):
        label = "eq:" + str(len(context["equation_labels"]) + 1)
        block = equation_block(grammar, rng, label) if kind == "equation" else align_block(grammar, rng, label)
        context["equation_labels"].append(label)
        return block

    # theorems get their own counter
    if kind == "theorem":
        context["theorem_count"] = context.get("theorem_count", 0) + 1
        return theorem_block(grammar, rng, context, "thm:" + str(context["theorem_count"]))

    if kind == "itemize":
        return itemize_block(grammar, rng, context)

    # paragraphs may point back at equations and figures
    symbols = BODY_SYMBOLS * 6
    if context["equation_labels"]:
        symbols.append("EquationSentence")
    if context["figure_labels"]:
        symbols.append("FigureSentence")
    return paragraph_block(grammar, rng, symbols, rng.randint(3, 6), context)


# one section as header lines plus its blocks
def section_text(section):

    lines = [r"\section{" + section["title"] + r"}\label{" + section["label"] + "}", ""]
    for block in section["blocks"]:
        lines.extend(block)
        lines.append("")

    return to_text(lines)


# total tex lines over header files and sections
def total_lines(files, sections):

    header_count = sum(len(text.splitlines()) for path, text in files.items() if path.endswith(".tex"))
    return header_count + sum(len(section_text(section).splitlines()) for section in sections)


# drop the last block that is not a figure
def drop_plain_block(section):

    for index in range(len(section["blocks"]) - 1, 0, -1):
        if not section["blocks"][index][0].startswith(r"\begin{figure}"):
            section["blocks"].pop(index)
            return True

    return False


def build_manuscript(grammar, rng, manuscript, cite_entries):

    # layout choices
    uses_paper_layout = rng.random() < 0.35
    main_name = "paper.tex" if uses_paper_layout else "main.tex"
    bib_stem = "refs" if rng.random() < 0.05 else "references"
    is_numbered = rng.random() < 0.5
    section_count = rng.randint(3, 5)

    # section titles, labels and file names
    titles = ["Introduction"]
    while len(titles) < section_count - 1:
        title = clean(grammar, "SectionTitle", rng, {})
        if title not in titles:
            titles.append(title)
    titles.append("Conclusions")
    sections = []
    used_slugs = set()
    for index, title in enumerate(titles):
        slug = slugify(title, 3)
        while slug in used_slugs:
            slug = slug + "-" + str(index)
        used_slugs.add(slug)
        stem = str(index).zfill(2) + "-" + slug if is_numbered else slug
        sections.append({"title": title, "label": "sec:" + slug, "input": "sections/" + stem, "blocks": []})

    # header files in one of two layouts
    preamble = preamble_lines(rng, latex_safe(manuscript["title"]))
    document = document_lines(manuscript, [section["input"] for section in sections], bib_stem)
    files = {}
    if uses_paper_layout:
        files["preamble.tex"] = to_text(preamble)
        files["paper.tex"] = to_text([r"\documentclass[11pt]{article}", r"\input{preamble}"] + document)
    else:
        files["main.tex"] = to_text([r"\documentclass[11pt]{article}"] + preamble + document)

    # bibliography and the shared reference context
    files[bib_stem + ".bib"] = bib_text(cite_entries)
    context = {"mode": "tex", "cite_keys": [entry["key"] for entry in cite_entries], "equation_labels": [], "figure_labels": [], "section_labels": []}

    # introduction ending in an outline of the later sections
    introduction = sections[0]
    for index in range(rng.randint(2, 3)):
        introduction["blocks"].append(paragraph_block(grammar, rng, INTRODUCTION_SYMBOLS, rng.randint(3, 5), context))
    outline = [grammar.sentence("OutlineSentence", rng, dict(context, section_labels=[section["label"]])) for section in sections[1:]]
    introduction["blocks"].append(wrap(" ".join(outline)))

    # conclusions
    sections[-1]["blocks"].append(paragraph_block(grammar, rng, CLOSING_SYMBOLS, rng.randint(3, 5), context))

    # every middle section opens with a paragraph
    middle = sections[1:-1]
    for section in middle:
        section["blocks"].append(paragraph_block(grammar, rng, BODY_SYMBOLS, rng.randint(3, 5), context))

    # two or three figures spread over the middle sections
    figures = []
    for index in range(rng.randint(2, 3)):
        name = grammar.expand("FigureName", rng)
        if any(spec["name"] == name for spec in figures):
            name = name + "-" + str(index + 1)
        lines, spec = figure_block(grammar, rng, name, context)
        rng.choice(middle)["blocks"].append(lines)
        figures.append(spec)
        context["figure_labels"].append("fig:" + name)

    # blocks added round robin up to the line target
    target = rng.randint(255, 292)
    position = 0
    while total_lines(files, sections) < target:
        middle[position % len(middle)]["blocks"].append(random_block(grammar, rng, context))
        position += 1

    # trim or pad into the window that leaves room for breakage
    while total_lines(files, sections) > MAXIMUM_LINES - 5:
        if not drop_plain_block(max(middle, key=lambda section: len(section["blocks"]))):
            break
    while total_lines(files, sections) < MINIMUM_LINES + 5:
        middle[-1]["blocks"].append(paragraph_block(grammar, rng, BODY_SYMBOLS, 2, context))

    # section files
    for section in sections:
        files[section["input"] + ".tex"] = section_text(section)

    # final line count inside the window
    line_count = sum(len(text.splitlines()) for path, text in files.items() if path.endswith(".tex"))
    assert MINIMUM_LINES <= line_count <= MAXIMUM_LINES, line_count
    return {"files": files, "main_name": main_name, "figures": figures, "line_count": line_count}


# insert a line after the last line that starts with a prefix
def insert_after_last(lines, prefix, new_line):

    positions = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    lines.insert(positions[-1] + 1 if positions else 1, new_line)


# section files of a built manuscript
def section_paths(built):

    return [path for path in built["files"] if path.startswith("sections/")]


# one cosmetic error in a random section file
def soft_error(rng, built, kind):

    path = rng.choice(section_paths(built))
    lines = built["files"][path].split("\n")

    # a display environment that never closes
    if kind == "unclosed_display":
        candidates = [index for index, line in enumerate(lines) if line in (r"\end{align}", r"\end{equation}")]
        if candidates:
            lines.pop(rng.choice(candidates))

    # a starred end for an unstarred begin
    if kind == "starred_end":
        candidates = [index for index, line in enumerate(lines) if line == r"\end{equation}"]
        if candidates:
            lines[rng.choice(candidates)] = r"\end{equation*}"

    # a macro nobody defined inside displayed math
    if kind == "undefined_macro":
        candidates = [index for index, line in enumerate(lines) if line.startswith("  ") and "\\" in line and not line.startswith(r"  \label")]
        if candidates:
            index = rng.choice(candidates)
            lines[index] = lines[index] + " " + rng.choice(UNDEFINED_MACROS)

    # an alignment tab in running text
    if kind == "stray_ampersand":
        candidates = [index for index, line in enumerate(lines) if line and line[0].isalpha() and " " in line]
        if candidates:
            index = rng.choice(candidates)
            middle = lines[index].index(" ", len(lines[index]) // 2) if " " in lines[index][len(lines[index]) // 2:] else lines[index].index(" ")
            lines[index] = lines[index][:middle] + " &" + lines[index][middle:]

    # a caption whose brace never closes
    if kind == "unclosed_caption":
        candidates = [index for index, line in enumerate(lines) if line.startswith(r"\caption{")]
        if candidates:
            index = rng.choice(candidates)
            lines[index] = lines[index][:-1]

    built["files"][path] = "\n".join(lines)


def break_manuscript(rng, built):

    # one failure that stops pdflatex before any page is written
    failure = rng.choice(["missing_input", "missing_package", "missing_end"])
    main_name = built["main_name"]
    main_lines = built["files"][main_name].split("\n")
    if failure == "missing_input":
        insert_after_last(main_lines, r"\input{sections/", r"\input{sections/" + rng.choice(MISSING_SECTIONS) + "}")
    if failure == "missing_end":
        main_lines.remove(r"\end{document}")
    built["files"][main_name] = "\n".join(main_lines)

    # the fake package goes wherever the packages live
    if failure == "missing_package":
        target = "preamble.tex" if "preamble.tex" in built["files"] else main_name
        target_lines = built["files"][target].split("\n")
        insert_after_last(target_lines, r"\usepackage", r"\usepackage{" + rng.choice(FAKE_PACKAGES) + "}")
        built["files"][target] = "\n".join(target_lines)

    # zero to three cosmetic errors on top
    soft_errors = rng.sample(["unclosed_display", "starred_end", "undefined_macro", "stray_ampersand", "unclosed_caption"], rng.randint(0, 3))
    for kind in soft_errors:
        soft_error(rng, built, kind)

    # recount and record what was broken
    built["line_count"] = sum(len(text.splitlines()) for path, text in built["files"].items() if path.endswith(".tex"))
    assert MINIMUM_LINES <= built["line_count"] <= MAXIMUM_LINES, built["line_count"]
    built["failure"] = failure
    built["soft_errors"] = soft_errors
    return built

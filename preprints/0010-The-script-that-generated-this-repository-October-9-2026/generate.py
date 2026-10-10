import math
import random
import re
import shutil
import sys
import time
from multiprocessing import Pool
from pathlib import Path

# repository layout relative to this script
SCRIPT_DIRECTORY = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIRECTORY.parent.parent
PREPRINTS_DIRECTORY = REPOSITORY_ROOT / "preprints"
sys.path.insert(0, str(SCRIPT_DIRECTORY))

from slop.grammar import Grammar, to_markdown
from slop.indexes import NUMBER_WIDTH, contents_files, history_markdown, lean_files, manuscript_readme, overview_tex, readme_markdown, trace_tex, withdrawn_readme
from slop.pdfs import build_working, corrupted_pdf
from slop.tex import break_manuscript, build_manuscript

# collection size and bookkeeping
SEED = 20261009
MANUSCRIPT_COUNT = 2500
WITHDRAWN_COUNT = 3
REVISED_COUNT = 14
UPDATED_COUNT = 13
TRACE_COUNT = 10
WORKER_COUNT = 16

# working papers thin out with position in the collection
VALID_DECAY = 250.0
FORCED_VALID = 15

# this script is the tenth entry
SCRIPT_NUMBER = 10

# corrupted pdf sizes in bytes
MANUSCRIPT_BYTES = (20000, 100000)
FIGURE_BYTES = (3000, 20000)
WITHDRAWN_BYTES = (3000, 5000)

# manuscripts per page of the manuscript map
CONTENTS_PAGE_SIZE = 500

# fixed titles by entry number
FIXED_TITLES = {1: "A Complete Solution of Quantum Chromodynamics to All Orders", 2: "SLOP: Self-supervised Learning Of Perturbation theory", 3: "One Thousand Results in Perturbative QCD", 4: "Next-to-Next-to-Leading Order Corrections to Nothing", 6: "HYPE: Hierarchical Yukawa-Perturbative Embeddings", 8: "VIBES: Variational Infrared-Bounded Energy Spectra", 11: "AGI: Anomalous Gluon Interactions at Next-to-Leading Logarithm", 12: "CLOUT: Collinear Logarithms Over Unresolved Transformers", 14: "FOMO: Fixed-Order Matching Operators", 15: "We Achieve State-of-the-Art Results on a Benchmark We Made Up"}

# release dates, September three times as likely as October
DATES = [("September", day, 9) for day in range(18, 31)] + [("October", day, 10) for day in range(1, 10)]
DATE_WEIGHTS = [3 if month == "September" else 1 for month, day, month_number in DATES]

# pdf names in the proportions of the original
PDF_CHOICES = ["paper.pdf", "slug", "main.pdf", "manuscript.pdf", "article.pdf"]
PDF_WEIGHTS = [59, 23, 13, 3, 2]

# words dropped from short pdf slugs
SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to", "via", "with", "is", "are", "all", "you", "need"}


# file written with parents created
def write_file(path, content):

    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")


# previous output removed, this script's directory and the readme kept
def clean_repository():

    for name in ["CONTENTS.md", "history.md", "LICENSE", "overview.tex", "overview.pdf"]:
        (REPOSITORY_ROOT / name).unlink(missing_ok=True)
    for name in ["lean", "reasoning_traces", "contents"]:
        shutil.rmtree(REPOSITORY_ROOT / name, ignore_errors=True)

    # every manuscript directory but this one
    for path in PREPRINTS_DIRECTORY.iterdir():
        if path.is_dir() and path != SCRIPT_DIRECTORY:
            shutil.rmtree(path)


# directory slug in the style of the original release
def title_slug(title):

    stripped = title.replace("'", "").replace("’", "")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", stripped).strip("-")

    # long backronyms cut at a word boundary to stay under file-name limits
    while len(slug) > 150 and "-" in slug:
        slug = slug.rsplit("-", 1)[0]
    return slug


# short lowercase pdf name from the content words of a title
def pdf_slug(title):

    words = [word for word in re.sub(r"[^a-z0-9 ]", " ", title.lower()).split() if word not in SMALL_WORDS]
    return "-".join(words[:4]) + ".pdf"


# a title nobody has used yet
def unique_title(grammar, rng, seen):

    title = grammar.title(rng)
    while title in seen:
        title = grammar.title(rng)
    seen.add(title)
    return title


# lowercase first letter for use mid-sentence, acronyms left alone
def lowercase_first(text):

    if text[:2].isupper():
        return text
    return text[:1].lower() + text[1:]


# one manuscript record with its text
def new_manuscript(grammar, rng, position, title, is_valid):

    abstract = grammar.sentence("Abstract", rng, {"mode": "tex"})

    # date and pdf name
    date_index = rng.choices(range(len(DATES)), weights=DATE_WEIGHTS)[0]
    pdf_choice = rng.choices(PDF_CHOICES, weights=PDF_WEIGHTS)[0]
    pdf_name = pdf_slug(title) if pdf_choice == "slug" else pdf_choice
    return {"position": position, "title": title, "valid": is_valid, "abstract": abstract, "abstract_markdown": to_markdown(abstract), "date_index": date_index, "pdf_name": pdf_name, "previous": None, "fix": None, "withdrawn": False, "superseded": False, "lowercase": rng.random() < 0.01, "iso_date": False}


# every paper in order, fixed titles first
def build_papers(grammar, rng):

    papers = []
    seen_titles = set(FIXED_TITLES.values())
    for position in range(1, MANUSCRIPT_COUNT + WITHDRAWN_COUNT + 1):

        # entry number before superseded editions are slotted in
        number = position if position < SCRIPT_NUMBER else position + 1
        title = FIXED_TITLES[number] if number in FIXED_TITLES else unique_title(grammar, rng, seen_titles)
        is_valid = number <= FORCED_VALID or rng.random() < math.exp(-position / VALID_DECAY)
        papers.append(new_manuscript(grammar, rng, position, title, is_valid))

    return papers


# withdrawals and superseded editions
def mark_revisions(grammar, rng, papers):

    # withdrawn papers come from after the fixed titles
    candidates = [paper for paper in papers if paper["position"] > FORCED_VALID]
    withdrawn = rng.sample(candidates, WITHDRAWN_COUNT)
    for paper in withdrawn:
        paper["withdrawn"] = True
        paper["pdf_name"] = "manuscript.pdf"

    # revised papers keep a copy of their earlier edition
    revisable = [paper for paper in candidates if not paper["withdrawn"] and paper["date_index"] > 0]
    revised = rng.sample(revisable, REVISED_COUNT)
    for paper in revised:
        previous = dict(paper)
        previous["date_index"] = max(0, paper["date_index"] - rng.randint(1, 4))
        previous["abstract"] = grammar.sentence("Abstract", rng, {"mode": "tex"})
        previous["superseded"] = True
        paper["previous"] = previous
        paper["fix"] = grammar.phrase("FixPhrase", rng)

    # one numeric date suffix somewhere in the collection
    rng.choice(revisable)["iso_date"] = True
    return withdrawn, revised


# one number per folder, superseded editions just before their revisions
def number_entries(papers):

    entries = []
    for paper in papers:
        if len(entries) == SCRIPT_NUMBER - 1:
            entries.append({"script_directory": SCRIPT_DIRECTORY.name})
        if paper["previous"] is not None:
            entries.append(paper["previous"])
        entries.append(paper)

    for index, entry in enumerate(entries):
        entry["number"] = index + 1
    return entries


# date text and directory name from the date index and number
def assign_directory(manuscript, seen_directories):

    month, day, month_number = DATES[manuscript["date_index"]]
    manuscript["date_text"] = month + " " + str(day) + ", 2026"
    slug = title_slug(manuscript["title"])
    if manuscript["lowercase"]:
        slug = slug.lower()

    # number up front, and exactly one numeric date suffix in the collection
    number = str(manuscript["number"]).zfill(NUMBER_WIDTH)
    if manuscript["iso_date"]:
        directory = number + "-" + slug + "-2026-" + str(month_number).zfill(2) + "-" + str(day).zfill(2)
    else:
        directory = number + "-" + slug + "-" + month + "-" + str(day) + "-2026"

    # never two manuscripts in one directory
    while directory in seen_directories:
        directory = directory + "-2"
    seen_directories.add(directory)
    manuscript["directory"] = directory


# corrupted pdfs for a broken manuscript and its figures
def write_corrupted(rng, manuscript_directory, built, pdf_name):

    write_file(manuscript_directory / pdf_name, corrupted_pdf(rng, *MANUSCRIPT_BYTES))
    for spec in built["figures"]:
        write_file(manuscript_directory / "build" / "figures" / (spec["name"] + ".pdf"), corrupted_pdf(rng, *FIGURE_BYTES))


# tex tree, readme and pdfs for one manuscript, returning a compile job if it works
def write_manuscript(grammar, manuscript, published):

    rng = random.Random(str(SEED) + manuscript["directory"])
    manuscript_directory = PREPRINTS_DIRECTORY / manuscript["directory"]

    # withdrawn papers keep only a notice and a stub
    if manuscript["withdrawn"]:
        revision = "%040x" % rng.getrandbits(160)
        write_file(manuscript_directory / "README.md", withdrawn_readme(manuscript, grammar.phrase("WithdrawalReason", rng), "October 7, 2026", revision))
        write_file(manuscript_directory / "manuscript.pdf", corrupted_pdf(rng, *WITHDRAWN_BYTES))
        return None

    # citations to other papers in the collection
    others = [other for other in published if other["directory"] != manuscript["directory"]]
    cite_entries = [{"key": "TPC:" + other["directory"], "title": other["title"]} for other in rng.sample(others, rng.randint(4, 9))]
    built = build_manuscript(grammar, rng, manuscript, cite_entries)
    if not manuscript["valid"]:
        break_manuscript(rng, built)

    # sources and readme
    for relative, text in built["files"].items():
        write_file(manuscript_directory / "build" / relative, text)
    write_file(manuscript_directory / "README.md", manuscript_readme(manuscript))

    # broken papers get corrupted pdfs, working ones a compile job
    if not manuscript["valid"]:
        write_corrupted(rng, manuscript_directory, built, manuscript["pdf_name"])
        return None
    return {"build_directory": str(manuscript_directory / "build"), "main_name": built["main_name"], "output_pdf": str(manuscript_directory / manuscript["pdf_name"]), "figures": built["figures"]}


# trace table rows and the exceptions sentence in a hand-edited readme
def refresh_readme(path, traces, exceptions):

    lines = path.read_text(encoding="utf-8").split("\n")
    rows = ["| " + str(number).zfill(NUMBER_WIDTH) + " | [" + subject + "](reasoning_traces/" + file_name + ") |" for number, subject, file_name in traces]
    sentence = "Exceptions to this fixed procedure include work on " + exceptions[0] + " and " + exceptions[1] + ". Additionally, the writeup for " + exceptions[0] + " was human edited for readability. "

    # the table sits under its header and separator
    header = next((index for index, line in enumerate(lines) if line.startswith("| Family |") or line.startswith("| Manuscript |")), None)
    if header is not None:
        end = header + 2
        while end < len(lines) and lines[end].startswith("| "):
            end += 1
        lines[header:end] = ["| Manuscript | Subject |", "|---|---|"] + rows

    # the exceptions sentence names two traced manuscripts
    lines = [sentence if line.startswith("Exceptions to this fixed procedure") else line for line in lines]
    path.write_text("\n".join(lines), encoding="utf-8")


# top-level files, overview, lean stub and reasoning traces
def write_indexes(grammar, rng, entries, published, withdrawn, revised):

    listed = [entry for entry in entries if entry.get("script_directory") is not None or not (entry["withdrawn"] or entry["superseded"])]
    for relative, text in contents_files(listed, len(published), CONTENTS_PAGE_SIZE).items():
        write_file(REPOSITORY_ROOT / relative, text)

    # reasoning traces for a handful of manuscripts
    traced = sorted(rng.sample(published, TRACE_COUNT), key=lambda manuscript: manuscript["number"])
    traces = []
    for manuscript in traced:
        file_name = title_slug(manuscript["title"]).lower()[:60].strip("-") + ".pdf"
        traces.append((manuscript["number"], manuscript["title"], file_name))
        write_file(REPOSITORY_ROOT / "reasoning_traces" / file_name, corrupted_pdf(rng, 100000, 300000))

    # one trace source that never compiles
    paragraphs = [" ".join(grammar.sentence("BodySentence", rng, {"mode": "tex"}) for index in range(rng.randint(3, 6))) for index in range(30)]
    write_file(REPOSITORY_ROOT / "reasoning_traces" / traces[0][2].replace(".pdf", ".tex"), trace_tex(traces[0][1], paragraphs))

    # a hand-edited readme is kept and refreshed, a fresh build gets a generated one
    exceptions = [lowercase_first(manuscript["title"]) for manuscript in rng.sample(traced, 2)]
    readme_path = REPOSITORY_ROOT / "README.md"
    if readme_path.exists():
        refresh_readme(readme_path, traces, exceptions)
    else:
        write_file(readme_path, readme_markdown(len(published), traces, exceptions, SCRIPT_DIRECTORY.name, grammar.parameter_count()))

    # history of withdrawals and fixes
    fixes = [(manuscript["title"], manuscript["fix"]) for manuscript in revised]
    reason = grammar.phrase("WithdrawalReason", rng)
    write_file(REPOSITORY_ROOT / "history.md", history_markdown([manuscript["title"] for manuscript in withdrawn], reason, fixes, UPDATED_COUNT, len(published)))

    # license, lean stub and overview
    shutil.copyfile("/usr/share/common-licenses/Apache-2.0", REPOSITORY_ROOT / "LICENSE")
    for relative, text in lean_files(len(published)).items():
        write_file(REPOSITORY_ROOT / relative, text)
    write_file(REPOSITORY_ROOT / "overview.tex", overview_tex([entry for entry in listed if entry.get("script_directory") is None]))
    write_file(REPOSITORY_ROOT / "overview.pdf", corrupted_pdf(rng, 300000, 340000))


def main():

    start = time.time()
    grammar = Grammar(SCRIPT_DIRECTORY / "grammar")
    rng = random.Random(SEED)
    clean_repository()

    # papers, withdrawals, revisions and numbering
    papers = build_papers(grammar, rng)
    withdrawn, revised = mark_revisions(grammar, rng, papers)
    entries = number_entries(papers)
    manuscripts = [entry for entry in entries if entry.get("script_directory") is None]

    # directories for every numbered manuscript
    seen_directories = {SCRIPT_DIRECTORY.name}
    for manuscript in manuscripts:
        assign_directory(manuscript, seen_directories)

    # every manuscript written, working ones queued for compiling
    published = [manuscript for manuscript in manuscripts if not (manuscript["withdrawn"] or manuscript["superseded"])]
    jobs = []
    for manuscript in manuscripts:
        job = write_manuscript(grammar, manuscript, published)
        if job is not None:
            jobs.append(job)
    print("written", len(manuscripts), "manuscript directories,", len(jobs), "to compile", flush=True)

    # figures and pdflatex in parallel
    with Pool(WORKER_COUNT) as pool:
        for index, output in enumerate(pool.imap_unordered(build_working, jobs)):
            if (index + 1) % 50 == 0:
                print("compiled", index + 1, "of", len(jobs), flush=True)

    # index files
    write_indexes(grammar, rng, entries, published, withdrawn, revised)

    # working papers by number
    for low, high in [(1, 100), (101, 300), (301, 600), (601, 100000)]:
        in_range = [manuscript for manuscript in published if low <= manuscript["number"] <= high]
        working = [manuscript for manuscript in in_range if manuscript["valid"]]
        print("numbers", low, "to", high, ":", len(working), "of", len(in_range), "manuscripts work")

    # totals
    print("manuscripts", len(published), "folders", len(manuscripts) + 1, "productions", grammar.parameter_count(), "seconds", round(time.time() - start))


if __name__ == "__main__":
    main()

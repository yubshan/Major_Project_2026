from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MARKDOWN_DIR = ROOT.parent / "markdown"
PDF_DIR = ROOT.parent / "VISITHERE"
BUILD_DIR = ROOT / ".pdf_build"

FILES = [
    ("README.md", "00_Suwarna_Roadmap_Index.pdf", "Suwarna's Decision Logic Roadmap"),
    ("roadmap.md", "01_Decision_Logic_Roadmap.pdf", "Decision Logic Roadmap"),
    ("mini_projects.md", "02_Checkbox_Mini_Projects.pdf", "Checkbox Mini-Projects"),
    ("blackboard_contract_draft.md", "03_Blackboard_Contract_Draft.pdf", "Blackboard Contract Draft"),
    ("github_linkedin_packaging.md", "04_GitHub_LinkedIn_Packaging.pdf", "GitHub and LinkedIn Packaging Guide"),
]


def normalize_pdf_text(text: str) -> str:
    return (
        text.replace("├", "+")
        .replace("└", "+")
        .replace("│", "|")
        .replace("─", "-")
        .replace("→", "->")
        .replace("×", "x")
        .replace("—", "-")
        .replace("–", "-")
    )


def tex_escape(text: str) -> str:
    text = normalize_pdf_text(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def inline_markup(text: str) -> str:
    escaped = tex_escape(text)
    escaped = re.sub(r"`([^`]+)`", r"\\texttt{\1}", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", escaped)
    return escaped


def table_to_tex(rows: list[str]) -> list[str]:
    parsed = []
    for row in rows:
        cells = [inline_markup(cell.strip()) for cell in row.strip().strip("|").split("|")]
        parsed.append(cells)
    if len(parsed) < 2:
        return [inline_markup(row) + r"\par" for row in rows]
    cols = len(parsed[0])
    widths = " ".join(["X"] * cols)
    out = [r"\begin{tabularx}{\linewidth}{" + widths + r"}", r"\toprule"]
    out.append(" & ".join(parsed[0]) + r" \\")
    out.append(r"\midrule")
    for row in parsed[2:]:
        if len(row) != cols:
            continue
        out.append(" & ".join(row) + r" \\")
    out.extend([r"\bottomrule", r"\end{tabularx}", r"\vspace{0.5em}"])
    return out


def markdown_to_tex(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    in_code = False
    code_lines: list[str] = []
    table_lines: list[str] = []

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            out.extend(table_to_tex(table_lines))
            table_lines = []

    def flush_code() -> None:
        nonlocal code_lines
        if code_lines:
            out.append(r"\begin{Verbatim}[fontsize=\small]")
            out.extend(code_lines)
            out.append(r"\end{Verbatim}")
            code_lines = []

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("```"):
            flush_table()
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(normalize_pdf_text(line))
            continue

        if line.startswith("|") and line.endswith("|"):
            table_lines.append(line)
            continue
        flush_table()

        if not line:
            out.append("")
            continue

        if line.startswith("# "):
            out.append(r"\section*{" + inline_markup(line[2:].strip()) + "}")
        elif line.startswith("## "):
            out.append(r"\subsection*{" + inline_markup(line[3:].strip()) + "}")
        elif line.startswith("### "):
            out.append(r"\subsubsection*{" + inline_markup(line[4:].strip()) + "}")
        elif line.startswith("- [ ] "):
            out.append(r"\checkbox{} " + inline_markup(line[6:].strip()) + r"\par")
        elif line.startswith("- "):
            out.append(r"\begin{itemize}[leftmargin=1.2em]\item " + inline_markup(line[2:].strip()) + r"\end{itemize}")
        elif re.match(r"^\d+\. ", line):
            out.append(r"\begin{enumerate}[leftmargin=1.4em]\item " + inline_markup(re.sub(r"^\d+\. ", "", line)) + r"\end{enumerate}")
        elif line == "---":
            out.append(r"\vspace{0.5em}\hrule\vspace{0.8em}")
        else:
            out.append(inline_markup(line) + r"\par")

    flush_table()
    flush_code()
    return "\n".join(out)


def document(title: str, body: str) -> str:
    return rf"""
\documentclass[11pt,a4paper]{{article}}
\usepackage[margin=0.75in]{{geometry}}
\usepackage{{fontenc}}
\usepackage{{lmodern}}
\usepackage{{microtype}}
\usepackage{{xcolor}}
\usepackage{{tabularx}}
\usepackage{{booktabs}}
\usepackage{{enumitem}}
\usepackage{{fancyvrb}}
\usepackage{{hyperref}}
\definecolor{{DrisyaBlue}}{{HTML}}{{174A7C}}
\definecolor{{SoftGray}}{{HTML}}{{F3F5F7}}

\newcommand{{\checkbox}}{{\fbox{{\phantom{{x}}}}}}
\hypersetup{{colorlinks=true, linkcolor=DrisyaBlue, urlcolor=DrisyaBlue}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0.45em}}
\renewcommand{{\arraystretch}}{{1.25}}
\title{{\textbf{{{tex_escape(title)}}}\\\large Project Drisya Decision Logic}}
\author{{Suwarna Pyakurel}}
\date{{}}
\begin{{document}}
\maketitle
\vspace{{-1em}}
\hrule
\vspace{{1em}}
{body}
\end{{document}}
"""


def main() -> None:
    if not shutil.which("pdflatex"):
        raise SystemExit("pdflatex is required but was not found")

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    for md_name, pdf_name, title in FILES:
        md_path = MARKDOWN_DIR / md_name
        tex_path = BUILD_DIR / md_name.replace(".md", ".tex")
        body = markdown_to_tex(md_path.read_text(encoding="utf-8"))
        tex_path.write_text(document(title, body), encoding="utf-8")
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", str(BUILD_DIR), str(tex_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )
        generated = BUILD_DIR / md_name.replace(".md", ".pdf")
        shutil.copy2(generated, PDF_DIR / pdf_name)


if __name__ == "__main__":
    main()

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


HERE = Path(__file__).resolve().parent
MANUSCRIPT = HERE.parent
CONTENT = HERE / "translation_content.md"
OUTPUT = HERE / "RK-Guard_中文翻译审校润色稿.docx"

FORMAL_ENVS = {
    "align", "align*", "equation", "equation*", "gather", "gather*",
    "multline", "multline*", "figure", "figure*", "table", "table*",
    "algorithm", "itemize", "enumerate", "definition", "theorem",
    "lemma", "proposition", "assumption", "problem", "observation",
    "strategy", "scenario", "proof",
}


def set_cell_shading(paragraph, fill: str) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    ppr.append(shd)


def set_font(run, ascii_name="Calibri", east_asia="宋体", size=11,
             bold=None, italic=None, color=None):
    run.font.name = ascii_name
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.rFonts
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:ascii"), ascii_name)
    rfonts.set(qn("w:hAnsi"), ascii_name)
    rfonts.set(qn("w:eastAsia"), east_asia)
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def add_page_field(paragraph):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, instr, separate, text, end):
        run._r.append(element)
    set_font(run, size=9, color="666666")


def extract_formal_blocks(tex: str) -> list[str]:
    lines = tex.splitlines()
    blocks: list[str] = []
    current: list[str] | None = None
    stack: list[str] = []
    begin_re = re.compile(r"\\begin\{([^}]+)\}")
    end_re = re.compile(r"\\end\{([^}]+)\}")

    for line in lines:
        begins = begin_re.findall(line)
        ends = end_re.findall(line)
        if current is None:
            selected = next((env for env in begins if env in FORMAL_ENVS), None)
            if selected is not None:
                current = [line]
                stack = list(begins)
                for env in ends:
                    if env in stack:
                        stack.remove(env)
                if not stack:
                    blocks.append("\n".join(current))
                    current = None
        else:
            current.append(line)
            stack.extend(begins)
            for env in ends:
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i] == env:
                        stack.pop(i)
                        break
            if not stack:
                blocks.append("\n".join(current))
                current = None
    return blocks


def configure_styles(doc: Document) -> None:
    # narrative_proposal preset with a named Chinese typography override.
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    normal.font.size = Pt(11)
    pf = normal.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.space_before = Pt(0)
    pf.space_after = Pt(8)
    pf.line_spacing = 1.333

    heading_tokens = {
        "Heading 1": (16, "2E74B5", 18, 10),
        "Heading 2": (13, "2E74B5", 12, 6),
        "Heading 3": (12, "1F4D78", 8, 4),
    }
    for name, (size, color, before, after) in heading_tokens.items():
        style = styles[name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    code = styles.add_style("LaTeX Block", WD_STYLE_TYPE.PARAGRAPH)
    code.font.name = "Consolas"
    code._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    code.font.size = Pt(7.5)
    code.paragraph_format.left_indent = Inches(0.12)
    code.paragraph_format.right_indent = Inches(0.08)
    code.paragraph_format.space_before = Pt(0)
    code.paragraph_format.space_after = Pt(0)
    code.paragraph_format.line_spacing = 1.0
    code.paragraph_format.keep_together = False
    code.paragraph_format.widow_control = False

    note = styles.add_style("Translation Note", WD_STYLE_TYPE.PARAGRAPH)
    note.font.name = "Calibri"
    note._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    note.font.size = Pt(9.5)
    note.font.color.rgb = RGBColor.from_string("555555")
    note.paragraph_format.space_after = Pt(6)
    note.paragraph_format.line_spacing = 1.15


def add_latex_block(doc: Document, block: str) -> None:
    lines = block.splitlines() or [""]
    for index, line in enumerate(lines):
        p = doc.add_paragraph(style="LaTeX Block")
        # Keep short formal blocks intact and prevent detached opening lines.
        p.paragraph_format.keep_together = True
        p.paragraph_format.keep_with_next = (
            index < len(lines) - 1
            and (len(lines) <= 15 or index < 2 or line.startswith("\\bibitem"))
        )
        set_cell_shading(p, "F5F7F9")
        r = p.add_run(line if line else " ")
        set_font(r, ascii_name="Consolas", east_asia="微软雅黑", size=7.5,
                 color="202124")


def add_formal_section(doc: Document, filename: str) -> None:
    source = MANUSCRIPT / filename
    blocks = extract_formal_blocks(source.read_text(encoding="utf-8"))
    if not blocks:
        return
    p = doc.add_paragraph(style="Translation Note")
    r = p.add_run("以下按源文件顺序保留本节的公式、符号定义、定理、证明、算法、表格和图片 LaTeX 语法。")
    set_font(r, size=9.5, color="555555")
    for index, block in enumerate(blocks, 1):
        label = doc.add_paragraph(style="Translation Note")
        label.paragraph_format.keep_with_next = True
        rr = label.add_run(f"LaTeX 块 {index}")
        set_font(rr, size=8.5, color="2E74B5")
        add_latex_block(doc, block)
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(2)


def add_bibliography(doc: Document) -> None:
    bbl = MANUSCRIPT / "main.bbl"
    if not bbl.exists():
        bbl = MANUSCRIPT / "ref.bib"
    p = doc.add_paragraph(style="Translation Note")
    r = p.add_run("参考文献保留为论文编译所使用的 LaTeX/BibTeX 原文，以避免作者、题名、卷期、页码及 DOI 信息在翻译中发生变化。")
    set_font(r, size=9.5, color="555555")
    add_latex_block(doc, bbl.read_text(encoding="utf-8", errors="replace"))


def add_inline_math_paragraph(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    # Preserve all inline LaTeX exactly; typography remains body style.
    cursor = 0
    for m in re.finditer(r"(\$[^$]+\$|\\[A-Za-z]+(?:\{[^{}]*\})?)", text):
        if m.start() > cursor:
            r = p.add_run(text[cursor:m.start()])
            set_font(r)
        r = p.add_run(m.group(0))
        set_font(r, ascii_name="Cambria Math", east_asia="宋体", size=10.5)
        cursor = m.end()
    if cursor < len(text):
        r = p.add_run(text[cursor:])
        set_font(r)


def build() -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)
    configure_styles(doc)

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.LEFT
    hr = header.add_run("RK-Guard 中文翻译审校润色稿")
    set_font(hr, size=8.5, color="777777")
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    add_page_field(footer)

    # Editorial-cover opening, adapted for an academic full translation.
    doc.add_paragraph().paragraph_format.space_after = Pt(72)
    kicker = doc.add_paragraph()
    kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    kr = kicker.add_run("IEEE TDSC 投稿论文 · 中文翻译审校润色稿")
    set_font(kr, ascii_name="Calibri", east_asia="微软雅黑", size=11,
             bold=True, color="9A6A20")
    kicker.paragraph_format.space_after = Pt(18)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = title.add_run("电力信息物理系统中\n面向恢复知识投毒的弹性恢复")
    set_font(tr, ascii_name="Calibri", east_asia="微软雅黑", size=25,
             bold=True, color="203748")
    title.paragraph_format.space_after = Pt(12)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = sub.add_run("Resilient Power Cyber-Physical System Restoration\nunder Recovery Knowledge Poisoning")
    set_font(sr, size=13, color="4F6472")
    sub.paragraph_format.space_after = Pt(24)

    author = doc.add_paragraph()
    author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ar = author.add_run("Kai Zhong · Zhibang Yang · Siyang Yu · Kenli Li")
    set_font(ar, size=11, bold=True, color="333333")
    author.paragraph_format.space_after = Pt(42)

    note = doc.add_paragraph(style="Translation Note")
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    nr = note.add_run("译稿说明：正文、标题、图注含义和实验分析译为中文；公式、符号、定理、证明、算法、表格、图片引用与参考文献按最终 LaTeX 源文件原样保留，便于核对与复用。")
    set_font(nr, size=9.5, color="555555")
    doc.add_page_break()

    raw = CONTENT.read_text(encoding="utf-8")
    for block in re.split(r"\n\s*\n", raw):
        block = block.strip()
        if not block:
            continue
        formal = re.fullmatch(r"\[\[FORMAL:(.+?)\]\]", block)
        if formal:
            add_formal_section(doc, formal.group(1))
            continue
        if block == "[[BIBLIOGRAPHY]]":
            add_bibliography(doc)
            continue
        if block.startswith("### "):
            doc.add_paragraph(block[4:], style="Heading 3")
        elif block.startswith("## "):
            doc.add_paragraph(block[3:], style="Heading 2")
        elif block.startswith("# "):
            doc.add_paragraph(block[2:], style="Heading 1")
        else:
            add_inline_math_paragraph(doc, block.replace("\n", " "))

    props = doc.core_properties
    props.title = "RK-Guard 中文翻译审校润色稿"
    props.subject = "恢复知识投毒下的电力信息物理系统弹性恢复"
    props.author = "作者团队；中文译稿由 Codex 根据最终 LaTeX 与 PDF 生成"
    props.keywords = "PCPS, RK-Guard, 恢复知识投毒, 知识图谱, 弹性恢复"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()

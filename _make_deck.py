from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

W, H = 13.333, 7.5
BG     = RGBColor(0x0B, 0x12, 0x20)
CARD   = RGBColor(0x14, 0x1E, 0x2E)
CARD2  = RGBColor(0x1B, 0x27, 0x3A)
LINE   = RGBColor(0x2A, 0x3A, 0x52)
TEAL   = RGBColor(0x2D, 0xD4, 0xBF)
CYAN   = RGBColor(0x38, 0xBD, 0xF8)
VIOLET = RGBColor(0xA7, 0x8B, 0xFA)
WHITE  = RGBColor(0xF1, 0xF5, 0xF9)
MUTED  = RGBColor(0x9F, 0xB0, 0xC6)
DIM    = RGBColor(0x6B, 0x7C, 0x93)

FONT = "Segoe UI"
MONO = "Consolas"

prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]


def tx(slide, x, y, w, h, text, size=14, color=WHITE, bold=False, font=FONT,
       align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0, italic=False,
       space_after=0, caps=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        p.space_after = Pt(space_after)
        r = p.add_run()
        r.text = line.upper() if caps else line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.name = font
        r.font.color.rgb = color
    return box


def rect(slide, x, y, w, h, fill=CARD, line=None, radius=0.06, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         line_w=1.0):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            s.adjustments[0] = radius
        except Exception:
            pass
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(line_w)
    s.shadow.inherit = False
    if s.has_text_frame:
        s.text_frame.text = ""
    return s


def slide_new(idx):
    s = prs.slides.add_slide(BLANK)
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(W), Inches(H))
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG
    bg.line.fill.background()
    bg.shadow.inherit = False
    return s


def est_lines(text, width_in, size, factor=0.52):
    per = max(1, int(width_in / (factor * size / 72.0)))
    return sum(max(1, -(-len(para) // per)) for para in text.split("\n"))


def header(s, kicker, title, subtitle=None, title_size=34):
    tx(s, 0.75, 0.52, 10, 0.3, kicker, 11.5, TEAL, True, caps=True)
    size = title_size
    while size > 22 and est_lines(title, 11.8, size) > 1:
        size -= 2
    tx(s, 0.75, 0.86, 11.8, 0.75, title, size, WHITE, True, spacing=0.95)

    y = 1.62
    if subtitle:
        tx(s, 0.75, 1.62, 11.5, 0.4, subtitle, 13.5, MUTED)
        y = 2.0
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.75), Inches(y), Inches(0.55), Inches(0.035))
    bar.fill.solid()
    bar.fill.fore_color.rgb = TEAL
    bar.line.fill.background()
    bar.shadow.inherit = False
    return y


def footer(s, idx, label="GraphRAG  ·  Knowledge-graph retrieval"):
    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.75), Inches(6.93), Inches(11.83), Inches(0.012))
    ln.fill.solid()
    ln.fill.fore_color.rgb = LINE
    ln.line.fill.background()
    ln.shadow.inherit = False
    tx(s, 0.75, 7.03, 8, 0.25, label, 9.5, DIM)
    tx(s, 10.6, 7.03, 2.0, 0.25, f"{idx:02d} / 10", 9.5, DIM, align=PP_ALIGN.RIGHT)


def card(s, x, y, w, h, title, body, accent=TEAL, tsize=15.5, bsize=11.5,
         fill=CARD, icon=None, radius=0.07):
    rect(s, x, y, w, h, fill=fill, radius=radius)
    strip = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x + 0.02), Inches(y + 0.22), Inches(0.055), Inches(h - 0.44))
    strip.adjustments[0] = 0.5
    strip.fill.solid()
    strip.fill.fore_color.rgb = accent
    strip.line.fill.background()
    strip.shadow.inherit = False
    top = y + 0.24
    if icon:
        tx(s, x + 0.3, top, 0.8, 0.3, icon, 16, accent, True)
        top += 0.38
    tx(s, x + 0.3, top, w - 0.55, 0.7, title, tsize, WHITE, True, spacing=0.95)
    tx(s, x + 0.3, top + (0.62 if len(title) < 34 else 0.86), w - 0.55, h - (top - y) - 0.85,
       body, bsize, MUTED, spacing=1.28)


# ---------------------------------------------------------------- 1. title
s = slide_new(1)
# decorative node-link motif
nodes = [(10.35, 1.55, 0.30, TEAL), (11.85, 2.35, 0.24, CYAN), (9.85, 3.05, 0.20, VIOLET),
         (11.35, 3.75, 0.26, TEAL), (10.45, 4.45, 0.18, CYAN), (12.25, 1.45, 0.16, DIM)]
edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4), (1, 5), (5, 3)]
for a, b in edges:
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                Inches(nodes[a][0]), Inches(nodes[a][1]),
                                Inches(nodes[b][0]), Inches(nodes[b][1]))
    ln.line.color.rgb = RGBColor(0x33, 0x4B, 0x66)
    ln.line.width = Pt(1.1)
for cx, cy, d, c in nodes:
    o = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d / 2), Inches(cy - d / 2), Inches(d), Inches(d))
    o.fill.solid()
    o.fill.fore_color.rgb = c
    o.line.fill.background()
    o.shadow.inherit = False

tx(s, 0.9, 1.35, 7.5, 0.3, "Retrieval-augmented generation  ·  case study", 12, TEAL, True, caps=True)
tx(s, 0.85, 1.78, 8.6, 1.3, "GraphRAG", 78, WHITE, True, spacing=0.9)
tx(s, 0.9, 3.0, 7.9, 0.85, "Retrieval-augmented generation with a\nknowledge-graph memory", 25, WHITE, True, spacing=1.1)
tx(s, 0.9, 4.05, 7.4, 0.6, "Vectors for recall. A graph for relationships.\nCited answers over your own documents.", 14, MUTED, spacing=1.35)

chips = ["FastAPI", "MongoDB / Neo4j", "ChromaDB", "React + TypeScript"]
x = 0.9
for c in chips:
    w = 0.28 + len(c) * 0.093
    rect(s, x, 4.9, w, 0.42, fill=CARD2, radius=0.4)
    tx(s, x, 4.99, w, 0.24, c, 10.5, MUTED, align=PP_ALIGN.CENTER)
    x += w + 0.14

ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.9), Inches(5.56), Inches(2.6), Inches(0.02))
ln.fill.solid(); ln.fill.fore_color.rgb = LINE; ln.line.fill.background(); ln.shadow.inherit = False
tx(s, 0.9, 5.7, 6, 0.24, "Presented by", 8.5, DIM, True, caps=True)
tx(s, 0.9, 5.92, 6.5, 0.32, "Simran   ·   UID 25MCI10196", 13.5, WHITE, True)
tx(s, 0.9, 6.22, 7.2, 0.26, "Course 25CAH-724   ·   Submitted to Ashaq Hussain Bhat", 10.5, MUTED)

tx(s, 0.9, 6.62, 8, 0.3, "Hybrid retrieval  ·  entity linking  ·  N-hop expansion  ·  provenance on every answer",
   10.5, DIM)
footer(s, 1, "Offline-first  ·  Docker-ready  ·  Tested end to end")

# ---------------------------------------------------------------- 2. problem
s = slide_new(2)
header(s, "01  ·  The problem", "Flat vector RAG breaks on multi-hop questions",
       "Semantic search over chunks is excellent at one hop — and blind beyond it.")

rect(s, 0.75, 2.2, 11.83, 1.15, fill=CARD, radius=0.06)
qbar = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.77), Inches(2.42), Inches(0.06), Inches(0.71))
qbar.fill.solid(); qbar.fill.fore_color.rgb = VIOLET; qbar.line.fill.background(); qbar.shadow.inherit = False
tx(s, 1.15, 2.4, 11.0, 0.8,
   "“Which supplier makes the actuator used by the robot that failed at the Rotterdam site?”",
   19, WHITE, italic=True, anchor=MSO_ANCHOR.MIDDLE, spacing=1.15)

cards2 = [
    ("Fragmented", "No chunk has the whole answer", "It lives across a platform overview, a supplier contract and an incident report.", CYAN),
    ("Similar, not related", "Embeddings capture similarity", "They do not encode that Atlas-7 USES the Helios actuator, or who SUPPLIES it.", VIOLET),
    ("Unverifiable", "Answers lack provenance", "Without chunk-level citations, a confident sentence cannot be checked.", TEAL),
]
x = 0.75
for kick, t, b, c in cards2:
    rect(s, x, 3.6, 3.79, 1.85, fill=CARD, radius=0.07)
    tx(s, x + 0.3, 3.82, 3.2, 0.25, kick, 10.5, c, True, caps=True)
    tx(s, x + 0.3, 4.12, 3.25, 0.6, t, 13.5, WHITE, True, spacing=1.05)
    by = 4.12 + 0.29 * est_lines(t, 3.25, 13.5) + 0.1
    tx(s, x + 0.3, by, 3.25, 5.3 - by, b, 10.8, MUTED, spacing=1.28)
    x += 4.02

tx(s, 0.75, 5.62, 11.83, 0.4, "Multi-hop reasoning needs explicit structure, not a wider context window.",
   15, WHITE, True)
tx(s, 0.75, 6.1, 11.83, 0.5,
   "Stuffing more near-miss chunks into the prompt raises cost and latency while making the answer harder to trust.",
   11.5, MUTED)
footer(s, 2)

# ---------------------------------------------------------------- 3. idea
s = slide_new(3)
header(s, "02  ·  The approach", "Keep both: vector recall, graph precision",
       "The pipeline extracts entities and relations at ingestion, then walks them at query time.")

# left panel
rect(s, 0.75, 2.25, 4.3, 2.75, fill=CARD, radius=0.06)
tx(s, 1.05, 2.5, 3.7, 0.3, "Vector search", 17, WHITE, True)
tx(s, 1.05, 2.85, 3.7, 0.28, "RECALL OVER PROSE", 10, CYAN, True, caps=True)
tx(s, 1.05, 3.22, 3.65, 1.55,
   "• Dense nearest-neighbour over chunks\n• Finds paraphrases and long-tail wording\n• Fast, but unaware of relationships",
   11.5, MUTED, spacing=1.5)

# right panel
rect(s, 8.28, 2.25, 4.3, 2.75, fill=CARD, radius=0.06)
tx(s, 8.58, 2.5, 3.7, 0.3, "Graph traversal", 17, WHITE, True)
tx(s, 8.58, 2.85, 3.7, 0.28, "PRECISION OVER RELATIONS", 10, VIOLET, True, caps=True)
tx(s, 8.58, 3.22, 3.65, 1.55,
   "• Entity linking → N-hop expansion\n• Typed edges make hops explicit\n• Every path is explainable",
   11.5, MUTED, spacing=1.5)

# fusion centre
rect(s, 5.35, 2.95, 2.63, 1.35, fill=CARD2, radius=0.1, line=TEAL)
tx(s, 5.35, 3.18, 2.63, 0.3, "FUSION", 11, TEAL, True, align=PP_ALIGN.CENTER, caps=True)
tx(s, 5.35, 3.52, 2.63, 0.55, "0.6 vector\n0.4 graph", 12, WHITE, True, align=PP_ALIGN.CENTER, spacing=1.2)
for x0, x1 in ((5.06, 5.33), (8.0, 8.27)):
    ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x0), Inches(3.62), Inches(x1), Inches(3.62))
    ln.line.color.rgb = RGBColor(0x33, 0x4B, 0x66)
    ln.line.width = Pt(1.2)

# path example
tx(s, 0.75, 5.25, 11.83, 0.3, "The hop the graph makes explicit", 10.5, DIM, True, caps=True)
path = [("Atlas-7", "robot", CYAN), ("USES", "relation", VIOLET), ("Helios actuator", "part", CYAN),
        ("SUPPLIES", "relation", VIOLET), ("Kestrel Metals", "supplier", CYAN)]
x = 0.75
for label, sub, c in path:
    if sub == "relation":
        tx(s, x, 5.63, 1.25, 0.4, "→", 16, VIOLET, True, align=PP_ALIGN.CENTER)
        tx(s, x, 5.98, 1.25, 0.25, label, 8.5, VIOLET, align=PP_ALIGN.CENTER)
        x += 1.25
    else:
        w = max(1.75, 0.3 + len(label) * 0.115)
        rect(s, x, 5.55, w, 0.66, fill=CARD, line=LINE, radius=0.16)
        tx(s, x, 5.68, w, 0.28, label, 11.5, WHITE, True, align=PP_ALIGN.CENTER)
        tx(s, x, 5.96, w, 0.22, sub, 8, DIM, align=PP_ALIGN.CENTER)
        x += w + 0.1

tx(s, 0.75, 6.35, 11.83, 0.3,
   "Every citation carries its chunk id, document id and origin: vector, graph, or both.",
   11.5, MUTED)
footer(s, 3)

# ---------------------------------------------------------------- 4. architecture
s = slide_new(4)
header(s, "03  ·  Architecture", "One interface per layer, two implementations",
       "The same application code runs fully offline or on the production stack.")

# band 1 frontend
rect(s, 0.75, 2.15, 11.83, 0.92, fill=CARD, radius=0.06)
tx(s, 1.05, 2.34, 3.2, 0.3, "React 18  +  Vite  +  Tailwind", 13.5, WHITE, True)
tx(s, 1.05, 2.66, 10.9, 0.28, "Dashboard · Documents · Chat (SSE) · Graph explorer · Analytics · Admin · Profile",
   10.5, MUTED)
tx(s, 11.0, 2.34, 1.4, 0.3, "CLIENT", 9.5, CYAN, True, align=PP_ALIGN.RIGHT, caps=True)

tx(s, 3.9, 3.11, 5.0, 0.24, "▼  REST + SSE  ·  JWT bearer", 8.5, DIM, align=PP_ALIGN.CENTER)

# band 2 api
rect(s, 0.75, 3.38, 11.83, 1.5, fill=CARD, radius=0.05, line=RGBColor(0x24, 0x4A, 0x50), line_w=1.0)
tx(s, 1.05, 3.55, 4.0, 0.3, "FastAPI", 14.5, TEAL, True)
tx(s, 1.05, 3.9, 3.5, 0.85,
   "routes/  auth · documents · search\nchat · graph · analytics · admin\nmiddleware/  request-id · rate-limit · errors",
   9.8, MUTED, spacing=1.35)
tx(s, 4.75, 3.9, 3.6, 0.85,
   "services/  parsing → chunking → extraction\nHybridRetriever · ChatService · memory\nGraphAgent (plan / retrieve / reflect)",
   9.8, MUTED, spacing=1.35)
tx(s, 8.65, 3.9, 3.6, 0.85,
   "container.py  dependency wiring\nasync ingestion tasks\nLLM · Embedder · Store interfaces",
   9.8, MUTED, spacing=1.35)
tx(s, 11.0, 3.55, 1.4, 0.3, "SERVER", 9.5, TEAL, True, align=PP_ALIGN.RIGHT, caps=True)

tx(s, 6.15, 4.94, 1.1, 0.24, "▼", 8.5, DIM, align=PP_ALIGN.CENTER)

# band 3 stores
stores = [
    ("MongoDB  /  memory", "users, documents, chunks,\nconversations, memories", CYAN),
    ("Neo4j  /  Kuzu", "entities, relations,\nMENTIONED_IN links", VIOLET),
    ("ChromaDB  /  NumPy", "chunk embeddings,\nmetadata filters", TEAL),
]
x = 0.75
for name, body, c in stores:
    rect(s, x, 5.2, 3.83, 1.2, fill=CARD, radius=0.06)
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.28), Inches(5.42), Inches(0.12), Inches(0.12))
    dot.fill.solid(); dot.fill.fore_color.rgb = c; dot.line.fill.background(); dot.shadow.inherit = False
    tx(s, x + 0.5, 5.34, 3.1, 0.3, name, 12.5, WHITE, True)
    tx(s, x + 0.28, 5.68, 3.35, 0.55, body, 10, MUTED, spacing=1.25)
    x += 3.99

tx(s, 0.75, 6.52, 11.83, 0.28,
   "Interfaces:  Database  ·  GraphStore  ·  VectorStore  ·  LLM  ·  Embedder        "
   "Switching a backend is configuration, not a rewrite.", 9.8, DIM)
footer(s, 4)

# ---------------------------------------------------------------- 5. ingestion
s = slide_new(5)
header(s, "04  ·  Ingestion", "From upload to a queryable graph",
       "PDF, DOCX, TXT and Markdown — parsed, chunked, embedded, extracted, linked.")

steps = [
    ("01", "Upload & validate", "Type and size checks, document row persisted with status processing.", CYAN),
    ("02", "Parse & chunk", "Paragraph-aware cleanup, token-aware windows with overlap, heading context kept.", CYAN),
    ("03", "Embed & index", "Batched embeddings upserted into the vector store with metadata.", TEAL),
    ("04", "Extract", "LLM entity/relation JSON with a deterministic regex/NER fallback.", VIOLET),
    ("05", "Link & publish", "Entities resolved and deduped, typed relations and mentions written, status ready.", VIOLET),
]
x = 0.75
for num, t, b, c in steps:
    rect(s, x, 2.18, 2.22, 2.55, fill=CARD, radius=0.06)
    tx(s, x + 0.26, 2.38, 1.0, 0.3, num, 11, c, True)
    tx(s, x + 0.26, 2.72, 1.7, 0.65, t, 13.5, WHITE, True, spacing=1.0)
    tx(s, x + 0.26, 3.45, 1.7, 1.12, b, 10.2, MUTED, spacing=1.25)
    if num != "05":
        ln = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x + 2.23), Inches(3.45),
                                    Inches(x + 2.39), Inches(3.45))
        ln.line.color.rgb = RGBColor(0x3F, 0x54, 0x70)
        ln.line.width = Pt(1.6)
    x += 2.4

facts = [
    ("Asynchronous & cancellable", "Per-document progress and status:\npending → processing → ready | failed"),
    ("Retry without re-upload", "reingest re-runs the full pipeline,\nsame document id and citations"),
    ("Consistency by compensation", "Three stores are not transactional;\nfailed graph writes compensate deletes"),
]
x = 0.75
for t, b in facts:
    rect(s, x, 4.95, 3.83, 1.5, fill=CARD2, radius=0.06)
    tx(s, x + 0.28, 5.14, 3.3, 0.3, t, 12, WHITE, True)
    tx(s, x + 0.28, 5.55, 3.35, 0.75, b, 10.2, MUTED, spacing=1.3)
    x += 3.99

tx(s, 0.75, 6.6, 11.83, 0.28,
   "A failed graph write downgrades the answer path to vector-only with a warning — the upload still succeeds.",
   10, DIM)
footer(s, 5)

# ---------------------------------------------------------------- 6. retrieval
s = slide_new(6)
header(s, "05  ·  Retrieval", "Three retrievers run in parallel, then fuse",
       "Dense search, entity→chunk lookup and N-hop expansion, merged by weighted rank fusion.")

lanes = [
    ("Dense vectors", "Top K × 2 by cosine similarity\nover chunk embeddings", CYAN),
    ("Entity lookup", "Question entities linked to\nchunks that mention them", TEAL),
    ("Graph expansion", "N hops (default 2) from linked\nentities, scored by confidence", VIOLET),
]
x = 0.75
for t, b, c in lanes:
    rect(s, x, 2.18, 3.83, 1.3, fill=CARD, radius=0.06)
    tx(s, x + 0.3, 2.36, 3.3, 0.3, t, 13.5, c, True)
    tx(s, x + 0.3, 2.72, 3.35, 0.62, b, 10.3, MUTED, spacing=1.28)
    x += 3.99

tx(s, 5.4, 3.55, 2.5, 0.3, "▼   ▼   ▼", 11, DIM, align=PP_ALIGN.CENTER)

rect(s, 0.75, 3.92, 11.83, 1.2, fill=CARD2, radius=0.05, line=RGBColor(0x24, 0x4A, 0x50))
tx(s, 1.05, 4.08, 3.0, 0.25, "FUSION SCORE", 10, TEAL, True, caps=True)
tx(s, 1.05, 4.38, 11.2, 0.42,
   "score = w_v · ( 0.75 · vector_norm + 0.25 · reciprocal_rank ) + w_g · graph_confidence",
   15, WHITE, True, font=MONO)
tx(s, 1.05, 4.82, 11.2, 0.25, "defaults   VECTOR_WEIGHT = 0.6      GRAPH_WEIGHT = 0.4", 9.5, DIM, font=MONO)

notes = [
    ("Rewritten first", "Follow-ups resolved against the conversation summary before any search runs.", CYAN),
    ("Hydrated citations", "Graph-only chunks are re-read from the vector store so every citation has text.", TEAL),
    ("Confidence, not vibes", "A score derived from fused evidence, returned with the answer.", VIOLET),
]
x = 0.75
for t, b, c in notes:
    rect(s, x, 5.38, 3.83, 1.15, fill=CARD, radius=0.06)
    tx(s, x + 0.28, 5.56, 3.3, 0.28, t, 12, c, True)
    tx(s, x + 0.28, 5.9, 3.35, 0.55, b, 10, MUTED, spacing=1.25)
    x += 3.99

tx(s, 0.75, 6.62, 11.83, 0.28,
   "If the graph is unreachable, retrieval logs and returns vector-only results with strategy = vector. Chat never hard-fails.",
   9.8, DIM)
footer(s, 6)

# ---------------------------------------------------------------- 7. answering
s = slide_new(7)
header(s, "06  ·  Answering", "A chain, not a single prompt",
       "Rewrite → plan → retrieve → synthesize → cite → verify → reflect.")

chain = ["Rewrite", "Plan", "Retrieve", "Synthesize", "Cite", "Verify", "Reflect"]
x = 0.75
for i, step in enumerate(chain):
    c = TEAL if i in (0, 4, 5, 6) else CYAN
    rect(s, x, 2.2, 1.45, 0.92, fill=CARD, line=c, radius=0.12)
    tx(s, x, 2.32, 1.45, 0.25, f"{i+1}", 8.5, c, True, align=PP_ALIGN.CENTER)
    tx(s, x, 2.58, 1.45, 0.3, step, 10.5, WHITE, True, align=PP_ALIGN.CENTER)
    if i < len(chain) - 1:
        tx(s, x + 1.45, 2.55, 0.27, 0.3, "›", 15, DIM, True, align=PP_ALIGN.CENTER)
    x += 1.72

rect(s, 0.75, 3.35, 5.75, 2.55, fill=CARD, radius=0.06)
tx(s, 1.05, 3.55, 4.9, 0.3, "What the model actually receives", 13.5, WHITE, True)
tx(s, 1.05, 3.98, 5.15, 1.75,
   "• System rules and answer style\n"
   "• Numbered source chunks with ids\n"
   "• Graph triplets from the expansion\n"
   "• Recalled long-term memories\n"
   "• Rolling conversation summary\n"
   "• Answer-style preference from the profile",
   11.2, MUTED, spacing=1.32)

rect(s, 6.78, 3.35, 5.8, 2.55, fill=CARD, radius=0.06)
tx(s, 7.08, 3.55, 4.9, 0.3, "What every answer ships with", 13.5, WHITE, True)
tx(s, 7.08, 3.98, 5.2, 1.75,
   "• Inline [n] citations tied to chunk + document\n"
   "• Source badge: vector, graph, or both\n"
   "• Confidence score and reasoning trace\n"
   "• Graph paths used to reach the answer\n"
   "• Suggested follow-up questions\n"
   "• Markdown / JSON export of the thread",
   11.2, MUTED, spacing=1.32)

tx(s, 0.75, 6.08, 11.83, 0.3,
   "Streamed token by token over SSE (meta → graph → token → done), with 👍 / 👎 feedback per message.",
   11, MUTED)
footer(s, 7)

# ---------------------------------------------------------------- 8. frontend
s = slide_new(8)
header(s, "07  ·  Interface", "A dashboard that shows its work",
       "React 18 + TypeScript + Vite, hand-written shadcn-style components, React Flow for the graph.")

pages = [
    ("Dashboard", "Corpus stats, graph size, recent documents, quick actions.", CYAN),
    ("Documents", "Drag-and-drop upload with live progress, status polling, reingest, delete.", CYAN),
    ("Chat", "Streaming answers, inline citations, graph-path drawer, confidence, follow-ups, export.", TEAL),
    ("Graph", "Force layout coloured by entity type, search, hop control, Cypher console.", VIOLET),
    ("Analytics", "Daily volume, token spend, latency, top documents, inventory.", TEAL),
    ("Admin", "Users and roles, all documents, error logs, runtime configuration.", VIOLET),
    ("Profile", "Name, default answer style, password rotation, session info.", DIM),
]
pos = [(0.75, 2.18), (4.74, 2.18), (8.73, 2.18),
       (0.75, 3.72), (4.74, 3.72), (8.73, 3.72),
       (0.75, 5.26)]
for (t, b, c), (x, y) in zip(pages, pos):
    w = 3.85 if not (t == "Chat") else 3.85
    rect(s, x, y, w, 1.34, fill=CARD, radius=0.06)
    tx(s, x + 0.28, y + 0.18, w - 0.5, 0.28, t, 13, c, True)
    tx(s, x + 0.28, y + 0.54, w - 0.55, 0.7, b, 10, MUTED, spacing=1.25)

rect(s, 4.74, 5.26, 7.84, 1.34, fill=CARD2, radius=0.06, line=RGBColor(0x24, 0x4A, 0x50))
tx(s, 5.02, 5.44, 7.3, 0.28, "Read-only by construction", 13, TEAL, True)
tx(s, 5.02, 5.8, 7.3, 0.65,
   "The Cypher console accepts MATCH / RETURN only — write and procedure clauses rejected, rows and characters truncated, queries time-boxed.",
   10, MUTED, spacing=1.25)
footer(s, 8)

# ---------------------------------------------------------------- 9. engineering
s = slide_new(9)
header(s, "08  ·  Engineering", "Built to be inspected, not just demoed",
       "Offline defaults, real abstractions, and the unglamorous parts done properly.")

cols = [
    ("Pluggable by design", CYAN, [
        "Database, GraphStore, VectorStore, LLM and Embedder sit behind abstract bases.",
        "Offline: memory + Kuzu + NumPy + hash embeddings + extractive LLM.",
        "Production: MongoDB + Neo4j + ChromaDB + OpenAI, same call sites.",
        "Tests exercise the real pipeline, not a parallel mock one.",
    ]),
    ("Secure and guarded", TEAL, [
        "JWT access + refresh with bcrypt hashes, role-based access.",
        "Per-identity rate limiting, request ids, one error envelope.",
        "Every entity, chunk, memory and chat is scoped by user_id.",
        "Structured logs persisted for admin review.",
    ]),
    ("Verified offline", VIOLET, [
        "Pytest suite runs with no server, no API key, no network.",
        "Covers auth, upload and ingestion, chunking and extraction.",
        "Covers fusion, citations, memory, Cypher guards, admin auth.",
        "seed_demo.py smoke-tests the real HTTP stack end to end.",
    ]),
]
x = 0.75
for t, c, bullets in cols:
    rect(s, x, 2.16, 3.83, 3.75, fill=CARD, radius=0.06)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(2.16), Inches(3.83), Inches(0.05))
    bar.fill.solid(); bar.fill.fore_color.rgb = c; bar.line.fill.background(); bar.shadow.inherit = False
    tx(s, x + 0.3, 2.42, 3.2, 0.3, t, 14, WHITE, True)
    yy = 2.92
    for b in bullets:
        tx(s, x + 0.3, yy, 0.16, 0.3, "—", 10, c, True)
        tx(s, x + 0.58, yy, 2.95, 0.8, b, 10.4, MUTED, spacing=1.24)
        yy += 0.72
    x += 3.99

tx(s, 0.75, 6.14, 11.83, 0.35,
   "Honest defaults: the offline LLM is explicitly extractive and /health warns when dev defaults reach production.",
   11.5, WHITE, True)
tx(s, 0.75, 6.55, 11.83, 0.3,
   "/health reports the active backend for every layer, so a misconfigured deployment is obvious in one request.",
   10, DIM)
footer(s, 9)

# ---------------------------------------------------------------- 10. get started
s = slide_new(10)
header(s, "09  ·  Getting started", "Runs on a laptop in one command",
       "Python 3.11+ and Node 18+. No Docker, no database server, no API key required.")

rect(s, 0.75, 2.2, 6.6, 3.45, fill=RGBColor(0x0F, 0x18, 0x27), radius=0.05, line=LINE)
tx(s, 1.02, 2.38, 5.6, 0.25, "QUICKSTART", 9.5, TEAL, True, caps=True)
code = [
    ("$", "cp .env.example .env"),
    ("$", "cd backend  &&  pip install -r requirements.txt"),
    ("$", "uvicorn app.main:app --reload --port 8000"),
    ("$", "cd frontend  &&  npm install  &&  npm run dev"),
    ("", ""),
    ("#", "docker compose up -d --build   →  UI :8080"),
]
yy = 2.72
for prompt, line in code:
    if not prompt:
        yy += 0.12
        continue
    if prompt:
        tx(s, 1.02, yy, 0.25, 0.28, prompt, 10, TEAL if prompt == "$" else DIM, font=MONO)
    tx(s, 1.28, yy, 5.9, 0.28, line, 10.2, WHITE if prompt == "$" else MUTED, font=MONO)
    yy += 0.42

rect(s, 7.55, 2.2, 5.03, 3.45, fill=CARD, radius=0.06)
tx(s, 7.83, 2.38, 4.5, 0.3, "Try these questions", 13, WHITE, True)
qs = ["Which supplier manufactures the\nHelios actuator used by the Atlas-7?",
      "What happened in incident 4471 and\nwhich site was affected?",
      "How does Project Lighthouse reduce\nrecalibration downtime?"]
yy = 2.78
for q in qs:
    tx(s, 7.83, yy, 4.45, 0.72, q, 10.6, MUTED, spacing=1.25)
    yy += 0.78
tx(s, 7.83, 5.24, 4.4, 0.25, "sign in:  admin@graphrag.ai  /  Admin12345!", 8.8, DIM, font=MONO)

# closing band
rect(s, 0.75, 5.92, 11.83, 0.85, fill=CARD2, radius=0.05)
tx(s, 1.05, 6.06, 3.6, 0.25, "THE RESULT", 9.5, TEAL, True, caps=True)
tx(s, 1.05, 6.32, 11.3, 0.3,
   "Multi-hop answers over your own documents, every claim traceable to a chunk, and the graph path that found it.",
   12.5, WHITE, True)
footer(s, 10, "Thank you  ·  Simran  ·  UID 25MCI10196")

prs.core_properties.author = "Simran (25MCI10196)"
prs.core_properties.last_modified_by = "Simran"
prs.core_properties.title = "GraphRAG — Retrieval-augmented generation with a knowledge-graph memory"
prs.core_properties.subject = "Course 25CAH-724 · Submitted to Ashaq Hussain Bhat"
prs.core_properties.keywords = "GraphRAG, RAG, knowledge graph, NLP, 25CAH-724"

NOTES = [
    "GraphRAG is a retrieval-augmented generation service that answers questions over your own "
    "documents. The point of the project is the memory: instead of only stuffing the prompt with "
    "the nearest text chunks, it also keeps a knowledge graph of entities and relations, and walks "
    "that graph before the model writes a word. Everything runs offline on a laptop by default, and "
    "the same code runs on MongoDB, Neo4j, ChromaDB and OpenAI in Docker.",

    "Start with the failure that motivated the project. The Rotterdam question looks simple but no "
    "single chunk contains the answer: the platform, the supplier contract and the incident report "
    "each hold one piece. Embeddings encode topical similarity, not relationships, so retrieval "
    "returns near-misses. And even when the answer is right, without citations nobody can check it.",

    "The design keeps both retrieval modes. Vectors give recall over prose: they find paraphrases "
    "and unusual wording. Graph traversal gives precision over relations: entity linking followed "
    "by two-hop expansion. Each lane is scored, normalised and fused with configurable weights, so "
    "the answer is grounded in both kinds of evidence and every hop is explainable.",

    "Architecturally, the important decision is one interface per layer with two implementations "
    "behind it: memory or MongoDB, Kuzu or Neo4j, NumPy or ChromaDB, hash embeddings or OpenAI. The "
    "application code never knows which is active, so the offline stack and the production stack "
    "exercise exactly the same pipeline - which is also why the tests are meaningful.",

    "Ingestion is asynchronous and cancellable. A document is validated, parsed, cleaned and chunked "
    "with heading context preserved, embedded in batches, then mined for entities and relations with "
    "an LLM and a deterministic regex fallback. Entities are resolved and deduplicated before typed "
    "relations, mentions and document links are written. Three stores are not transactional, so a "
    "failed graph write compensates with deletes and downgrades the answer path instead of failing "
    "the upload.",

    "Retrieval runs three lanes concurrently: dense vector search over chunks, an entity to chunk "
    "lookup, and a two-hop graph expansion. The fusion score combines normalised vector similarity, "
    "a reciprocal-rank term and graph confidence. Graph-only chunks are re-hydrated from the vector "
    "store so every citation has text. If the graph is down, retrieval degrades to vector-only with "
    "a warning rather than failing the request.",

    "Answering is a chain rather than one prompt: rewrite the follow-up, plan, retrieve, synthesise, "
    "cite, verify the citations, then reflect. The prompt carries numbered sources, graph triplets, "
    "recalled long-term memories and a rolling conversation summary. Every answer returns citations, "
    "a confidence score, the graph paths used, a reasoning trace and follow-ups, streamed over SSE "
    "with per-message feedback.",

    "The frontend is React 18 and TypeScript with hand-written shadcn-style components and React Flow "
    "for the graph. Seven pages: dashboard, documents, chat, graph explorer, analytics, admin and "
    "profile. The Cypher console is read-only by construction - MATCH and RETURN only, statements "
    "validated, rows and characters capped, queries time-boxed.",

    "Engineering choices worth calling out: offline defaults are honest, so the mock LLM is explicitly "
    "extractive and /health warns when development defaults are used in production. Security is JWT "
    "with refresh rotation and role-based access, with per-identity rate limiting and user-scoped "
    "data. The pytest suite runs with no server, no API key and no network, and a seed script "
    "smoke-tests the real HTTP stack end to end.",

    "Getting started is deliberately boring: Python and Node, copy the env file, install and run. No "
    "Docker, no database server, no API key. Upload the sample corpus, sign in with the bootstrapped "
    "admin account, and the sample questions exercise multi-hop reasoning, incident lookup and "
    "process explanation. The result is multi-hop answers over your own documents where every claim "
    "traces back to a chunk and to the graph path that found it.",
]

for i, slide in enumerate(prs.slides):
    if i < len(NOTES):
        slide.notes_slide.notes_text_frame.text = NOTES[i]

prs.save("GraphRAG.pptx")
print("saved", len(prs.slides), "slides")

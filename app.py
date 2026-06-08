"""Gradio web UI for The Unofficial Guide (Milestone 5, item 6).

A minimal query interface: type a question, get a grounded answer plus the
sources it drew from. Wraps the end-to-end pipeline in generate.answer().

Run:  python app.py   ->  open http://localhost:7860
"""

from __future__ import annotations

import gradio as gr

from generate import answer


def handle_query(question: str) -> tuple[str, str]:
    """Run one question through the pipeline; return (answer, sources) text."""
    if not question.strip():
        return "Please enter a question.", ""
    result = answer(question)
    # On a refusal there are no sources, so show a clear placeholder instead.
    sources = "\n".join(f"• {s}" for s in result.sources) or "—"
    return result.text, sources


# Custom styling: brand the primary button dark teal.
CSS = """
#ask-btn {
    background: #0D3B3C !important;
    background-image: none !important;
    border-color: #0D3B3C !important;
    color: #ffffff !important;
}
#ask-btn:hover { background: #0a2e2f !important; border-color: #0a2e2f !important; }
"""

with gr.Blocks(title="The Unofficial Guide") as demo:
    gr.Markdown(
        "# The Unofficial Guide\n"
        "Ask about how founders built profitable products and income streams. "
        "Answers are grounded only in the collected case studies."
    )
    question = gr.Textbox(
        label="Your question",
        placeholder="e.g. What business models did these founders use to make money?",
    )
    ask_btn = gr.Button("Ask", variant="primary", elem_id="ask-btn")
    answer_box = gr.Textbox(label="Answer", lines=8)
    sources_box = gr.Textbox(label="Sources", lines=4)

    # Trigger on both the button and pressing Enter in the textbox.
    ask_btn.click(handle_query, inputs=question, outputs=[answer_box, sources_box])
    question.submit(handle_query, inputs=question, outputs=[answer_box, sources_box])


if __name__ == "__main__":
    demo.launch(css=CSS)

"""
Updated vision prompt builder — reads visual_focus_areas from platform config
and injects them into the Claude vision prompt for platform-specific analysis.

This file patches visual_inspector.py's _analyze_with_claude_vision method.
Replace the prompt string in visual_inspector.py with build_vision_prompt().
"""


def build_vision_prompt(url: str, viewport: dict, config: dict) -> str:
    """
    Build a Claude vision prompt tailored to the platform config.
    Reads visual_focus_areas from qa_config.yaml and injects them.
    """
    focus_areas = config.get("visual_focus_areas", [])
    focus_section = ""
    if focus_areas:
        focus_section = "\n\nPLATFORM-SPECIFIC CHECKS (check these in particular):\n"
        for i, area in enumerate(focus_areas, 1):
            focus_section += f"{i}. {area}\n"

    return f"""You are a senior QA engineer and UX expert reviewing a screenshot of a web application.

Page URL: {url}
Viewport: {viewport['name']} ({viewport['width']}x{viewport['height']}px)
{focus_section}
Examine this screenshot with extreme thoroughness and identify EVERY visual issue.

Standard checks:
1. LAYOUT: Overlapping elements, misaligned items, broken grid, inconsistent spacing
2. TYPOGRAPHY: Truncated text, wrong font sizes, inconsistent fonts, unreadable text
3. RESPONSIVE: Elements that don't fit this viewport, content cut off, touch targets too small
4. IMAGES & ICONS: Broken images, distorted assets, missing icons
5. COLOUR & CONTRAST: Hard-to-read text, low contrast, inconsistent colours
6. FORMS: Misaligned labels, broken inputs, unclear error states
7. EMPTY STATES: Tables/lists with no data and no empty state message
8. LOADING: Visible spinners where content should be, skeleton screens
9. NUMBERS: Incorrect formatting — for Indian platforms check ₹ symbol, lakh/crore notation
10. GENERAL: Anything unprofessional, incomplete, or inconsistent

For each issue found, respond with a JSON array. Each item must have:
- "type": short category (e.g. "layout_overlap", "truncated_text")
- "severity": "CRITICAL" | "MAJOR" | "MINOR" | "COSMETIC"
- "description": specific, actionable description with location on page
- "element": which UI element or section

If the page looks completely clean, return an empty array [].
Return ONLY the JSON array, no other text."""

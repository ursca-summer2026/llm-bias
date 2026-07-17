# LLM Bias Research Toolkit - Presentation

This directory contains a comprehensive Quarto presentation introducing the LLM Bias Research Toolkit.

## Contents

- **`intro.qmd`** - Main presentation file (Quarto markdown)
- **`custom.scss`** - Custom styling (colorblind-safe palette matching dashboard)
- **`README.md`** - This file

## Viewing the Presentation

### Option 1: Render to HTML (Recommended)

```bash
# Install Quarto (if not already installed)
# macOS
brew install quarto

# Linux
curl -LO https://quarto.org/download/latest/quarto-linux-amd64.deb
sudo dpkg -i quarto-linux-amd64.deb

# Windows - Download from https://quarto.org/docs/get-started/

# Navigate to presentation directory
cd llm-bias-research/docs/presentation

# Render presentation
quarto render intro.qmd

# Open in browser
open intro.html  # macOS
xdg-open intro.html  # Linux
start intro.html  # Windows
```

### Option 2: Live Preview

```bash
cd llm-bias-research/docs/presentation
quarto preview intro.qmd
```

This opens a browser with live reload - edit `intro.qmd` and see changes instantly!

### Option 3: Export to PDF

```bash
# Requires Chrome or Chromium
quarto render intro.qmd --to pdf
```

## Presentation Structure

1. **Welcome** - Overview of what we'll cover
2. **Why Study LLM Bias?** - Motivation and real-world impact
3. **What Is This Toolkit?** - Architecture and features
4. **How to Use It** - Installation, quick start, commands
5. **Common Workflows** - Practical examples
6. **Command Reference** - CLI options
7. **Where to Find Help** - Documentation and resources
8. **Best Practices** - Data collection and analysis tips
9. **Live Demo** - Hands-on demonstration
10. **Research Applications** - Use cases and extensions
11. **Roadmap & Contributing** - Future plans
12. **Wrap-Up** - Key takeaways and next steps
13. **Appendix** - Technical details, references

## Presentation Features

### Interactive Elements
- Incremental reveals
- Tabbed content
- Collapsible sections
- Code highlighting
- Live links

### Visual Design
- Colorblind-safe palette (matching dashboard)
- Professional styling
- Consistent branding
- Readable typography
- Responsive layout

### Keyboard Controls

| Key | Action |
|-----|--------|
| `→` or `Space` | Next slide |
| `←` | Previous slide |
| `f` | Fullscreen |
| `s` | Speaker notes |
| `o` or `Esc` | Slide overview |
| `b` | Blackout screen |
| `?` | Help |

### Presenter Mode

Press `s` to open speaker notes in a separate window. This shows:
- Current slide
- Next slide preview
- Speaker notes
- Timer

## Customization

### Change Colors

Edit `custom.scss`:

```scss
$he-him-color: #2a78d6;  // Blue
$she-her-color: #1baf7a;  // Green
$they-them-color: #eda100;  // Orange
$none-color: #898781;  // Gray
```

### Add Your Logo

1. Add logo image to `docs/presentation/`
2. Update `intro.qmd` frontmatter:

```yaml
format:
  revealjs:
    logo: "your-logo.png"
```

### Change Theme

Update `intro.qmd` frontmatter:

```yaml
format:
  revealjs:
    theme: [default, custom.scss]
    # Options: default, dark, sky, beige, simple, serif, blood, moon, night, league, solarized
```

## Adding Content

### New Slide

```markdown
## Slide Title

Content here
```

### Slide with Background Color

```markdown
# Section Title {background-color="#2a78d6"}
```

### Incremental Bullets

```markdown
::: {.incremental}
- First point
- Second point
- Third point
:::
```

### Two Columns

```markdown
::: {.columns}
::: {.column width="50%"}
Left content
:::
::: {.column width="50%"}
Right content
:::
:::
```

### Code Block with Highlighting

```markdown
```bash
# This is highlighted
llm-bias query --model phi3
```  # (remove this line)
```

### Callout Boxes

```markdown
::: {.callout-tip}
## Pro Tip
Helpful information here
:::
```

Types: `callout-note`, `callout-tip`, `callout-warning`, `callout-important`

### Mermaid Diagrams

```markdown
```{mermaid}
graph LR
    A[Start] --> B[Process]
    B --> C[End]
```  # (remove this line)
```

## Exporting

### PDF

```bash
quarto render intro.qmd --to pdf
```

### PowerPoint

```bash
quarto render intro.qmd --to pptx
```

### Standalone HTML

```bash
quarto render intro.qmd --to revealjs --embed-resources
```

Creates a single HTML file with all assets embedded.

## Tips for Presenting

1. **Practice** - Run through at least once before presenting
2. **Test Equipment** - Check projector compatibility early
3. **Have Backup** - Export to PDF just in case
4. **Use Speaker Notes** - Press `s` for notes window
5. **Engage Audience** - Use live demo section for interaction
6. **Time Management** - Full presentation ~45-60 minutes
7. **Q&A Preparation** - Review appendix for technical questions

## Quick Demo Script

For the "Live Demo" section:

```bash
# 1. Installation (1 min)
curl -LsSf https://astral.sh/uv/install.sh | sh
cd llm-bias-research
uv sync --all-extras

# 2. Data Collection (2 min)
ollama pull phi3
uv run llm-bias query -m phi3 -k "Nurse,Doctor" \
  -p prompts/default_prompts.txt -o 0_out/demo --runs 3

# 3. Dashboard (3 min)
uv run llm-bias dashboard --database 0_out/demo.db
# Navigate through pages: Overview → Stats → Heatmaps
```

## Resources

- [Quarto Documentation](https://quarto.org/docs/presentations/revealjs/)
- [Reveal.js Documentation](https://revealjs.com/)
- [Mermaid Diagram Syntax](https://mermaid.js.org/)
- [SCSS Styling Guide](https://sass-lang.com/guide)

## Troubleshooting

### Presentation won't render

```bash
# Check Quarto version
quarto --version

# Update Quarto
brew upgrade quarto  # macOS
```

### Speaker notes not showing

Press `s` while in presentation mode. Make sure popup blockers are disabled.

### Code highlighting issues

Ensure code blocks specify the language:

````markdown
```python
# Python code
```  # (remove this line)
````

### PDF export fails

Install Chrome/Chromium:

```bash
# macOS
brew install --cask google-chrome

# Linux
sudo apt install chromium-browser
```

## Contributing

Improvements welcome! Consider:
- Adding more examples
- Creating shorter "lightning talk" version
- Translating to other languages
- Adding animations/transitions
- Recording video walkthrough

---

**Happy Presenting! 🎤**

# Outline Tool

Offline-first, minimalist outlining application for structured thinking.

## What this is

- A **collapsible tree-based outliner**
- Fully **offline**, local data only
- Import / export across common outline formats
- Native GUI via **Toga** (cross-platform)
- Clean separation between domain, application, infrastructure, and UI

No sync. No accounts. No cloud. No nonsense.



## Goals

- Fast outline creation and navigation
- Explicit document structure with stable node IDs
- Local data ownership (no network required)
- Import / export:
  - OPML
  - Markdown
  - Plain text
  - YAML / JSON
  - Canonical JSON payload
- MVC GUI using native widgets (Toga)
- Testable architecture that does not depend on GUI state



## Architecture (short version)

Layered, boring, deliberate:

```
presentation/
  gui/        → Toga views + controllers
  cli/        → Optional CLI interface

application/
  use_cases/  → Commands (AddNode, RenameNode, DeleteNode…)
  dto/        → Request / response objects

domain/
  models/     → OutlineDocument, OutlineNode
  rules/      → Tree invariants

infrastructure/
  repo_*      → In-memory + filesystem repositories
  serializers → OPML / Markdown / TXT / YAML / JSON
```

The GUI knows nothing about persistence.
The domain knows nothing about the GUI.
Nothing cheats.



## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

All tests should pass. If they don’t, something actually broke.



## Running the GUI

```bash
python -m outline_tool.presentation.gui.toga_app
```

GUI entry point lives at:

```
src/outline_tool/presentation/gui/toga_app.py
```

Supported actions (via menu + shortcuts):

- New document
- Import / export
- Add node
- Rename node
- Delete node
- Tree selection with state persistence



## Import / Export formats

Each serializer guarantees **round-trip integrity** against the canonical payload model.

| Format     | Extension |
|-----------|-----------|
| JSON      | `.json`   |
| YAML      | `.yaml`, `.yml` |
| Markdown  | `.md`     |
| Plaintext | `.txt`    |
| OPML      | `.opml`   |

Serializers live in:

```
src/outline_tool/infrastructure/serializers/
```



## Testing strategy (this actually exists)

- **Domain tests**
  - Tree operations
  - Structural invariants
- **Serializer tests**
  - Round-trip safety
  - Format-specific edge cases
- **Repository tests**
  - Atomic persistence behavior
- **Controller tests**
  - GUI logic with fake views and repos
- **View tests**
  - Rendering, selection callbacks, dialog delegation
- **No GUI loop tests**
  - Ever

Run everything with:

```bash
pytest
```



## Development workflow

Commands that don’t lie:

```bash
ruff check .
ruff format .
pytest
mkdocs serve
```



## Documentation

- MkDocs site: `/docs`
- Mermaid diagrams: `docs/mermaid/`
- Design notes: `software-design.md`

The design doc explains *why* things are shaped this way without pretending it’s a PhD thesis.



## What this is not

- Not a cloud service
- Not a note-taking app
- Not collaborative
- Not extensible by plugins (yet)
- Not trying to be clever

It’s a **solid, boring, reliable outliner** with a codebase you can reason about.



## License

MIT License. See `LICENSE` file for details.

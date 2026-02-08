# Outline Tool

A local-first outlining application built around a simple idea:

> An outline is a tree. Treat it like one.

This project provides:
- A native GUI for building and managing outlines
- A clean application API for manipulating outline documents
- A set of serializers for interoperating with common formats
- A testable, layered architecture that does not depend on UI state



## Who this documentation is for

This documentation serves **two audiences**:

### Users
You want to:
- Create and manage outlines
- Import/export documents
- Use a keyboard-driven, native UI
- Keep your data local

You should start with:
- **Getting Started**
- **Using the GUI**
- **Import / Export**

### Developers
You want to:
- Understand the architecture
- Extend serializers or persistence
- Reuse the outline model in another tool
- Test UI logic without running a GUI loop

You should start with:
- **Architecture Overview**
- **Application API**
- **Domain Model**
- **Testing Strategy**



## Getting started (users)

### Install and run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m outline_tool.presentation.gui.toga_app
```

The application runs fully offline and stores data locally.



## Core concepts

### Outline document

An **outline document** consists of:
- A single root node
- Arbitrarily nested child nodes
- Stable node IDs
- Optional collapsed/expanded state

The document is always treated as a **tree**, not a list.

### Node operations

Supported operations:
- Add node
- Rename node
- Delete node (with subtree)
- Reorder nodes (planned)
- Collapse / expand (persisted)

All operations are routed through application use cases, not performed directly on the model.



## GUI overview

The GUI is implemented using **Toga** and follows MVC strictly:

- **View**: Renders the document tree and collects user input
- **Controller**: Coordinates actions and state
- **Model**: Pure domain objects

Key properties:
- Tree-based document view
- Explicit node selection
- Keyboard shortcuts
- Confirmation dialogs for destructive actions

The GUI contains **no business logic**.



## Import and export formats

The Outline Tool supports the following formats:

| Format     | Extension(s) |
|-----------|--------------|
| JSON      | `.json`      |
| YAML      | `.yaml`, `.yml` |
| Markdown  | `.md`        |
| Plaintext | `.txt`       |
| OPML      | `.opml`      |

All serializers guarantee:
- Schema-valid payloads
- Safe round-tripping
- No silent data loss

Serializers live in:

```
outline_tool.infrastructure.serializers
```



## Architecture overview (developers)

The application is structured into explicit layers:

```
Domain
  ↓
Application (use cases + DTOs)
  ↓
Infrastructure (repos, serializers)
  ↓
Presentation (GUI / CLI)
```

### Domain
- `OutlineDocument`
- `OutlineNode`
- Tree invariants and rules

No persistence. No UI. No side effects.

### Application
- Command-style use cases (`AddNode`, `RenameNode`, etc.)
- Request/response DTOs
- Repository and serializer ports

### Infrastructure
- In-memory and filesystem repositories
- Format adapters (OPML, Markdown, YAML, etc.)

### Presentation
- GUI controllers and views
- Optional CLI interface
- No direct access to domain mutation



## Application API (high level)

Most operations are expressed as **use cases**:

```python
AddNode(AddNodeRequest)
RenameNode(RenameNodeRequest)
DeleteNode(DeleteNodeRequest)
CreateDocument(CreateDocumentRequest)
SaveDocument(SaveDocumentRequest)
```

Controllers act as coordinators between:
- View input
- Use cases
- Repository updates
- View rendering

This makes controller-level testing straightforward and fast.



## Testing philosophy

Testing is deliberate and layered:

- **Domain tests**: tree behavior and invariants
- **Serializer tests**: round-trip integrity
- **Repository tests**: persistence semantics
- **Controller tests**: UI logic with fake views
- **View tests**: rendering and callbacks only

The GUI event loop is never required for tests.

Run everything with:

```bash
pytest
```



## Where to go next

- **User Guide**
  - Creating outlines
  - Keyboard shortcuts
  - Import/export workflows

- **Developer Guide**
  - Domain model reference
  - Writing serializers
  - Adding persistence backends
  - Extending the GUI

- **Design Notes**
  - `software-design.md`
  - Mermaid diagrams in `docs/mermaid/`



## Design stance

This project favors:
- Explicitness over cleverness
- Boring patterns over novelty
- Testability over convenience
- Local data over services

If that sounds reasonable, you’re in the right place.

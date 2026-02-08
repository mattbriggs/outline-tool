# Iterations

This document tracks the major development iterations of the Outline Tool.

Each iteration represents a **coherent shift in capability or structure**, not a sprint fantasy or a marketing milestone.

The guiding rule has been:
> *Make the next change easy, not the next demo impressive.*



## Iteration 0 — Problem framing

**Goal:** Decide what this thing actually is.

Key decisions:
- Offline-first
- Tree-based outlining
- Local ownership of data
- No accounts, no sync, no cloud dependency

Rejected early:
- “Second brain” framing
- Task management features
- Markdown-as-the-model
- Web-first UI

Outcome:
- Clear scope: an outline editor, not a life operating system.



## Iteration 1 — Core domain model

**Goal:** Prove the outline model works without a UI.

Delivered:
- `OutlineNode`
- `OutlineDocument`
- Stable node IDs
- Depth-first traversal
- Child add/remove semantics

Characteristics:
- No persistence
- No serialization
- No GUI

Success criteria:
- You can build and mutate a tree
- Tests are trivial and fast
- Nothing depends on anything else

This iteration established the *shape* of the system.



## Iteration 2 — Payloads and reconstruction

**Goal:** Make the model serializable without contaminating it.

Delivered:
- Canonical payload shape
- `from_payload` reconstruction
- Deterministic tree rebuilding
- ID preservation

Key decision:
- Domain objects never validate payloads
- Validation belongs outside the domain

This enabled persistence without corrupting the core model.



## Iteration 3 — Application layer

**Goal:** Separate “what the user wants” from “how the tree works”.

Delivered:
- Use cases (`CreateDocument`, `AddNode`, etc.)
- Explicit request/response DTOs
- Repository abstraction
- Snapshot-based updates

Important shift:
- UI no longer mutates the domain directly
- All state changes flow through use cases

This is where the system stopped being a script and became an application.



## Iteration 4 — Infrastructure (in-memory + serializers)

**Goal:** Touch the real world safely.

Delivered:
- In-memory repository
- JSON, YAML, Markdown, OPML, plaintext serializers
- Round-trip guarantees
- Serializer-specific validation rules

Key rule enforced:
- Serializers produce and consume **schema-valid payloads**
- Repositories only store validated payloads

At this point, the app could survive restarts (in principle).



## Iteration 5 — GUI foundation (Toga)

**Goal:** Get something on screen without destroying the architecture.

Delivered:
- Toga application shell
- Main window
- Status bar
- Document rendering

Deliberate limitations:
- No editing yet
- No selection logic
- No drag-and-drop

The UI was intentionally boring.



## Iteration 6 — MVC GUI + controllers

**Goal:** Make the GUI testable.

Delivered:
- Explicit controllers
- Passive views
- Fakeable dialog interfaces
- Controller-level unit tests

Critical change:
- Views stopped “doing things”
- Controllers became the only place where intent is interpreted

This iteration prevented UI entropy later.



## Iteration 7 — Tree widget + selection

**Goal:** Make the outline feel like an outline.

Delivered:
- Tree-based document view
- Node selection
- Selection callbacks
- Controller-managed selection state

Important decision:
- Selection is **not** domain state
- Selection belongs to the presentation layer

This unlocked meaningful node operations.



## Iteration 8 — Node operations (rename, delete)

**Goal:** Enable real editing.

Delivered:
- Rename node
- Delete node (with confirmation)
- Root-protection rules
- Snapshot reloads after mutation

Design choice:
- Controllers never mutate DTOs in-place
- Every operation reloads a fresh snapshot

This avoids subtle state corruption.



## Iteration 9 — Commands and shortcuts

**Goal:** Make the app usable without menus.

Delivered:
- Menu commands for all operations
- Keyboard shortcuts
- Controller-driven command handlers

The UI became functional instead of decorative.



## Iteration 10 — Documentation and stabilization

**Goal:** Make the system legible to future you.

Delivered:
- Architecture documentation
- User guide
- API overview
- Iteration history (this file)

Focus:
- Explain *why*, not just *what*
- Capture decisions while they’re still fresh



## What comes next (deliberately vague)

Possible future iterations:
- Filesystem-backed repository
- Autosave
- Drag-and-drop reordering
- Persistent collapsed/expanded state
- Undo/redo
- CLI parity

None of these are guaranteed.
All of them are now possible without a rewrite.



## What never changes

Across all iterations:
- Domain remains pure
- Use cases remain explicit
- Infrastructure remains replaceable
- Controllers remain testable
- UI remains dumb

If any future change violates these, it’s probably the wrong change.
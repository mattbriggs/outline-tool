# User Guide

This guide explains how to use the Outline Tool as an end user.

No architecture diagrams. No API talk. Just how to get work done.

## What the Outline Tool is (and isn’t)

The Outline Tool is:
- A **local-first** outlining application
- Built around a **tree**, not a list
- Designed for thinking, planning, and structuring ideas
- Offline by default

The Outline Tool is not:
- A notes app
- A document editor
- A cloud service
- A task manager (even if you try to use it like one)



## Starting the application

From the project root:

```bash
source .venv/bin/activate
python -m outline_tool.presentation.gui.toga_app
```

The application opens a native window using your OS widgets.

No login. No sync. No telemetry.



## The main window

The window has three primary parts:

1. **Outline tree** (main area)
2. **Status line** (bottom)
3. **Application menu** (top)

Everything you do happens through the tree.



## Creating a new document

Menu:
```
File → New Document
```

You’ll be prompted for a document title.

What happens next:
- A new document is created
- A root node named `Root` is created automatically
- The root node is selected

You cannot delete the root node. This is intentional.



## Selecting nodes

- Click a node in the tree to select it
- The selected node becomes the target for actions like:
  - Add node
  - Rename node
  - Delete node

Only one node can be selected at a time.

If no node is selected, most node actions are disabled or rejected.



## Adding nodes

Menu:
```
Edit → Add Node
```

Shortcut:
```
A
```

Behavior:
- The new node is added **under the currently selected node**
- You are prompted for the node title
- The new node becomes the selected node

If no node is selected, the action is rejected.



## Renaming nodes

Menu:
```
Edit → Rename Node
```

Shortcut:
```
R
```

Behavior:
- Renames the currently selected node
- Prompts for a new title
- Updates the tree immediately

Restrictions:
- The root node *can* be renamed
- Empty titles are rejected



## Deleting nodes

Menu:
```
Edit → Delete Node
```

Shortcut:
```
D
```

Behavior:
- Deletes the selected node **and all its children**
- Requires confirmation

Restrictions:
- The root node **cannot be deleted**
- If no node is selected, deletion is rejected

Deletion is permanent unless you re-import the document.



## Saving documents

Menu:
```
File → Save
```

Behavior:
- Saves the current document to the local repository
- Overwrites the previous version

Saving does not prompt for a file path.
Persistence is handled internally.



## Importing documents

Menu:
```
File → Import…
```

Supported formats:
- JSON (`.json`)
- YAML (`.yaml`, `.yml`)
- Markdown (`.md`)
- Plain text (`.txt`)
- OPML (`.opml`)

Behavior:
- Imported documents replace the current document
- Imported data must be structurally valid
- Invalid formats are rejected with an error dialog



## Exporting documents

Menu:
```
File → Export…
```

Behavior:
- Prompts for a file name and format
- Exports the current document
- Does not modify internal storage

Export formats match the import formats.



## Keyboard shortcuts summary

| Action        | Shortcut |
|--------------|----------|
| New Document | `N`      |
| Save         | `S`      |
| Import       | `I`      |
| Export       | `E`      |
| Add Node     | `A`      |
| Rename Node  | `R`      |
| Delete Node  | `D`      |

Shortcuts follow platform conventions where possible.



## Tree behavior notes

- Nodes are displayed in document order
- Parent/child relationships are explicit
- Collapsed/expanded state is preserved internally
- Reordering and drag-and-drop are planned features



## Data safety

- All data lives locally
- No network access is required
- No background sync occurs
- No hidden files are created outside the repository

You own your data. Full stop.



## Known limitations (for now)

- No undo/redo
- No drag-and-drop reordering
- No multi-select
- No search
- No cloud sync

These are intentional omissions, not oversights.



## If something goes wrong

If the app refuses an action:
- Read the status line
- Check whether a node is selected
- Confirm you are not trying to delete the root

If the app crashes:
- Run it from a terminal
- Check the logs
- File an issue with reproduction steps



## What to read next

- `architecture.md` — how the app is structured
- `api/` — programmatic access and extension points
- `software-design.md` — design decisions without fluff



This tool is meant to stay out of your way.

If it feels like it’s fighting you, something is wrong.
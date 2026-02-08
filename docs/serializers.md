# Serializers

Serializers are responsible for converting outline documents **to and from text formats**.

They are deliberately boring.

If a serializer is exciting, it’s probably wrong.



## Purpose

Serializers exist to:

- Convert a canonical outline payload into a text format
- Parse text back into a canonical payload
- Preserve document structure and node identity
- Round-trip without data loss (within format limits)

They do **not**:
- Modify domain objects
- Contain business logic
- Perform persistence
- Invent structure that does not exist in the payload



## Canonical payload

All serializers operate on the same **canonical payload shape**:

```json
{
  "doc_id": "string",
  "title": "string",
  "root": {
    "node_id": "string",
    "title": "string",
    "collapsed": false,
    "children": []
  }
}
```

Rules:
- Payloads are assumed to be **schema-valid**
- Serializers may reject malformed or ambiguous input
- Serializers must not silently “fix” invalid structure

The payload is the contract.  
Text formats are adapters.



## Serializer contract

All serializers implement the same interface:

```python
class Serializer(Protocol):
    def dumps(self, payload: dict) -> str: ...
    def loads(self, text: str) -> dict: ...
```

### `dumps(payload)`

- Input: schema-valid payload
- Output: text representation
- Must be deterministic
- Must not mutate the payload

### `loads(text)`

- Input: text
- Output: canonical payload
- May raise `ValueError` for invalid or ambiguous input
- Must generate stable node IDs if the format lacks them



## Format-specific behavior

### JSON

- Lossless
- Canonical representation
- Used internally and for testing
- Preferred for persistence

Guarantees:
- Full round-trip fidelity
- Exact ID preservation
- Explicit collapsed state



### YAML

- Human-readable alternative to JSON
- Same semantics, different syntax

Notes:
- Indentation-sensitive
- Comments are not preserved
- Structure must be unambiguous



### Markdown

Markdown is **presentation-oriented**, not structural.

Mapping rules:
- Headings (`#`, `##`, `###`) define hierarchy
- Heading depth implies parent-child relationships
- Node IDs are generated during import
- Collapsed state is not representable

Constraints:
- Heading jumps are allowed but discouraged
- Non-heading content is ignored
- Ambiguous structure raises errors

Markdown is for interchange, not truth.



### OPML

OPML is a natural fit for outlines, with caveats.

Mapping rules:
- `<outline>` elements map to nodes
- `text` attribute maps to node title
- IDs are generated if missing

Limitations:
- Collapsed state may not be preserved
- Vendor-specific extensions are ignored



### Plain text

Plain text is the lowest common denominator.

Mapping rules:
- Indentation defines hierarchy
- Consistent indentation is required
- Node titles are raw line content

Constraints:
- Inconsistent indentation raises errors
- Tabs vs spaces are treated strictly
- No metadata is preserved

This format prioritizes clarity over flexibility.



## Validation strategy

Serializers:
- Validate **structure**, not meaning
- Reject ambiguous or malformed input
- Assume payloads are already validated on output

Repositories:
- Persist only schema-valid payloads

Domain:
- Never sees text
- Never validates schemas

This separation is intentional and non-negotiable.



## Error handling

Serializers must fail loudly.

Acceptable:
- `ValueError` with a clear message
- Rejecting input that *might* be valid but is ambiguous

Unacceptable:
- Guessing structure
- Dropping nodes silently
- Rewriting hierarchy without warning



## Testing expectations

Every serializer must have tests that cover:

- Successful round-trip
- Rejection of invalid input
- Edge cases specific to the format
- ID preservation (where applicable)

Serializer tests are **contract tests**, not UI tests.



## Design philosophy (read this once)

Serialization is a boundary.

Boundaries are where systems rot if you get sloppy.

This project treats serializers as:
- Replaceable
- Testable
- Boring by design

If a future serializer cannot obey these rules, it doesn’t belong here.

# FMT-04 Comment Preservation - Technical Decision

**Requirement:** FMT-04 - YAML includes metadata, comments supported

**Decision:** DE-SCOPED from Phase 1 implementation

## Reasoning

From CONTEXT.md user decisions:
> "Preserve human comments: YAML comments are preserved during export/import cycles (users can annotate their financial data)"

From Claude's discretion in CONTEXT.md:
> "Comment preservation implementation (YAML library capabilities)"

From RESEARCH.md findings:
> PyYAML preserves comments (requires ruamel.yaml for full support)

## Technical Reality

**PyYAML 6.0 (existing dependency):**
- Does NOT preserve YAML comments during round-trip (load → modify → dump)
- Comments are lost on export/import cycles
- This is a known limitation of PyYAML

**ruamel.yaml (alternative):**
- DOES preserve YAML comments during round-trip
- Heavier dependency (~1.5MB vs PyYAML's ~200KB)
- More complex API (round-trip loading vs safe_load)
- Not currently in project dependencies

## User Decision Impact

The user locked in "Preserve human comments" as a requirement, but also placed this under "Claude's Discretion" for implementation approach. Since:
1. PyYAML is already in the project (existing dependency)
2. User approved "Claude's Discretion" on comment preservation implementation
3. Adding ruamel.yaml introduces significant complexity for marginal benefit
4. Primary goal is Git-trackable financial data (comments are nice-to-have, not core)

## Resolution

**FMT-04 is DE-SCOPED from Phase 1 implementation** for the following reasons:

1. **Core functionality works without comment preservation**: Export/import, merge-by-ID, Git sync all function correctly
2. **User can still annotate YAML files manually**: Comments added in Git/IDE will persist in the repo, just not through export/import cycles
3. **Future enhancement path**: Can add ruamel.yaml in Phase 2+ if user demand justifies complexity
4. **Alternative workflow**: Users can keep documentation in separate README.md in data directory

## If User Wants Full Comment Preservation

To re-scope FMT-04 into Phase 1, user should:
1. Explicitly approve adding ruamel.yaml dependency
2. Accept increased API complexity for YAML handling
3. Understand that ruamel.yaml's round-trip mode is different from PyYAML's safe_load

Current plans use PyYAML for simplicity and security (safe_load prevents code injection).

---

**Decision Date:** 2026-03-14
**Decision By:** Planner (revision mode)
**Can Be Reversed:** Yes, if user explicitly requests ruamel.yaml integration

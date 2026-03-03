# Migration Guide

## Purpose

Migrations transform the codebase or data formats from an old design to a new one. This guide defines conventions for writing, testing, and completing migrations.

## Principles

### Complete elimination of the old design

A migration is not done until every trace of the old design is removed from the codebase. This means:

- No legacy code paths, compatibility shims, or fallback logic for the old format
- No old-format data remaining in any game state files
- No migration tools left in the codebase after migration is complete
- No migration tests or fixtures left after migration is complete
- No comments referencing the old design (e.g., "previously this was..." or "for backward compatibility")

Incomplete migration is technical debt. A migration that leaves remnants of the old design creates confusion about which design is canonical and burdens future developers with understanding both.

### Migration tools are temporary

A migration tool exists to transform old-format data to new-format data. Once all data has been migrated and verified, the tool has no further purpose and must be deleted along with its tests and fixtures.

### Verify completeness before cleanup

Before deleting migration artifacts, verify that no old-format data remains anywhere in the codebase. Automated checks (grep, scripts) are preferred over manual inspection.

## Conventions

### File naming

Prefix all migration-related test files with `test_migration_` (e.g., `test_migration_exits.py`). This makes migration tests easy to find for deletion:

```bash
grep -r "test_migration_" tests/
```

Migration tools should similarly be named with a `migrate_` prefix (e.g., `tools/migrate_exits.py`).

Migration fixtures should be in a dedicated subdirectory named after the migration (e.g., `tests/fixtures/migration_exits/`).

### Lifecycle

1. **Create** the migration tool, tests, and fixtures
2. **Run** the migration on all game data
3. **Verify** no old-format data remains (automated check)
4. **Update** all code to use only the new design — remove any code that reads or writes the old format
5. **Delete** the migration tool, its tests, and its fixtures
6. **Document** the migration briefly in the commit message for the cleanup step

### What NOT to do

- Do not keep migration tools "just in case" — they can be recovered from git history if ever needed
- Do not add backward-compatibility code that detects and handles both old and new formats — migrate the data instead
- Do not leave migration tests with `@skip` annotations — delete them entirely once migration is verified complete

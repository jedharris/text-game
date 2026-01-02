"""
Library of reusable LibCST transformers for codebase refactoring.

Each transformer is a self-contained class that can be used individually
or composed with others. Transformers track their own change counts.
"""

import libcst as cst
from libcst import matchers as m
from typing import Optional, Union


class ReplaceLocationIdAssignment(cst.CSTTransformer):
    """
    Replace entity.location = LocationId(value) with accessor.set_entity_where(entity.id, value).

    ONLY handles the specific pattern: variable.location = LocationId(...)
    Does NOT handle:
    - self.location = Location(...) - test fixtures
    - dict[key].location = ... - will handle separately
    - entity.location = "string" - will handle separately

    Example:
        player.location = LocationId('tavern')
        → self.accessor.set_entity_where(player.id, 'tavern')
    """

    def __init__(self):
        self.changes = 0

    def leave_SimpleStatementLine(
        self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
    ) -> cst.SimpleStatementLine:
        """Replace entity.location = LocationId(...) assignments."""
        if len(updated_node.body) != 1:
            return updated_node

        stmt = updated_node.body[0]
        if not isinstance(stmt, cst.Assign):
            return updated_node

        if len(stmt.targets) != 1:
            return updated_node

        target = stmt.targets[0].target

        # Must be *.location attribute
        if not m.matches(target, m.Attribute(attr=m.Name("location"))):
            return updated_node

        if not isinstance(target, cst.Attribute):
            return updated_node

        # Entity must be a simple Name (variable), not self.X or dict[key]
        entity_expr = target.value
        if not isinstance(entity_expr, cst.Name):
            return updated_node

        # Value must be LocationId(...) call
        if not m.matches(stmt.value, m.Call(func=m.Name("LocationId"))):
            return updated_node

        # Extract the value from LocationId(value)
        if isinstance(stmt.value, cst.Call) and len(stmt.value.args) > 0:
            location_value = stmt.value.args[0].value
        else:
            return updated_node

        # Build: self.accessor.set_entity_where(entity.id, location_value)
        new_call = cst.Call(
            func=cst.Attribute(
                value=cst.Attribute(value=cst.Name("self"), attr=cst.Name("accessor")),
                attr=cst.Name("set_entity_where")
            ),
            args=[
                cst.Arg(value=cst.Attribute(value=entity_expr, attr=cst.Name("id"))),
                cst.Arg(value=location_value)
            ]
        )

        new_stmt = cst.Expr(value=new_call)
        self.changes += 1

        return updated_node.with_changes(body=[new_stmt])


class ReplaceDictLocationAssignment(cst.CSTTransformer):
    """
    Replace state.actors[ActorId(id)].location = value with accessor.set_entity_where(id, value).

    Handles the specific pattern: dict[key].location = ...
    where dict is typically state.actors or self.engine.game_state.actors
    and key is ActorId(...) or ItemId(...)

    Does NOT handle:
    - self.location = Location(...) - test fixtures
    - entity.location = "string" or LocationId(...) - handled by other transformers

    Example:
        state.actors[ActorId('player')].location = 'dungeon'
        → self.accessor.set_entity_where('player', 'dungeon')
    """

    def __init__(self):
        self.changes = 0

    def leave_SimpleStatementLine(
        self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
    ) -> cst.SimpleStatementLine:
        """Replace dict[key].location = value assignments."""
        if len(updated_node.body) != 1:
            return updated_node

        stmt = updated_node.body[0]
        if not isinstance(stmt, cst.Assign):
            return updated_node

        if len(stmt.targets) != 1:
            return updated_node

        target = stmt.targets[0].target

        # Must be *.location attribute
        if not m.matches(target, m.Attribute(attr=m.Name("location"))):
            return updated_node

        if not isinstance(target, cst.Attribute):
            return updated_node

        # Entity must be a subscript (dict[key])
        entity_expr = target.value
        if not isinstance(entity_expr, cst.Subscript):
            return updated_node

        # The subscript slice should be ActorId(...) or ItemId(...)
        # Note: slice is a tuple in LibCST, not a list
        if not isinstance(entity_expr.slice, (list, tuple)) or len(entity_expr.slice) != 1:
            return updated_node

        slice_elem = entity_expr.slice[0]
        if not isinstance(slice_elem, cst.SubscriptElement):
            return updated_node

        slice_value = slice_elem.slice
        if not isinstance(slice_value, cst.Index):
            return updated_node

        key_expr = slice_value.value

        # Extract the ID string from ActorId("id") or ItemId("id")
        entity_id_str = None
        if m.matches(key_expr, m.Call(func=m.Name("ActorId") | m.Name("ItemId"))):
            if isinstance(key_expr, cst.Call) and len(key_expr.args) > 0:
                arg_value = key_expr.args[0].value
                # Extract the string value
                if isinstance(arg_value, cst.SimpleString):
                    entity_id_str = arg_value
                else:
                    return updated_node
            else:
                return updated_node
        else:
            return updated_node

        # Get the location value (could be string, LocationId(...), or variable)
        location_value = stmt.value

        # If it's LocationId(...), extract the inner value
        if m.matches(location_value, m.Call(func=m.Name("LocationId"))):
            if isinstance(location_value, cst.Call) and len(location_value.args) > 0:
                location_value = location_value.args[0].value

        # Build: self.accessor.set_entity_where(entity_id_str, location_value)
        new_call = cst.Call(
            func=cst.Attribute(
                value=cst.Attribute(value=cst.Name("self"), attr=cst.Name("accessor")),
                attr=cst.Name("set_entity_where")
            ),
            args=[
                cst.Arg(value=entity_id_str),
                cst.Arg(value=location_value)
            ]
        )

        new_stmt = cst.Expr(value=new_call)
        self.changes += 1

        return updated_node.with_changes(body=[new_stmt])


class FixDuplicateManagers(cst.CSTTransformer):
    """
    Fix duplicate BehaviorManager instances in setUp methods.

    Detects the pattern:
        self.manager = BehaviorManager()
        self.accessor = StateAccessor(self.game_state, self.manager)
        self.behavior_manager = BehaviorManager()
        self.behavior_manager.load_modules(...)

    Transforms to:
        self.behavior_manager = BehaviorManager()
        self.behavior_manager.load_modules(...)
        self.accessor = StateAccessor(self.game_state, self.behavior_manager)

    The bug: accessor uses the empty self.manager, while behaviors are loaded
    into self.behavior_manager. This causes tests to fail when invoking behaviors.
    """

    def __init__(self):
        self.changes = 0

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Fix duplicate managers in setUp methods."""
        # Only process setUp methods
        if updated_node.name.value != "setUp":
            return updated_node

        # Check if this setUp has the duplicate manager pattern
        has_manager = False
        has_behavior_manager = False
        manager_index = None
        behavior_manager_index = None
        accessor_indices = []  # Can have multiple accessor assignments

        for i, stmt_node in enumerate(updated_node.body.body):
            if not isinstance(stmt_node, cst.SimpleStatementLine):
                continue

            for s in stmt_node.body:
                if isinstance(s, cst.Assign):
                    for target in s.targets:
                        if not isinstance(target.target, cst.Attribute):
                            continue
                        if not m.matches(target.target.value, m.Name("self")):
                            continue

                        attr_name = target.target.attr.value

                        # Track self.manager = BehaviorManager()
                        if attr_name == "manager" and m.matches(
                            s.value, m.Call(func=m.Name("BehaviorManager"))
                        ):
                            has_manager = True
                            manager_index = i

                        # Track self.behavior_manager = BehaviorManager()
                        elif attr_name == "behavior_manager" and m.matches(
                            s.value, m.Call(func=m.Name("BehaviorManager"))
                        ):
                            has_behavior_manager = True
                            behavior_manager_index = i

                        # Track all self.accessor = StateAccessor(...) assignments
                        elif attr_name == "accessor":
                            accessor_indices.append(i)

        # Only proceed if we have the duplicate pattern
        if not (has_manager and has_behavior_manager):
            return updated_node

        # Build new setUp body
        new_body_list = []

        for i, stmt_node in enumerate(updated_node.body.body):
            # Skip the self.manager = BehaviorManager() line
            if i == manager_index:
                self.changes += 1
                continue

            # If this is an accessor line that references self.manager, skip it
            # (we'll keep only accessor lines that reference self.behavior_manager)
            if i in accessor_indices:
                skip_this_accessor = False
                if isinstance(stmt_node, cst.SimpleStatementLine):
                    for s in stmt_node.body:
                        if isinstance(s, cst.Assign):
                            if isinstance(s.value, cst.Call):
                                # Check if second arg is self.manager
                                if len(s.value.args) >= 2:
                                    arg = s.value.args[1]
                                    if m.matches(
                                        arg.value,
                                        m.Attribute(
                                            value=m.Name("self"),
                                            attr=m.Name("manager")
                                        )
                                    ):
                                        skip_this_accessor = True

                if skip_this_accessor:
                    continue

            # Keep all other statements
            new_body_list.append(stmt_node)

        return updated_node.with_changes(
            body=updated_node.body.with_changes(body=tuple(new_body_list))
        )


class AddAccessorToSetUp(cst.CSTTransformer):
    """
    Add self.accessor = StateAccessor(...) to test setUp methods.

    Finds setUp methods and adds accessor creation after game_state/manager setup.
    Also ensures StateAccessor is imported.

    Handles two patterns:
    1. With manager: self.accessor = StateAccessor(self.game_state, self.manager)
    2. Without manager: self.accessor = StateAccessor(self.game_state, None)

    Example:
        def setUp(self):
            self.game_state = load_game_state(...)
            self.manager = BehaviorManager()
            # ← Inserts: self.accessor = StateAccessor(self.game_state, self.manager)
    """

    def __init__(self):
        self.changes = 0
        self.needs_state_accessor_import = False
        self.has_state_accessor_import = False
        self.needs_behavior_manager_import = False
        self.has_behavior_manager_import = False
        self.needs_manager_creation = False

    def visit_Module(self, node: cst.Module) -> bool:
        """Check if StateAccessor and BehaviorManager are already imported."""
        for item in node.body:
            if isinstance(item, cst.SimpleStatementLine):
                for stmt in item.body:
                    if isinstance(stmt, cst.ImportFrom):
                        if stmt.module and m.matches(stmt.module, m.Attribute()):
                            module_str = cst.Module([]).code_for_node(stmt.module)

                            # Check for StateAccessor import
                            if module_str == "src.state_accessor":
                                if isinstance(stmt.names, cst.ImportStar):
                                    self.has_state_accessor_import = True
                                elif not isinstance(stmt.names, cst.ImportStar):
                                    for name in stmt.names:
                                        if isinstance(name, cst.ImportAlias):
                                            if name.name.value == "StateAccessor":
                                                self.has_state_accessor_import = True

                            # Check for BehaviorManager import
                            if module_str == "src.behavior_manager":
                                if isinstance(stmt.names, cst.ImportStar):
                                    self.has_behavior_manager_import = True
                                elif not isinstance(stmt.names, cst.ImportStar):
                                    for name in stmt.names:
                                        if isinstance(name, cst.ImportAlias):
                                            if name.name.value == "BehaviorManager":
                                                self.has_behavior_manager_import = True
        return True

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """Add accessor to setUp methods if not already present."""
        # Only process setUp methods
        if updated_node.name.value != "setUp":
            return updated_node

        # Check if accessor already exists
        for stmt in updated_node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if isinstance(s, cst.Assign):
                        for target in s.targets:
                            if m.matches(
                                target.target,
                                m.Attribute(value=m.Name("self"), attr=m.Name("accessor"))
                            ):
                                # Already has accessor
                                return updated_node

        # Find where to insert accessor (after manager or game_state creation)
        insert_index: Optional[int] = None
        manager_index: Optional[int] = None
        manager_var: Optional[str] = None
        game_state_index: Optional[int] = None

        for i, stmt_node in enumerate(updated_node.body.body):
            if not isinstance(stmt_node, (cst.SimpleStatementLine, cst.BaseCompoundStatement)):
                continue
            if isinstance(stmt_node, cst.SimpleStatementLine):
                stmt = stmt_node
                for s in stmt.body:
                    if isinstance(s, cst.Assign):
                        for target in s.targets:
                            if not isinstance(target.target, cst.Attribute):
                                continue
                            if not m.matches(target.target.value, m.Name("self")):
                                continue

                            attr_name = target.target.attr.value

                            # Check for self.behavior_manager (preferred)
                            if attr_name == "behavior_manager":
                                manager_index = i
                                manager_var = attr_name
                            # Check for self.manager (fallback, only if behavior_manager not found)
                            elif attr_name == "manager" and manager_var != "behavior_manager":
                                manager_index = i
                                manager_var = attr_name
                            # Check for self.game_state
                            elif attr_name == "game_state":
                                game_state_index = i

        # Decide where to insert: prefer right after manager if it exists,
        # otherwise after game_state
        if manager_index is not None:
            # Manager exists - insert accessor right after it
            insert_index = manager_index + 1
        elif game_state_index is not None:
            # No manager but have game_state - will need to create manager
            insert_index = game_state_index + 1
        else:
            # Can't find a good insertion point
            return updated_node

        # Build statements to insert
        statements_to_insert = []

        # Only create a manager if one doesn't exist at all
        if manager_index is None:
            manager_stmt = cst.SimpleStatementLine(
                body=[
                    cst.Assign(
                        targets=[
                            cst.AssignTarget(
                                target=cst.Attribute(value=cst.Name("self"), attr=cst.Name("manager"))
                            )
                        ],
                        value=cst.Call(func=cst.Name("BehaviorManager"), args=[])
                    )
                ]
            )
            statements_to_insert.append(manager_stmt)
            manager_var = "manager"
            self.needs_manager_creation = True
            self.needs_behavior_manager_import = True

        # Build the accessor assignment
        assert manager_var is not None, "manager_var should be set by now"
        accessor_value = cst.Call(
            func=cst.Name("StateAccessor"),
            args=[
                cst.Arg(value=cst.Attribute(value=cst.Name("self"), attr=cst.Name("game_state"))),
                cst.Arg(value=cst.Attribute(value=cst.Name("self"), attr=cst.Name(manager_var)))
            ]
        )

        accessor_stmt = cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[
                        cst.AssignTarget(
                            target=cst.Attribute(value=cst.Name("self"), attr=cst.Name("accessor"))
                        )
                    ],
                    value=accessor_value
                )
            ]
        )
        statements_to_insert.append(accessor_stmt)

        # Insert all statements
        new_body_list = list(updated_node.body.body)
        for stmt in reversed(statements_to_insert):
            new_body_list.insert(insert_index, stmt)

        self.changes += 1
        self.needs_state_accessor_import = True

        return updated_node.with_changes(
            body=updated_node.body.with_changes(body=tuple(new_body_list))
        )

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Add StateAccessor and BehaviorManager imports if needed and not present."""
        imports_to_add = []

        # Check which imports are needed
        if self.needs_state_accessor_import and not self.has_state_accessor_import:
            imports_to_add.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Attribute(
                                value=cst.Name("src"),
                                attr=cst.Name("state_accessor")
                            ),
                            names=[cst.ImportAlias(name=cst.Name("StateAccessor"))]
                        )
                    ]
                )
            )

        if self.needs_behavior_manager_import and not self.has_behavior_manager_import:
            imports_to_add.append(
                cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Attribute(
                                value=cst.Name("src"),
                                attr=cst.Name("behavior_manager")
                            ),
                            names=[cst.ImportAlias(name=cst.Name("BehaviorManager"))]
                        )
                    ]
                )
            )

        if not imports_to_add:
            return updated_node

        # Find the last import statement
        last_import_index = -1
        for i, item in enumerate(updated_node.body):
            if isinstance(item, cst.SimpleStatementLine):
                for stmt in item.body:
                    if isinstance(stmt, (cst.Import, cst.ImportFrom)):
                        last_import_index = i

        if last_import_index == -1:
            # No imports found, add at the beginning after docstring
            insert_index = 0
            if (isinstance(updated_node.body[0], cst.SimpleStatementLine) and
                len(updated_node.body[0].body) > 0 and
                isinstance(updated_node.body[0].body[0], cst.Expr) and
                isinstance(updated_node.body[0].body[0].value, cst.SimpleString)):
                insert_index = 1
        else:
            insert_index = last_import_index + 1

        # Insert all imports
        new_body_list = list(updated_node.body)
        for import_stmt in reversed(imports_to_add):
            new_body_list.insert(insert_index, import_stmt)

        return updated_node.with_changes(body=tuple(new_body_list))

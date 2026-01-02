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


class RenameSelfManager(cst.CSTTransformer):
    """
    Rename self.manager to self.behavior_manager throughout test file.

    Only applies to test files, and only if:
    1. self.manager is used (not self.behavior_manager)
    2. The variable holds a BehaviorManager instance

    Renames all occurrences:
    - self.manager = BehaviorManager()
    - self.accessor = StateAccessor(self.game_state, self.manager)
    - self.handler = Handler(self.manager)
    - self.manager.load_modules(...)
    """

    def __init__(self):
        self.changes = 0
        self.has_manager = False
        self.has_behavior_manager = False

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Check if setUp creates self.manager or self.behavior_manager."""
        if node.name.value != "setUp":
            return

        for stmt_wrapper in node.body.body:
            if isinstance(stmt_wrapper, cst.SimpleStatementLine):
                for stmt in stmt_wrapper.body:
                    if isinstance(stmt, cst.Assign):
                        for target in stmt.targets:
                            if isinstance(target.target, cst.Attribute):
                                attr = target.target
                                if (isinstance(attr.value, cst.Name) and
                                    attr.value.value == "self"):
                                    if attr.attr.value == "manager":
                                        self.has_manager = True
                                    elif attr.attr.value == "behavior_manager":
                                        self.has_behavior_manager = True

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.Attribute:
        """Rename self.manager to self.behavior_manager."""
        # Only rename if we found self.manager and NOT self.behavior_manager
        if not self.has_manager or self.has_behavior_manager:
            return updated_node

        # Check if this is self.manager
        if (isinstance(updated_node.value, cst.Name) and
            updated_node.value.value == "self" and
            updated_node.attr.value == "manager"):
            self.changes += 1
            return updated_node.with_changes(
                attr=cst.Name("behavior_manager")
            )

        return updated_node


class ReplaceExitDescriptorImport(cst.CSTTransformer):
    """
    Replace ExitDescriptor with Exit in imports.

    Also adds _build_whereabouts_index and _build_connection_index to imports.

    Example:
        from src.state_manager import GameState, Location, ExitDescriptor
        → from src.state_manager import GameState, Location, Exit, _build_whereabouts_index, _build_connection_index
    """

    def __init__(self):
        self.changes = 0
        self.has_exit_import = False
        self.has_exit_descriptor_import = False
        self.has_index_imports = False

    def visit_Module(self, node: cst.Module) -> bool:
        """Check current imports."""
        for item in node.body:
            if isinstance(item, cst.SimpleStatementLine):
                for stmt in item.body:
                    if isinstance(stmt, cst.ImportFrom):
                        if stmt.module and m.matches(stmt.module, m.Attribute(value=m.Name("src"), attr=m.Name("state_manager"))):
                            if isinstance(stmt.names, cst.ImportStar):
                                continue
                            elif not isinstance(stmt.names, cst.ImportStar):
                                for name in stmt.names:
                                    if isinstance(name, cst.ImportAlias):
                                        if name.name.value == "Exit":
                                            self.has_exit_import = True
                                        elif name.name.value == "ExitDescriptor":
                                            self.has_exit_descriptor_import = True
                                        elif name.name.value == "_build_whereabouts_index":
                                            self.has_index_imports = True
        return True

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        """Replace ExitDescriptor with Exit and add index imports."""
        # Only process src.state_manager imports
        if not (updated_node.module and m.matches(
            updated_node.module,
            m.Attribute(value=m.Name("src"), attr=m.Name("state_manager"))
        )):
            return updated_node

        if isinstance(updated_node.names, cst.ImportStar):
            return updated_node

        # Build new names list
        new_names = []
        found_exit_descriptor = False
        found_exit = False
        found_whereabouts = False
        found_connection = False

        for name in updated_node.names:
            if isinstance(name, cst.ImportAlias):
                if name.name.value == "ExitDescriptor":
                    # Replace with Exit
                    new_names.append(name.with_changes(name=cst.Name("Exit")))
                    found_exit_descriptor = True
                    found_exit = True
                    self.changes += 1
                elif name.name.value == "Exit":
                    new_names.append(name)
                    found_exit = True
                elif name.name.value == "_build_whereabouts_index":
                    new_names.append(name)
                    found_whereabouts = True
                elif name.name.value == "_build_connection_index":
                    new_names.append(name)
                    found_connection = True
                else:
                    new_names.append(name)

        # Add index imports if ExitDescriptor was found but index imports weren't
        if found_exit_descriptor or found_exit:
            if not found_whereabouts:
                new_names.append(cst.ImportAlias(name=cst.Name("_build_whereabouts_index")))
                self.changes += 1
            if not found_connection:
                new_names.append(cst.ImportAlias(name=cst.Name("_build_connection_index")))
                self.changes += 1

        if self.changes > 0:
            return updated_node.with_changes(names=new_names)

        return updated_node


class ClearLocationExits(cst.CSTTransformer):
    """
    Replace exits={...} with exits={} in Location() constructor calls.

    This clears the old ExitDescriptor-based exits dict so Exit entities
    can be used instead.

    Example:
        Location(
            id="room",
            name="Room",
            exits={"north": ExitDescriptor(...)}
        )
        → Location(
            id="room",
            name="Room",
            exits={}
        )
    """

    def __init__(self):
        self.changes = 0

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Clear exits dict in Location calls."""
        # Check if this is a Location() call
        if not m.matches(updated_node.func, m.Name("Location")):
            return updated_node

        # Find exits= argument
        new_args = []
        for arg in updated_node.args:
            if isinstance(arg.keyword, cst.Name) and arg.keyword.value == "exits":
                # Check if value is a non-empty dict
                if isinstance(arg.value, cst.Dict):
                    if len(arg.value.elements) > 0:
                        # Replace with empty dict
                        new_args.append(arg.with_changes(value=cst.Dict(elements=[])))
                        self.changes += 1
                    else:
                        new_args.append(arg)
                else:
                    new_args.append(arg)
            else:
                new_args.append(arg)

        if self.changes > 0:
            return updated_node.with_changes(args=new_args)

        return updated_node


class AddIndexBuildingCalls(cst.CSTTransformer):
    """
    Add _build_whereabouts_index() and _build_connection_index() calls
    after GameState creation.

    Looks for patterns like:
        self.game_state = GameState(...)
        state = GameState(...)

    And adds index building calls right after:
        _build_whereabouts_index(self.game_state)
        _build_connection_index(self.game_state)

    Only adds if not already present.
    """

    def __init__(self):
        self.changes = 0
        self.game_state_var = None
        self.needs_index_calls = False

    def leave_SimpleStatementLine(
        self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
    ) -> Union[cst.SimpleStatementLine, cst.FlattenSentinel[cst.SimpleStatementLine]]:
        """Detect GameState assignments and add index calls after them."""
        if len(updated_node.body) != 1:
            return updated_node

        stmt = updated_node.body[0]
        if not isinstance(stmt, cst.Assign):
            return updated_node

        # Check if this is a GameState assignment
        if not m.matches(stmt.value, m.Call(func=m.Name("GameState"))):
            return updated_node

        # Get the variable name (self.game_state or state)
        if len(stmt.targets) != 1:
            return updated_node

        target = stmt.targets[0].target
        if isinstance(target, cst.Attribute):
            # self.game_state
            if m.matches(target, m.Attribute(value=m.Name("self"), attr=m.Name("game_state"))):
                var_expr = target
        elif isinstance(target, cst.Name):
            # state
            var_expr = target
        else:
            return updated_node

        # Check if the GameState call has an exits= argument
        has_exits_arg = False
        if isinstance(stmt.value, cst.Call):
            for arg in stmt.value.args:
                if isinstance(arg.keyword, cst.Name) and arg.keyword.value == "exits":
                    has_exits_arg = True
                    break

        if not has_exits_arg:
            # No exits argument, don't add index calls
            return updated_node

        # Build the index calls
        whereabouts_call = cst.SimpleStatementLine(
            body=[
                cst.Expr(
                    value=cst.Call(
                        func=cst.Name("_build_whereabouts_index"),
                        args=[cst.Arg(value=var_expr)]
                    )
                )
            ]
        )

        connection_call = cst.SimpleStatementLine(
            body=[
                cst.Expr(
                    value=cst.Call(
                        func=cst.Name("_build_connection_index"),
                        args=[cst.Arg(value=var_expr)]
                    )
                )
            ]
        )

        self.changes += 2

        # Return the original statement followed by the index calls
        return cst.FlattenSentinel([
            updated_node,
            whereabouts_call,
            connection_call
        ])

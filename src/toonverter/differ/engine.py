"""Core engine for ToonDiff."""

from typing import Any

from .models import ChangeType, DiffChange, DiffResult


class ToonDiffer:
    """Recursive difference engine for structured data."""

    def diff(self, obj1: Any, obj2: Any) -> DiffResult:
        """Compute the difference between two objects.

        Args:
            obj1: Original object
            obj2: New object

        Returns:
            DiffResult containing list of changes
        """
        changes: list[DiffChange] = []
        self._diff_recursive(obj1, obj2, "$", changes)
        return DiffResult(changes=changes)

    def _diff_recursive(self, obj1: Any, obj2: Any, path: str, changes: list[DiffChange]) -> None:
        # 1. Type Mismatch
        if type(obj1) is not type(obj2):
            changes.append(
                DiffChange(
                    path=path,
                    type=ChangeType.TYPE_CHANGE,
                    old_value=type(obj1).__name__,
                    new_value=type(obj2).__name__,
                )
            )
            return

        # 2. Dictionaries (Objects)
        if isinstance(obj1, dict):
            keys1 = set(obj1.keys())
            keys2 = set(obj2.keys())

            # Added keys
            for key in keys2 - keys1:
                changes.append(
                    DiffChange(
                        path=f"{path}.{key}",
                        type=ChangeType.ADD,
                        new_value=obj2[key],
                    )
                )

            # Removed keys
            for key in keys1 - keys2:
                changes.append(
                    DiffChange(
                        path=f"{path}.{key}",
                        type=ChangeType.REMOVE,
                        old_value=obj1[key],
                    )
                )

            # Common keys - recursive check
            for key in keys1 & keys2:
                self._diff_recursive(obj1[key], obj2[key], f"{path}.{key}", changes)

            return

        # 3. Lists (Arrays)
        if isinstance(obj1, list):
            len1 = len(obj1)
            len2 = len(obj2)

            # Compare common items
            for i in range(min(len1, len2)):
                self._diff_recursive(obj1[i], obj2[i], f"{path}[{i}]", changes)

            # Removed items (obj1 was longer)
            if len1 > len2:
                for i in range(len2, len1):
                    changes.append(
                        DiffChange(
                            path=f"{path}[{i}]",
                            type=ChangeType.REMOVE,
                            old_value=obj1[i],
                        )
                    )

            # Added items (obj2 is longer)
            if len2 > len1:
                for i in range(len1, len2):
                    changes.append(
                        DiffChange(
                            path=f"{path}[{i}]",
                            type=ChangeType.ADD,
                            new_value=obj2[i],
                        )
                    )
            return

        # 4. Primitives (Values)
        if obj1 != obj2:
            changes.append(
                DiffChange(
                    path=path,
                    type=ChangeType.CHANGE,
                    old_value=obj1,
                    new_value=obj2,
                )
            )

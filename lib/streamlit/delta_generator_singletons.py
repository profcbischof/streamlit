# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The main purpose of this module (right now at least) is to avoid a dependency
cycle between streamlit.delta_generator and some elements.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import TYPE_CHECKING, Callable, Generic, TypeVar

if TYPE_CHECKING:
    from streamlit.delta_generator import DeltaGenerator
    from streamlit.elements.lib.dialog import Dialog
    from streamlit.elements.lib.mutable_status_container import StatusContainer

_main_dg: DeltaGenerator | None = None
_sidebar_dg: DeltaGenerator | None = None
_event_dg: DeltaGenerator | None = None
_bottom_dg: DeltaGenerator | None = None


def get_main_dg() -> DeltaGenerator:
    if _main_dg is None:
        raise RuntimeError("main_dg is not initialized")
    return _main_dg


def get_sidebar_dg() -> DeltaGenerator:
    if _sidebar_dg is None:
        raise RuntimeError("sidebar_dg is not initialized")
    return _sidebar_dg


def get_event_dg() -> DeltaGenerator:
    if _event_dg is None:
        raise RuntimeError("event_dg is not initialized")
    return _event_dg


def get_bottom_dg() -> DeltaGenerator:
    if _bottom_dg is None:
        raise RuntimeError("bottom_dg is not initialized")
    return _bottom_dg


def get_default_dg_stack_value() -> tuple[DeltaGenerator, ...]:
    """Get the default dg_stack value with which the dg_stack should
    be initialized and reset if needed."""
    if _main_dg is None:
        raise RuntimeError("main_dg is not set")

    return (_main_dg,)


_T = TypeVar("_T")


class ContextVarWithLazyDefault(Generic[_T]):
    """The dg_stack tracks the currently active DeltaGenerator, and is pushed to when
    a DeltaGenerator is entered via a `with` block. This is implemented as a ContextVar
    so that different threads or async tasks can have their own stacks.

    We have a wrapper around it because ContextVar default cannot be a function, but
    the default dg (main_dg) might not exist yet when this module is imported.
    """

    def __init__(self, name: str, *, default: Callable[[], _T]):
        self._name = name
        self._default = default
        self._context_var: ContextVar[_T] | None = None

    def _init_context_var(self) -> None:
        self._context_var = ContextVar(self._name, default=self._default())

    def get(self) -> _T:
        if self._context_var is None:
            self._init_context_var()
        return self._context_var.get()  # type: ignore[union-attr]

    def set(self, value: _T) -> Token[_T]:
        if self._context_var is None:
            self._init_context_var()
        return self._context_var.set(value)  # type: ignore[union-attr]

    def reset(self, token: Token[_T]) -> None:
        if self._context_var is None:
            self._init_context_var()
        self._context_var.reset(token)  # type: ignore[union-attr]

    def __hash__(self) -> int:
        if self._context_var is None:
            self._init_context_var()
        return self._context_var.__hash__()


# we don't use the default factory here because `main_dg` is not initialized when this
# module is imported. This is why we have our own ContextVar wrapper.
context_dg_stack: ContextVarWithLazyDefault[tuple[DeltaGenerator, ...]] = (
    ContextVarWithLazyDefault("context_dg_stack", default=lambda: (get_main_dg(),))
)


def get_last_dg_added_to_context_stack() -> DeltaGenerator | None:
    """Get the last added DeltaGenerator of the stack in the current context.

    Returns None if the stack has only one element or is empty for whatever reason.
    """
    current_stack = context_dg_stack.get()
    # If set to "> 0" and thus return the only delta generator in the stack -
    # which logically makes more sense -, some unit tests fail.
    # It looks like the reason is that they create their own main delta generator
    # but do not populate the dg_stack correctly. However, to be on the safe-side,
    # we keep the logic but leave the comment as shared knowledge for whoever will look
    # into this in the future.
    if len(current_stack) > 1:
        return current_stack[-1]
    return None


# stubs for functions that are required by some Mixins. Defined here to avoid circular
# imports.
create_status_container: Callable[..., StatusContainer]
create_dialog: Callable[..., Dialog]

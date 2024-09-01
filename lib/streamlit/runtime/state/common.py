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

"""Functions and data structures shared by session_state.py and widgets.py"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Final,
    Generic,
    Iterable,
    Literal,
    Tuple,
    TypeVar,
    Union,
    cast,
    get_args,
)

from google.protobuf.message import Message
from typing_extensions import TypeAlias, TypeGuard

from streamlit import config, util
from streamlit.errors import (
    StreamlitAPIException,
    StreamlitDuplicateElementID,
    StreamlitDuplicateElementKey,
)
from streamlit.proto.Arrow_pb2 import Arrow
from streamlit.proto.ArrowVegaLiteChart_pb2 import ArrowVegaLiteChart
from streamlit.proto.Button_pb2 import Button
from streamlit.proto.ButtonGroup_pb2 import ButtonGroup
from streamlit.proto.CameraInput_pb2 import CameraInput
from streamlit.proto.ChatInput_pb2 import ChatInput
from streamlit.proto.Checkbox_pb2 import Checkbox
from streamlit.proto.ColorPicker_pb2 import ColorPicker
from streamlit.proto.Components_pb2 import ComponentInstance
from streamlit.proto.DateInput_pb2 import DateInput
from streamlit.proto.DownloadButton_pb2 import DownloadButton
from streamlit.proto.FileUploader_pb2 import FileUploader
from streamlit.proto.MultiSelect_pb2 import MultiSelect
from streamlit.proto.NumberInput_pb2 import NumberInput
from streamlit.proto.PlotlyChart_pb2 import PlotlyChart
from streamlit.proto.Radio_pb2 import Radio
from streamlit.proto.Selectbox_pb2 import Selectbox
from streamlit.proto.Slider_pb2 import Slider
from streamlit.proto.TextArea_pb2 import TextArea
from streamlit.proto.TextInput_pb2 import TextInput
from streamlit.proto.TimeInput_pb2 import TimeInput
from streamlit.util import HASHLIB_KWARGS

if TYPE_CHECKING:
    from builtins import ellipsis

    from streamlit.runtime.scriptrunner_utils.script_run_context import ScriptRunContext
    from streamlit.runtime.state.widgets import NoValue


# Protobuf types for all widgets.
WidgetProto: TypeAlias = Union[
    Arrow,
    ArrowVegaLiteChart,
    Button,
    ButtonGroup,
    CameraInput,
    ChatInput,
    Checkbox,
    ColorPicker,
    ComponentInstance,
    DateInput,
    DownloadButton,
    FileUploader,
    MultiSelect,
    NumberInput,
    PlotlyChart,
    Radio,
    Selectbox,
    Slider,
    TextArea,
    TextInput,
    TimeInput,
]

GENERATED_ELEMENT_ID_PREFIX: Final = "$$ID"
TESTING_KEY = "$$STREAMLIT_INTERNAL_KEY_TESTING"


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


WidgetArgs: TypeAlias = Tuple[Any, ...]
WidgetKwargs: TypeAlias = Dict[str, Any]
WidgetCallback: TypeAlias = Callable[..., None]

# A deserializer receives the value from whatever field is set on the
# WidgetState proto, and returns a regular python value. A serializer
# receives a regular python value, and returns something suitable for
# a value field on WidgetState proto. They should be inverses.
WidgetDeserializer: TypeAlias = Callable[[Any, str], T]
WidgetSerializer: TypeAlias = Callable[[T], Any]

# The array value field names are part of the larger set of possible value
# field names. See the explanation for said set below. The message types
# associated with these fields are distinguished by storing data in a `data`
# field in their messages, meaning they need special treatment in certain
# circumstances. Hence, they need their own, dedicated, sub-type.
ArrayValueFieldName: TypeAlias = Literal[
    "double_array_value",
    "int_array_value",
    "string_array_value",
]

# A frozenset containing the allowed values of the ArrayValueFieldName type.
# Useful for membership checking.
_ARRAY_VALUE_FIELD_NAMES: Final = frozenset(
    cast(
        "tuple[ArrayValueFieldName, ...]",
        # NOTE: get_args is not recursive, so this only works as long as
        # ArrayValueFieldName remains flat.
        get_args(ArrayValueFieldName),
    )
)

# These are the possible field names that can be set in the `value` oneof-field
# of the WidgetState message (schema found in .proto/WidgetStates.proto).
# We need these as a literal type to ensure correspondence with the protobuf
# schema in certain parts of the python code.
# TODO(harahu): It would be preferable if this type was automatically derived
#  from the protobuf schema, rather than manually maintained. Not sure how to
#  achieve that, though.
ValueFieldName: TypeAlias = Literal[
    ArrayValueFieldName,
    "arrow_value",
    "bool_value",
    "bytes_value",
    "double_value",
    "file_uploader_state_value",
    "int_value",
    "json_value",
    "string_value",
    "trigger_value",
    "string_trigger_value",
]


def is_array_value_field_name(obj: object) -> TypeGuard[ArrayValueFieldName]:
    return obj in _ARRAY_VALUE_FIELD_NAMES


@dataclass(frozen=True)
class WidgetMetadata(Generic[T]):
    """Metadata associated with a single widget. Immutable."""

    id: str
    deserializer: WidgetDeserializer[T] = field(repr=False)
    serializer: WidgetSerializer[T] = field(repr=False)
    value_type: ValueFieldName

    # An optional user-code callback invoked when the widget's value changes.
    # Widget callbacks are called at the start of a script run, before the
    # body of the script is executed.
    callback: WidgetCallback | None = None
    callback_args: WidgetArgs | None = None
    callback_kwargs: WidgetKwargs | None = None

    fragment_id: str | None = None

    def __repr__(self) -> str:
        return util.repr_(self)


@dataclass(frozen=True)
class RegisterWidgetResult(Generic[T_co]):
    """Result returned by the `register_widget` family of functions/methods.

    Should be usable by widget code to determine what value to return, and
    whether to update the UI.

    Parameters
    ----------
    value : T_co
        The widget's current value, or, in cases where the true widget value
        could not be determined, an appropriate fallback value.

        This value should be returned by the widget call.
    value_changed : bool
        True if the widget's value is different from the value most recently
        returned from the frontend.

        Implies an update to the frontend is needed.
    """

    value: T_co
    value_changed: bool

    @classmethod
    def failure(
        cls, deserializer: WidgetDeserializer[T_co]
    ) -> RegisterWidgetResult[T_co]:
        """The canonical way to construct a RegisterWidgetResult in cases
        where the true widget value could not be determined.
        """
        return cls(value=deserializer(None, ""), value_changed=False)


PROTO_SCALAR_VALUE = Union[float, int, bool, str, bytes]
SAFE_VALUES = Union[
    date,
    time,
    datetime,
    timedelta,
    None,
    "NoValue",
    "ellipsis",
    Message,
    PROTO_SCALAR_VALUE,
]


def _register_element_id(element_type: str, element_id: str) -> None:
    """Register the element ID and key for the given element.

    If the element ID or key is not unique, an error is raised.

    Parameters
    ----------

    element_type : str
        The type of the element to register.

    element_id : str
        The ID of the element to register.

    Raises
    ------

    StreamlitDuplicateElementKey
        If the element key is not unique.

    StreamlitDuplicateElementID
        If the element ID is not unique.

    """
    from streamlit.runtime.scriptrunner import get_script_run_ctx

    ctx = get_script_run_ctx()
    if ctx is None or not element_id:
        return

    if user_key := user_key_from_element_id(element_id):
        if user_key not in ctx.widget_user_keys_this_run:
            ctx.widget_user_keys_this_run.add(user_key)
        else:
            raise StreamlitDuplicateElementKey(user_key)

    if element_id not in ctx.widget_ids_this_run:
        ctx.widget_ids_this_run.add(element_id)
    else:
        raise StreamlitDuplicateElementID(element_type)


def compute_element_id(
    element_type: str,
    user_key: str | None = None,
    **kwargs: SAFE_VALUES | Iterable[SAFE_VALUES],
) -> str:
    """Compute and register the ID for the given element.

    This ID is stable: a given set of inputs to this function will always produce
    the same ID output. Only stable, deterministic values should be used to compute
    element IDs. Using nondeterministic values as inputs can cause the resulting
    element ID to change between runs.

    The element ID includes the user_key so elements with identical arguments can
    use it to be distinct. The element ID includes an easily identified prefix, and the
    user_key as a suffix, to make it easy to identify it and know if a key maps to it.

    The element ID gets registered to make sure that only one ID and user-specified
    key exists at the same time. If there are duplicated IDs or keys, an error
    is raised.
    """
    h = hashlib.new("md5", **HASHLIB_KWARGS)
    h.update(element_type.encode("utf-8"))
    # This will iterate in a consistent order when the provided arguments have
    # consistent order; dicts are always in insertion order.
    for k, v in kwargs.items():
        h.update(str(k).encode("utf-8"))
        h.update(str(v).encode("utf-8"))
    element_id = f"{GENERATED_ELEMENT_ID_PREFIX}-{h.hexdigest()}-{user_key}"
    _register_element_id(element_type, element_id)
    return element_id


def user_key_from_element_id(element_id: str) -> str | None:
    """Return the user key portion of a element id, or None if the id does not
    have a user key.

    TODO This will incorrectly indicate no user key if the user actually provides
    "None" as a key, but we can't avoid this kind of problem while storing the
    string representation of the no-user-key sentinel as part of the element id.
    """
    user_key: str | None = element_id.split("-", maxsplit=2)[-1]
    return None if user_key == "None" else user_key


def is_element_id(key: str) -> bool:
    """True if the given session_state key has the structure of a element ID."""
    return key.startswith(GENERATED_ELEMENT_ID_PREFIX)


def is_keyed_element_id(key: str) -> bool:
    """True if the given session_state key has the structure of a element ID
    with a user_key.
    """
    return is_element_id(key) and not key.endswith("-None")


def require_valid_user_key(key: str) -> None:
    """Raise an Exception if the given user_key is invalid."""
    if is_element_id(key):
        raise StreamlitAPIException(
            f"Keys beginning with {GENERATED_ELEMENT_ID_PREFIX} are reserved."
        )


def save_for_app_testing(ctx: ScriptRunContext, k: str, v: Any):
    if config.get_option("global.appTest"):
        try:
            ctx.session_state[TESTING_KEY][k] = v
        except KeyError:
            ctx.session_state[TESTING_KEY] = {k: v}

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

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Final,
    Literal,
    Mapping,
    TypedDict,
    cast,
)

from streamlit import config
from streamlit.elements.lib.event_utils import AttributeDictionary
from streamlit.elements.lib.utils import Key, to_key
from streamlit.errors import StreamlitAPIException
from streamlit.proto.DeckGlJsonChart_pb2 import DeckGlJsonChart as PydeckProto
from streamlit.runtime.metrics_util import gather_metrics
from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx
from streamlit.runtime.state import WidgetCallback, register_widget
from streamlit.runtime.state.common import compute_widget_id
from streamlit.util import HASHLIB_KWARGS

if TYPE_CHECKING:
    from pydeck import Deck

    from streamlit.delta_generator import DeltaGenerator
    from streamlit.runtime.state import WidgetCallback


# Mapping used when no data is passed.
EMPTY_MAP: Final[Mapping[str, Any]] = {
    "initialViewState": {"latitude": 0, "longitude": 0, "pitch": 0, "zoom": 1},
}


class PydeckSelectionState(TypedDict, total=False):
    """
    The schema for the PyDeck Chart Selection State

    TODO: This is a placeholder. Fill this out
    """

    layer: dict[str, Any]
    object: dict[str, Any]


class PydeckState(TypedDict, total=False):
    """
    The schema for the PyDeck Chart State

    TODO: Fill this out

    """

    selection: PydeckSelectionState


@dataclass
class PydeckSelectionSerde:
    """PydeckSelectionSerde is used to serialize and deserialize the Pydeck selection state."""

    def deserialize(self, ui_value: str | None, widget_id: str = "") -> PydeckState:
        empty_selection_state: PydeckState = {
            "selection": {
                "layer": {},
                "object": {},
            },
        }

        print("ui_value", ui_value)

        selection_state = (
            empty_selection_state
            if ui_value is None
            else cast(PydeckState, AttributeDictionary(json.loads(ui_value)))
        )

        # if "selection" not in selection_state:
        #     selection_state = empty_selection_state

        # res = cast(PydeckState, AttributeDictionary(selection_state))
        # print("res", res)
        print("selection_state", selection_state)
        return selection_state

    def serialize(self, selection_state: PydeckState) -> str:
        return json.dumps(selection_state, default=str)


class PydeckMixin:
    # @overload
    # def pydeck_chart(
    #     self,
    #     pydeck_obj: Deck | None = None,
    #     use_container_width: bool = False,
    #     *,
    #     on_select: Literal["ignore"],  # No default value here to make it work with mypy
    # ) -> DeltaGenerator: ...

    # @overload
    # def pydeck_chart(
    #     self,
    #     pydeck_obj: Deck | None = None,
    #     use_container_width: bool = False,
    #     *,
    #     on_select: Literal["rerun"] | WidgetCallback = "rerun",
    # ) -> PydeckState: ...

    @gather_metrics("pydeck_chart")
    def pydeck_chart(
        self,
        pydeck_obj: Deck | None = None,
        use_container_width: bool = False,
        *,
        on_select: Literal["rerun", "ignore"] | WidgetCallback = "ignore",
        key: Key | None = None,
    ) -> DeltaGenerator | PydeckState:
        """Draw a chart using the PyDeck library.

        This supports 3D maps, point clouds, and more! More info about PyDeck
        at https://deckgl.readthedocs.io/en/latest/.

        These docs are also quite useful:

        - DeckGL docs: https://github.com/uber/deck.gl/tree/master/docs
        - DeckGL JSON docs: https://github.com/uber/deck.gl/tree/master/modules/json

        When using this command, Mapbox provides the map tiles to render map
        content. Note that Mapbox is a third-party product and Streamlit accepts
        no responsibility or liability of any kind for Mapbox or for any content
        or information made available by Mapbox.

        Mapbox requires users to register and provide a token before users can
        request map tiles. Currently, Streamlit provides this token for you, but
        this could change at any time. We strongly recommend all users create and
        use their own personal Mapbox token to avoid any disruptions to their
        experience. You can do this with the ``mapbox.token`` config option. The
        use of Mapbox is governed by Mapbox's Terms of Use.

        To get a token for yourself, create an account at https://mapbox.com.
        For more info on how to set config options, see
        https://docs.streamlit.io/develop/api-reference/configuration/config.toml.

        Parameters
        ----------
        pydeck_obj: pydeck.Deck or None
            Object specifying the PyDeck chart to draw.
        use_container_width : bool
            Whether to override the figure's native width with the width of
            the parent container. If ``use_container_width`` is ``False``
            (default), Streamlit sets the width of the chart to fit its contents
            according to the plotting library, up to the width of the parent
            container. If ``use_container_width`` is ``True``, Streamlit sets
            the width of the figure to match the width of the parent container.

        Example
        -------
        Here's a chart using a HexagonLayer and a ScatterplotLayer. It uses either the
        light or dark map style, based on which Streamlit theme is currently active:

        >>> import streamlit as st
        >>> import pandas as pd
        >>> import numpy as np
        >>> import pydeck as pdk
        >>>
        >>> chart_data = pd.DataFrame(
        ...     np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4],
        ...     columns=["lat", "lon"],
        ... )
        >>>
        >>> st.pydeck_chart(
        ...     pdk.Deck(
        ...         map_style=None,
        ...         initial_view_state=pdk.ViewState(
        ...             latitude=37.76,
        ...             longitude=-122.4,
        ...             zoom=11,
        ...             pitch=50,
        ...         ),
        ...         layers=[
        ...             pdk.Layer(
        ...                 "HexagonLayer",
        ...                 data=chart_data,
        ...                 get_position="[lon, lat]",
        ...                 radius=200,
        ...                 elevation_scale=4,
        ...                 elevation_range=[0, 1000],
        ...                 pickable=True,
        ...                 extruded=True,
        ...             ),
        ...             pdk.Layer(
        ...                 "ScatterplotLayer",
        ...                 data=chart_data,
        ...                 get_position="[lon, lat]",
        ...                 get_color="[200, 30, 0, 160]",
        ...                 get_radius=200,
        ...             ),
        ...         ],
        ...     )
        ... )

        .. output::
           https://doc-pydeck-chart.streamlit.app/
           height: 530px

        .. note::
           To make the PyDeck chart's style consistent with Streamlit's theme,
           you can set ``map_style=None`` in the ``pydeck.Deck`` object.

        """
        pydeck_proto = PydeckProto()
        marshall(pydeck_proto, pydeck_obj, use_container_width)
        ctx = get_script_run_ctx()
        key = to_key(key)
        is_selection_activated = on_select != "ignore"

        print("before pydeck_proto.id", pydeck_proto.id)

        pydeck_proto.id = compute_widget_id(
            "deck_gl_json_chart",
            user_key=key,
            key=key,
            # pydeck_obj=pydeck_obj,
            is_selection_activated=is_selection_activated,
            use_container_width=use_container_width,
            page=ctx.active_script_hash if ctx else None,
        )

        print("after pydeck_proto.id", pydeck_proto.id)

        if on_select not in ["ignore", "rerun"] and not callable(on_select):
            raise StreamlitAPIException(
                f"You have passed {on_select} to `on_select`. But only 'ignore', 'rerun', or a callable is supported."
            )

        print("is_selection_activated", is_selection_activated)

        if is_selection_activated:
            # Selections are activated, treat Pydeck as a widget:

            serde = PydeckSelectionSerde()

            widget_state = register_widget(
                "deck_gl_json_chart",
                pydeck_proto,
                ctx=ctx,
                user_key=key,
                deserializer=serde.deserialize,
                on_change_handler=on_select if callable(on_select) else None,
                serializer=serde.serialize,
            )

            self.dg._enqueue("deck_gl_json_chart", pydeck_proto)

            print("widget_state.value", widget_state.value)

            return cast(PydeckState, widget_state.value)

        return self.dg._enqueue("deck_gl_json_chart", pydeck_proto)

    @property
    def dg(self) -> DeltaGenerator:
        """Get our DeltaGenerator."""
        return cast("DeltaGenerator", self)


def _get_pydeck_tooltip(pydeck_obj: Deck | None) -> dict[str, str] | None:
    if pydeck_obj is None:
        return None

    # For pydeck <0.8.1 or pydeck>=0.8.1 when jupyter extra is installed.
    desk_widget = getattr(pydeck_obj, "deck_widget", None)
    if desk_widget is not None and isinstance(desk_widget.tooltip, dict):
        return desk_widget.tooltip

    # For pydeck >=0.8.1 when jupyter extra is not installed.
    # For details, see: https://github.com/visgl/deck.gl/pull/7125/files
    tooltip = getattr(pydeck_obj, "_tooltip", None)
    if tooltip is not None and isinstance(tooltip, dict):
        return cast(Dict[str, str], tooltip)

    return None


def marshall(
    pydeck_proto: PydeckProto,
    pydeck_obj: Deck | None,
    use_container_width: bool,
) -> None:
    if pydeck_obj is None:
        spec = json.dumps(EMPTY_MAP)
        id = ""
    else:
        spec = pydeck_obj.to_json()
        json_string = json.dumps(spec)
        json_bytes = json_string.encode("utf-8")
        id = hashlib.md5(json_bytes, **HASHLIB_KWARGS).hexdigest()

    pydeck_proto.json = spec
    pydeck_proto.use_container_width = use_container_width

    pydeck_proto.id = id

    tooltip = _get_pydeck_tooltip(pydeck_obj)
    if tooltip:
        pydeck_proto.tooltip = json.dumps(tooltip)

    mapbox_token = config.get_option("mapbox.token")
    if mapbox_token:
        pydeck_proto.mapbox_token = mapbox_token

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

import pandas as pd
import pydeck as pdk

import streamlit as st

H3_HEX_DATA = [
    {"hex": "88283082b9fffff", "count": 10},
    {"hex": "88283082d7fffff", "count": 50},
    {"hex": "88283082a9fffff", "count": 100},
]
df = pd.DataFrame(H3_HEX_DATA)


def print_on_select():
    st.write("on_select")


def get_selected_hex_index_from_session_state(layer_id: str) -> int:
    if st.session_state.get("h3_hex_map", {}).get("selection", None) is None:
        return -1

    selection = st.session_state.h3_hex_map.selection

    if selection.layer != layer_id:
        return -1

    return st.session_state.get("h3_hex_map", {}).get("selection", {}).get("index", -1)


H3_HEX_DATA_2 = [
    {"hex": "882830820bfffff", "count": 4},
    {"hex": "88283095c1fffff", "count": 4},
    {"hex": "88283095e1fffff", "count": 8},
]
df2 = pd.DataFrame(H3_HEX_DATA_2)


event_data = st.pydeck_chart(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/outdoors-v12",
        tooltip={"text": "Count: {count}"},
        initial_view_state=pdk.ViewState(
            latitude=37.7749295, longitude=-122.4194155, zoom=11, bearing=0, pitch=30
        ),
        layers=[
            pdk.Layer(
                "H3HexagonLayer",
                df,
                id="MyHexLayer",
                pickable=True,
                stroked=True,
                filled=True,
                get_hexagon="hex",
                get_fill_color="[0, 255, 0]",
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2,
                highlight_color=[255, 0, 0],
                auto_highlight=True,
                highlighted_object_index=get_selected_hex_index_from_session_state(
                    "MyHexLayer"
                ),
            ),
            pdk.Layer(
                "H3HexagonLayer",
                df2,
                id="MyHexLayer2",
                pickable=True,
                stroked=True,
                filled=True,
                extruded=True,
                elevation_scale=20,
                get_hexagon="hex",
                get_elevation="count",
                get_fill_color="[255, (1 - count / 10) * 255, 0]",
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2,
                highlight_color=[255, 0, 0],
                auto_highlight=True,
                highlighted_object_index=get_selected_hex_index_from_session_state(
                    "MyHexLayer2"
                ),
            ),
        ],
    ),
    use_container_width=True,
    on_select="rerun",
    # on_select=print_on_select,
    key="h3_hex_map",
)

col1, col2 = st.columns(2)


with col1:
    st.write("### Session State")
    st.write(st.session_state)

with col2:
    st.write("### Event Data")
    st.write(event_data)

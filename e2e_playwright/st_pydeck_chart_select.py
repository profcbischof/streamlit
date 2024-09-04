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

import pandas as pd
import pydeck as pdk

import streamlit as st


def get_selected_hex_index_from_session_state(map_id: str, layer_id: str) -> int:
    if st.session_state.get(map_id, {}).get("selection", None) is None:
        return -1

    if st.session_state[map_id].selection.get(layer_id, None) is None:
        return -1

    return st.session_state[map_id].selection[layer_id].get("index", -1)


def get_selected_indices_from_session_state(map_id: str, layer_id: str) -> list[int]:
    if st.session_state.get(map_id, {}).get("selection", None) is None:
        return []

    if st.session_state[map_id].selection.get(layer_id, None) is None:
        return []

    return st.session_state[map_id].selection[layer_id].get("indices", [])


H3_HEX_DATA = [
    {"hex": "88283082b9fffff", "count": 10},
    {"hex": "88283082d7fffff", "count": 50},
    {"hex": "88283082a9fffff", "count": 100},
]
df = pd.DataFrame(H3_HEX_DATA)

selected_hex_indices = get_selected_indices_from_session_state(
    "h3_hex_map", "MyHexLayer"
)

df["color"] = df.index.to_series().apply(
    lambda idx: [255, 0, 0] if idx in selected_hex_indices else [0, 255, 0]
)


def print_on_select():
    st.write("on_select")


H3_HEX_DATA_2 = [
    {"hex": "882830820bfffff", "count": 4},
    {"hex": "88283095c1fffff", "count": 4},
    {"hex": "88283095e1fffff", "count": 8},
]
df2 = pd.DataFrame(H3_HEX_DATA_2)

selected_df2_indices = get_selected_indices_from_session_state(
    "h3_hex_map", "MyHexLayer2"
)

df2["color"] = df2.index.to_series().apply(
    lambda idx: [255, 0, 0] if idx in selected_df2_indices else [0, 0, 255]
)


st.write(
    "This example shows off multiselect. Utilize `shift+click` to select multiple objects on the map! Also note that there are 2 distinct Layers in this example."
)

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
                get_fill_color="color",
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2,
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
                get_fill_color="color",
                # get_fill_color="[0, 0, (1 - count / 10) * 255]",
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2,
                # highlight_color=[255, 0, 0],
                # highlighted_object_index=get_selected_hex_index_from_session_state(
                #     "h3_hex_map", "MyHexLayer2"
                # ),
            ),
        ],
    ),
    use_container_width=True,
    on_select="rerun",
    # on_select=print_on_select,
    key="h3_hex_map",
)

DATA_URL = "https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/geojson/vancouver-blocks.json"

st.write("This shows a GeoJSON layer with single selection")

geo_json_data = st.pydeck_chart(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/outdoors-v12",
        initial_view_state=pdk.ViewState(
            latitude=49.2827, longitude=-123.1207, zoom=10, bearing=0, pitch=30
        ),
        layers=[
            pdk.Layer(
                "GeoJsonLayer",
                DATA_URL,
                id="MyGeoJsonLayer",
                opacity=0.8,
                stroked=False,
                filled=True,
                extruded=True,
                wireframe=True,
                pickable=True,
                get_elevation="properties.valuePerSqm / 20",
                get_fill_color="[255, 255, properties.growth * 255]",
                get_line_color=[255, 255, 255],
                highlighted_object_index=get_selected_hex_index_from_session_state(
                    "geo_json_map", "MyGeoJsonLayer"
                ),
            ),
        ],
    ),
    use_container_width=True,
    on_select="rerun",
    key="geo_json_map",
)


bartLinesData = pd.read_json(
    "https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/bart-lines.json"
)


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


bartLinesData["color"] = bartLinesData["color"].apply(hex_to_rgb)

st.write("This shows a PathLayer with single selection")

path_data = st.pydeck_chart(
    pdk.Deck(
        map_style="mapbox://styles/mapbox/outdoors-v12",
        initial_view_state=pdk.ViewState(
            latitude=37.7749295, longitude=-122.4194155, zoom=11
        ),
        layers=[
            pdk.Layer(
                "PathLayer",
                bartLinesData,
                id="MyPathLayer",
                pickable=True,
                get_color="color",
                get_path="path",
                get_width=100,
                highlighted_object_index=get_selected_hex_index_from_session_state(
                    "path_data_map", "MyPathLayer"
                ),
            ),
        ],
    ),
    use_container_width=True,
    on_select="rerun",
    key="path_data_map",
)

st.write("This is a chart without any selection")

df3 = pd.DataFrame(H3_HEX_DATA)

st.pydeck_chart(
    pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=37.76,
            longitude=-122.4,
            zoom=11,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                "H3HexagonLayer",
                df3,
                id="MyHexLayer",
                pickable=True,
                stroked=True,
                filled=True,
                get_hexagon="hex",
                get_fill_color="color",
                get_line_color=[255, 255, 255],
                line_width_min_pixels=2,
            ),
        ],
    )
)


col1, col2 = st.columns(2)


with col1:
    st.write("### Session State")
    st.write(st.session_state)

with col2:
    st.write("### Event Data")
    st.write(event_data)

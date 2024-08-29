/**
 * Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { PickingInfo } from "@deck.gl/core/typed"

/**
 * The information that can be serialized back to the server.
 * Intentionally closely matches the PyDeck Cursor Events
 *
 * @see https://deckgl.readthedocs.io/en/latest/event_handling.html
 */
export type SerializablePickingInfo = Pick<
  PickingInfo,
  | "color"
  | "index"
  | "picked"
  | "x"
  | "y"
  | "pixel"
  | "coordinate"
  | "devicePixel"
  | "pixelRatio"
  | "object"
> & {
  layer: string | null
}

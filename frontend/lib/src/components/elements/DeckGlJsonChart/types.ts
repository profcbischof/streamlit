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

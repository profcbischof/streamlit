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

import React, { ReactElement, ReactNode } from "react"

import { HelpCircle as HelpCircleIcon } from "react-feather"
import { useTheme } from "@emotion/react"

import Tooltip, {
  Placement,
} from "@streamlit/lib/src/components/shared/Tooltip"
import StreamlitMarkdown, {
  StreamlitMarkdownProps,
} from "@streamlit/lib/src/components/shared/StreamlitMarkdown"
import { EmotionTheme } from "@streamlit/lib/src/theme"

import {
  StyledLabelHelpInline,
  StyledTooltipIconWrapper,
} from "./styled-components"

export interface TooltipIconProps {
  placement?: Placement
  iconSize?: string
  isLatex?: boolean
  content: string
  children?: ReactNode
  markdownProps?: Partial<StreamlitMarkdownProps>
  onMouseEnterDelay?: number
}

function TooltipIcon({
  placement = Placement.AUTO,
  iconSize = "16",
  isLatex = false,
  content,
  children,
  markdownProps,
  onMouseEnterDelay,
}: TooltipIconProps): ReactElement {
  const theme: EmotionTheme = useTheme()
  return (
    <StyledTooltipIconWrapper
      className="stTooltipIcon"
      data-testid="stTooltipIcon"
      isLatex={isLatex}
    >
      <Tooltip
        content={
          <StreamlitMarkdown
            style={{ fontSize: theme.fontSizes.sm }}
            source={content}
            allowHTML={false}
            {...(markdownProps || {})}
          />
        }
        placement={placement}
        onMouseEnterDelay={onMouseEnterDelay}
        inline
      >
        {children || <HelpCircleIcon className="icon" size={iconSize} />}
      </Tooltip>
    </StyledTooltipIconWrapper>
  )
}

export const InlineTooltipIcon = ({
  placement = Placement.TOP_RIGHT,
  iconSize = "16",
  isLatex = false,
  content,
  children,
  markdownProps,
}: TooltipIconProps): ReactElement => {
  return (
    <StyledLabelHelpInline>
      <TooltipIcon
        placement={placement}
        iconSize={iconSize}
        isLatex={isLatex}
        content={content}
        markdownProps={markdownProps}
      >
        {children}
      </TooltipIcon>
    </StyledLabelHelpInline>
  )
}

export default TooltipIcon

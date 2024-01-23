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

from playwright.sync_api import Page, expect

from e2e_playwright.conftest import ImageCompareFunction


def test_displays_altair_chart(app: Page):
    expect(app.get_by_test_id("stArrowVegaLiteChart").locator("canvas")).to_have_count(
        8
    )


def test_altair_chart_displays_correctly(
    app: Page, assert_snapshot: ImageCompareFunction
):
    charts = app.get_by_test_id("stArrowVegaLiteChart")
    expect(charts).to_have_count(8)
    for index in range(charts.count()):
        assert_snapshot(
            charts.nth(index), name=f"st_arrow_altair_chart-displays-correctly-{index}"
        )
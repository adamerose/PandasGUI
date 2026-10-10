"""Filtering must preserve user columns used by the internal row mapping."""

import pandas as pd
import pytest

from pandasgui.store import PandasGuiDataFrameStore


@pytest.mark.parametrize('query', [None, '_temp_range_index > 15'])
def test_preserves_column_named_like_internal_index(query):
    frame = pd.DataFrame({
        '_temp_range_index': [10, 20, 30],
        '_temp_range_index (2)': [40, 50, 60],
        'value': [1, 2, 3],
    }, index=['a', 'a', 'b'])
    store = PandasGuiDataFrameStore(frame)
    if query is None:
        store.apply_filters()
        expected = frame
        expected_positions = [0, 1, 2]
    else:
        store.add_filter(query)
        expected = frame.iloc[1:]
        expected_positions = [1, 2]

    pd.testing.assert_frame_equal(store.df, expected)
    pd.testing.assert_frame_equal(store.df_unfiltered, frame)
    assert list(store.filtered_index_map) == expected_positions


def test_filtered_edit_targets_original_row_with_duplicate_index():
    frame = pd.DataFrame({
        '_temp_range_index': [10, 20, 30],
        'value': [1, 2, 3],
    }, index=['a', 'a', 'b'])
    store = PandasGuiDataFrameStore(frame)
    store.add_filter('_temp_range_index > 15')
    store.edit_data(0, 1, '9')

    expected = frame.copy()
    expected.iloc[1, 1] = 9
    pd.testing.assert_frame_equal(store.df_unfiltered, expected)
    pd.testing.assert_frame_equal(store.df, expected.iloc[1:])


def test_filter_without_collision_keeps_row_mapping():
    frame = pd.DataFrame({'value': [1, 2, 3]}, index=['a', 'a', 'b'])
    store = PandasGuiDataFrameStore(frame)
    store.add_filter('value > 1')

    pd.testing.assert_frame_equal(store.df, frame.iloc[1:])
    assert list(store.filtered_index_map) == [1, 2]

import pandas as pd

from app.analysis.correlation import correlation_analysis, find_strong_pairs


def test_perfect_positive_correlation_is_detected():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [2, 4, 6, 8, 10]})

    result = correlation_analysis(df)

    assert result["columns"] == ["a", "b"]
    assert result["strong_pairs"][0]["correlation"] == 1.0
    assert result["strong_pairs"][0]["direction"] == "positive"


def test_negative_correlation_reports_direction():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 8, 6, 4, 2]})

    pair = correlation_analysis(df)["strong_pairs"][0]

    assert pair["correlation"] == -1.0
    assert pair["direction"] == "negative"


def test_weak_correlation_is_not_reported_as_strong():
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5, 6], "b": [5, 1, 4, 2, 6, 3]})

    assert correlation_analysis(df)["strong_pairs"] == []


def test_single_numeric_column_produces_empty_matrix():
    df = pd.DataFrame({"a": [1, 2, 3], "label": list("xyz")})

    result = correlation_analysis(df)

    assert result["columns"] == []
    assert result["matrix"] == []


def test_strong_pairs_are_unique_and_sorted_by_strength():
    matrix = pd.DataFrame(
        [[1.0, 0.95, 0.75], [0.95, 1.0, 0.80], [0.75, 0.80, 1.0]],
        columns=["a", "b", "c"],
        index=["a", "b", "c"],
    )

    pairs = find_strong_pairs(matrix, threshold=0.7)

    assert len(pairs) == 3
    assert [abs(pair["correlation"]) for pair in pairs] == [0.95, 0.8, 0.75]

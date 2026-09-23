# The analysis engine

Everything InsightAI reports about a dataset is computed here, in
`backend/app/analysis`. The package imports pandas, NumPy and scikit-learn and
nothing else: no FastAPI, no SQLAlchemy, no Gemini. Each module is a set of plain
functions over a DataFrame, which is why the unit tests can assert exact values.

## Modules

| Module | Responsibility |
| --- | --- |
| `profiler.py` | Shape, memory use, and the mapping from pandas dtypes onto the four types the product reasons about: numeric, categorical, datetime, boolean |
| `statistics.py` | Count, mean, median, standard deviation, min, max, quartiles, IQR and skew per numeric column; IQR-based outlier counts |
| `quality.py` | Missing values, duplicate rows, constant columns, identifier-like columns, and columns whose stored type looks wrong |
| `categorical.py` | Unique counts and frequency distributions for categorical and boolean columns |
| `correlation.py` | Pearson correlation matrix and the strongest column pairs |
| `anomalies.py` | Isolation Forest over the numeric columns, for rows that are unusual as a combination |
| `insights.py` | Turns the computed summary into findings |
| `visualizations.py` | Chooses the charts worth drawing and emits ready-to-plot data |
| `engine.py` | Runs the above and returns one JSON-safe result |

## Thresholds

The rules are deliberately explicit rather than tuned, so a reader can judge them.

| Rule | Threshold | Defined in |
| --- | --- | --- |
| Missing data is worth reporting | 5% of rows | `insights.MISSING_WARNING_PCT` |
| Missing data is critical | 30% of rows | `insights.MISSING_CRITICAL_PCT` |
| Correlation counts as strong | \|r\| >= 0.7 | `correlation.STRONG_THRESHOLD` |
| A column is identifier-like | >= 90% unique values | `quality.HIGH_CARDINALITY_RATIO` |
| A category dominates | >= 80% of rows | `insights.DOMINANT_CATEGORY_PCT` |
| Outliers are worth reporting | >= 5% beyond the 1.5 x IQR fences | `insights.OUTLIER_WARNING_PCT` |
| A distribution is skewed | \|mean - median\| >= 0.25 standard deviations | `insights.SKEW_STD_RATIO` |
| Text parses as another type | >= 90% of values | `quality.NUMERIC_PARSE_THRESHOLD` |
| Text is converted to dates on load | >= 95% of values | `csv_loader.DATETIME_PARSE_THRESHOLD` |

## Why insights take a summary, not a DataFrame

`generate_insights()` is given the dictionary of numbers the other modules already
produced. It has no access to the data. A finding therefore cannot cite a statistic
that was never calculated — the constraint is structural, not a matter of care.

The same idea carries into the AI layer: `ai/context_builder.py` serialises this same
summary, and the model is told to answer only from it.

## Chart selection

`visualizations.py` picks charts from the detected column types rather than emitting
one per column:

- up to three histograms, for the numeric columns that vary the most;
- up to three bar charts, for categorical columns with between 2 and 50 values;
- one box-plot summary covering every numeric column;
- one scatter plot, for the most strongly correlated pair;
- one correlation heatmap when there are at least two numeric columns;
- one time series when a datetime column exists, bucketed by day, month or year
  depending on the span.

Choosing which chart answers a question is analysis, so it lives with the analysis and
is tested in Python. The frontend renders what it is handed.

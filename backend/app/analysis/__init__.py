"""Pure-Python data analysis. No FastAPI, no database, no AI."""

from app.analysis.engine import AnalysisResult, analyze_dataframe, build_preview

__all__ = ["AnalysisResult", "analyze_dataframe", "build_preview"]

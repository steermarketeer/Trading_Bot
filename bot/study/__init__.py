"""
Signal study: when a standard signal or chart pattern fires, how often does it work,
and does it matter whether it agrees with the weekly trend?

Pipeline: daily bars -> weekly trend -> events (signals + patterns) -> outcomes -> report.
Every event uses only data available at that day's close.
"""

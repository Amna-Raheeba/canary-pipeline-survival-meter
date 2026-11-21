"""Canary Pipeline Survival Meter.

Stage-wise canary survival as a leakage audit for LLM data
pipelines: plant labelled synthetic secrets, push them through the
pipeline, and measure exactly which stage leaks them and which stage
falsely claims to have redacted them.
"""

__version__ = "0.1.0"

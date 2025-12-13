"""
Test Bed Framework for Big Game

Provides configurable test infrastructure for region-based testing.
"""

from tests.infrastructure.test_bed.region_test_bed import RegionTestBed
from tests.infrastructure.test_bed.context_loaders import (
    ContextLoader,
    FreshContextLoader,
    CustomContextLoader,
)
from tests.infrastructure.test_bed.logger import LogEntry, InteractionLogger

__all__ = [
    "RegionTestBed",
    "ContextLoader",
    "FreshContextLoader",
    "CustomContextLoader",
    "LogEntry",
    "InteractionLogger",
]

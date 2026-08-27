#!/usr/bin/env python3
"""Compatibility entry point for the renamed v404 dual-device contracts."""

from __future__ import annotations

import unittest

from test_kgg_dual_device_v404 import DualDeviceV404ContractTests  # noqa: F401
from test_kgg_persistent_runtime_guard import PersistentRuntimeGuardTests  # noqa: F401


if __name__ == "__main__":
    unittest.main(verbosity=2)

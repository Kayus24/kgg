#!/usr/bin/env python3
"""Build a clean environment for Git commands targeting an explicit repository."""

from __future__ import annotations

import os
from collections.abc import Mapping


# `git rev-parse --local-env-vars` documents these as repository-local. Git
# exports several of them to hooks; inheriting them would make a command with a
# different cwd keep operating on the parent repository instead.
REPOSITORY_LOCAL_GIT_VARIABLES = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    "GIT_OBJECT_DIRECTORY",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_IMPLICIT_WORK_TREE",
    "GIT_GRAFT_FILE",
    "GIT_INDEX_FILE",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_REPLACE_REF_BASE",
    "GIT_PREFIX",
    "GIT_SHALLOW_FILE",
    "GIT_COMMON_DIR",
)


def sanitized_git_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    """Copy an environment without repository-local Git routing variables."""
    environment = dict(os.environ if source is None else source)
    for name in REPOSITORY_LOCAL_GIT_VARIABLES:
        environment.pop(name, None)
    for name in tuple(environment):
        if name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            environment.pop(name, None)
    return environment

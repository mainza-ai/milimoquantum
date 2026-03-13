"""Milimo Quantum — Extension Registry.

This module provides a registry for dynamically loading quantum platform extensions
(like MQDD) without hardcoding them into the core monolothic routers.
"""
import logging
from typing import Callable, Any
from fastapi import APIRouter

logger = logging.getLogger(__name__)

class Extension:
    def __init__(
        self,
        id: str,
        name: str,
        agent_type: str,
        slash_commands: list[str],
        intent_patterns: list[str],
        system_prompt: str,
        router: APIRouter | None = None,
        dispatch_handler: Callable[[str], dict] | None = None
    ):
        self.id = id
        self.name = name
        self.agent_type = agent_type
        self.slash_commands = slash_commands
        self.intent_patterns = intent_patterns
        self.system_prompt = system_prompt
        self.router = router
        self.dispatch_handler = dispatch_handler

class ExtensionRegistry:
    def __init__(self):
        self.extensions: dict[str, Extension] = {}

    def register(self, ext: Extension):
        self.extensions[ext.id] = ext
        logger.info(f"Registered extension: {ext.name} ({ext.id})")

    def get_extension_by_agent(self, agent_type: str) -> Extension | None:
        for ext in self.extensions.values():
            if ext.agent_type == agent_type:
                return ext
        return None
        
    def get_all_slash_commands(self) -> dict[str, str]:
        """Returns mapping of slash command -> agent_type"""
        cmds = {}
        for ext in self.extensions.values():
            for cmd in ext.slash_commands:
                cmds[cmd] = ext.agent_type
        return cmds
        
    def get_all_intent_patterns(self) -> list[tuple[list[str], str]]:
        """Returns list of (keywords, agent_type)"""
        patterns = []
        for ext in self.extensions.values():
            if ext.intent_patterns:
                patterns.append((ext.intent_patterns, ext.agent_type))
        return patterns

registry = ExtensionRegistry()

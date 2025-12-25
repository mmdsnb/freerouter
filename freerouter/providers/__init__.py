"""
Provider implementations for FreeRouter
"""

from .base import BaseProvider
from .openrouter import OpenRouterProvider
from .ollama import OllamaProvider
from .modelscope import ModelScopeProvider
from .iflow import IFlowProvider
from .static import StaticProvider

__all__ = [
    'BaseProvider',
    'OpenRouterProvider',
    'OllamaProvider',
    'ModelScopeProvider',
    'IFlowProvider',
    'StaticProvider',
]

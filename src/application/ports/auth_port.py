
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import requests


class AuthenticationPort(ABC):
    """Puerto para una estrategia de autenticación."""

    @abstractmethod
    def login(self, session: requests.Session) -> None:
        """Debe autenticar la sesión o lanzar AuthError."""
        ...

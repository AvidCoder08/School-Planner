from dataclasses import dataclass, field
from skoolplannr.state.session_state import SessionState


@dataclass
class AppState:
    session: SessionState = field(default_factory=SessionState)


app_state = AppState()

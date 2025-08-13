from typing import Dict, Any

class ProgressService:
    def __init__(self) -> None:
        # TODO: initialize storage (sqlite/json)
        pass

    def record_attempt(self, user_id: str, attempt: Dict[str, Any]) -> None:
        # TODO: persist attempt
        pass

    def get_progress(self, user_id: str) -> Dict[str, Any]:
        # TODO: return scores, badges, unlocks
        return { 'badges': [], 'scores': {}, 'levels_unlocked': {} }
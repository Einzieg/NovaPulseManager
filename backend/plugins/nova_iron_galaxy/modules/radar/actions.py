from backend.domain.action import ActionBase


class RadarRunAction(ActionBase):
    async def execute(self):
        raise NotImplementedError("Legacy action adapter is introduced in Phase 4")

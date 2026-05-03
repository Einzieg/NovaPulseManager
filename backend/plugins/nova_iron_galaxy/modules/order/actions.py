from backend.domain.action import ActionBase


class OrderRunAction(ActionBase):
    async def execute(self):
        raise NotImplementedError("Legacy action adapter is introduced in Phase 4")

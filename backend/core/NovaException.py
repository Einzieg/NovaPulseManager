class NovaException(Exception):
    def __init__(self, message="Nova"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


# ===== 新异常类（推荐使用） =====

class TaskCompleted(NovaException):
    """任务正常完成（控制流信号）

    用于插件内部表示任务已完成，需要提前结束执行循环。
    这不是错误，而是正常的控制流信号。
    """
    def __init__(self, message="任务完成"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class TaskAbortedError(NovaException):
    """任务被中止（环境问题/失败）

    用于表示任务因环境问题（如网络断开、登出等）无法继续执行。
    这会导致调度器将任务标记为失败。
    """
    def __init__(self, message="任务中止"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


# ===== 旧异常类（已弃用，保留用于向后兼容） =====
# 这些类将在未来版本中移除，请使用 TaskCompleted 或 TaskAbortedError

class TaskFinishes(TaskAbortedError):
    """已弃用：请使用 TaskAbortedError"""
    def __init__(self, message="任务结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class RadarFinishes(TaskCompleted):
    """已弃用：请使用 TaskCompleted"""
    def __init__(self, message="雷达结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class OrderFinishes(TaskCompleted):
    """已弃用：请使用 TaskCompleted"""
    def __init__(self, message="订单结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class PermPirateFinishes(TaskCompleted):
    """已弃用：请使用 TaskCompleted"""
    def __init__(self, message="常驻海盗结束"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message

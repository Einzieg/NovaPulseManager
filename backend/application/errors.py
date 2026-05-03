class ApplicationError(ValueError):
    """Base class for service-layer business errors."""


class DeviceNotFound(ApplicationError):
    pass


class WorkflowNotFound(ApplicationError):
    pass


class DeviceAlreadyRunning(ApplicationError):
    pass


class WorkflowValidationError(ApplicationError):
    pass


class PluginNotFound(ApplicationError):
    pass


class PluginConfigError(ApplicationError):
    pass

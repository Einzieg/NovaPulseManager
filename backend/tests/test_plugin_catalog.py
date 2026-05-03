from pathlib import Path

from backend.core.api.app import create_app
from backend.core.api.ws_manager import FastApiWebSocketManager
from backend.core.websocket import MessageHandlers
from backend.infrastructure.plugins import PluginCatalog


def test_plugin_catalog_discovers_legacy_app_actions():
    catalog = PluginCatalog(Path("backend/plugins"))
    catalog.discover()

    apps = catalog.list_apps()
    assert [app.app_id for app in apps] == ["nova_iron_galaxy"]

    actions = {action.action_ref: action for action in catalog.list_actions()}
    assert "nova_iron_galaxy.startup.launch" in actions
    assert "nova_iron_galaxy.permanent.run" in actions
    assert "nova_iron_galaxy.order.run" in actions
    assert "nova_iron_galaxy.radar.run" in actions
    assert actions["nova_iron_galaxy.order.run"].module_id == "order"


async def test_app_and_action_api_routes_do_not_break_legacy_plugins():
    handlers = MessageHandlers(Path("backend/plugins"), FastApiWebSocketManager())
    app = create_app(handlers, handlers.ws_server)
    paths = {route.path for route in app.routes}

    assert "/api/v1/apps" in paths
    assert "/api/v1/actions" in paths

    apps_response = await handlers.handle_app_list({})
    assert apps_response["apps"][0]["id"] == "nova_iron_galaxy"

    actions_response = await handlers.handle_action_list({})
    action_refs = {action["action_ref"] for action in actions_response["actions"]}
    assert "nova_iron_galaxy.permanent.run" in action_refs

    plugins_response = await handlers.handle_plugin_list({})
    plugin_ids = {plugin["id"] for plugin in plugins_response["plugins"]}
    assert "order-task" in plugin_ids
    assert "nova_iron_galaxy" not in plugin_ids

from .window import VRToolsWindow

from functools import partial
import asyncio
import omni.ext
import omni.kit.ui
import omni.ui as ui


# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print("[xiaopeng.vr.tools] some_public_function was called with x: ", x)
    return x ** x


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class XiaopengVrToolsExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    WINDOW_NAME = "VR Tools"
    MENU_PATH = f"Window/XPeng/{WINDOW_NAME}"

    def on_startup(self):
        # The ability to show up the window if the system requires it. We use it
        # in QuickLayout.
        ui.Workspace.set_show_window_fn(XiaopengVrToolsExtension.WINDOW_NAME, partial(self.show_window, None))

        # Put the new menu
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(
                XiaopengVrToolsExtension.MENU_PATH, self.show_window, toggle=True, value=False
            )

        # Show the window. It will call `self.show_window`
        # ui.Workspace.show_window(XiaopengVrToolsExtension.WINDOW_NAME)

    def on_shutdown(self):
        self._menu = None
        if self._window:
            self._window.destroy()
            self._window = None

        # Deregister the function that shows the window from omni.ui
        ui.Workspace.set_show_window_fn(XiaopengVrToolsExtension.WINDOW_NAME, None)

    def _set_menu(self, value):
        """Set the menu to create this window on and off"""
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(XiaopengVrToolsExtension.MENU_PATH, value)

    async def _destroy_window_async(self):
        # wait one frame, this is due to the one frame defer
        # in Window::_moveToMainOSWindow()
        await omni.kit.app.get_app().next_update_async()
        if self._window:
            self._window.destroy()
            self._window = None

    def _visiblity_changed_fn(self, visible):
        # Called when the user pressed "X"
        self._set_menu(visible)
        if not visible:
            # Destroy the window, since we are creating new window
            # in show_window
            asyncio.ensure_future(self._destroy_window_async())

    def show_window(self, menu, value):
        if value:
            self._window = VRToolsWindow(XiaopengVrToolsExtension.WINDOW_NAME, width=200, height=300)
            self._window.set_visibility_changed_fn(self._visiblity_changed_fn)
        elif self._window:
            self._window.visible = False

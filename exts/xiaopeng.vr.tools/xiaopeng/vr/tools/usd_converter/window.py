import omni.ext
import omni.ui as ui
import omni.kit.commands
import omni.usd
from typing import Union
from pxr import Usd, Sdf, UsdGeom, UsdShade
import os
import asyncio
import omni.kit.asset_converter as converter


class USDConverterWindow(ui.Window):
    def __init__(self, title: str, delegate=None, **kwargs):
        super().__init__(title, **kwargs)

        self.frame.set_build_fn(self._build_fn)

    def destroy(self):
        # It will destroy all the children
        super().destroy()

    def on_shutdown(self):
        self._win = None

    def show(self):
        self.visible = True
        self.focus()

    def hide(self):
        self.visible = False

    def _build_fn(self):
        def valid_path(path):
            clean_path = path.strip('"')
            if os.path.exists(clean_path):
                ext = os.path.splitext(clean_path)[1].lower()
                if ext == ".fbx":
                    return clean_path
            else:
                return None

        def on_convert():
            value = self.path_input.model.get_value_as_string()
            path = valid_path(value)
            if path:
                self.path_input.model.set_value(path)
                self.convert_usd(path)
            else:
                self.path_input.model.set_value('')

        with self.frame:
            with ui.VStack():
                ui.Spacer(height=5)
                with ui.HStack(height=20):
                    ui.Spacer(width=3)
                    ui.Label("File Path", name="header_attribute_name", width=70)
                    self.path_input = ui.StringField(name='path')
                    
                ui.Spacer(height=10)

                self.convert_btn = ui.Button("Convert to USD", clicked_fn=on_convert)
                
                ui.Spacer(height=10)

                self.progressbar = ui.ProgressBar(height=20)

    def progress_callback(self, current_step: int, total: int):
        # Show progress
        progress = current_step / total
        self.progressbar.model.set_value(progress)

        if progress == 1:
            self.convert_btn.enabled = True
            self.progressbar.model.set_value(0)

    async def convert(self, input_asset_path, output_asset_path):
        task_manager = converter.get_instance()
        task = task_manager.create_converter_task(input_asset_path, output_asset_path, self.progress_callback)
        success = await task.wait_until_finished()
        if not success:
            detailed_status_code = task.get_status()
            detailed_status_error_string = task.get_error_message()

    def convert_usd(self, source_path):
        file_name = os.path.splitext(source_path)[0]
        output_path = file_name + ".usd"

        # clean the old file
        if os.path.isfile(output_path):
            os.remove(output_path)

        # reset
        self.progressbar.model.set_value(0)
        self.convert_btn.enabled = False

        # async convert
        asyncio.ensure_future(self.convert(source_path, output_path))

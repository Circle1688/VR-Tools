import omni.ext
import omni.ui as ui
import omni.kit.commands
import omni.usd
from typing import Union, List
from pxr import Usd, Sdf, UsdGeom, UsdShade
import os
from omni.kit.widget.stage import StageIcons
from omni.kit.window.file_exporter import get_file_exporter
import json

from .material_output.window import MaterialOutputWindow
from .material_assign.window import MaterialAssignWindow
from .material_match.window import MaterialMatchWindow
from .usd_converter.window import USDConverterWindow
from .batch_rename.window import BatchRenameWindow

import omni.kit.pipapi
omni.kit.pipapi.install("fuzzywuzzy")

class VRToolsWindow(ui.Window):
    def __init__(self, title: str, delegate=None, **kwargs):
        super().__init__(title, **kwargs)

        self.material_output_window = None
        self.material_assign_window = None
        self.material_match_window = None
        self.usd_converter_window = None
        self.batch_rename_window = None

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

        with self.frame:
            with ui.VStack(spacing=5):
                ui.Button("Material Assign", height=40, clicked_fn=self.open_material_assign)
                ui.Button("Material Match", height=40, clicked_fn=self.open_material_match)
                ui.Button("Material Output", height=40, clicked_fn=self.open_material_output)
                ui.Button("USD Converter", height=40, clicked_fn=self.open_usd_converter)
                ui.Button("Batch Rename", height=40, clicked_fn=self.open_batch_rename)

    def open_material_output(self):
        if not self.material_output_window:
            self.material_output_window = MaterialOutputWindow("Material Output", width=400, height=110)
        else:
            self.material_output_window.visible = True
    
    def open_material_assign(self):
        if not self.material_assign_window:
            self.material_assign_window = MaterialAssignWindow("Material Assign", width=300, height=300)
        else:
            self.material_assign_window.visible = True
    
    def open_material_match(self):
        if not self.material_match_window:
            self.material_match_window = MaterialMatchWindow("Material Match", width=615, height=600)
        else:
            self.material_match_window.visible = True

    def open_usd_converter(self):
        if not self.usd_converter_window:
            self.usd_converter_window = USDConverterWindow("USD Converter", width=300, height=140)
        else:
            self.usd_converter_window.visible = True

    def open_batch_rename(self):
        if not self.batch_rename_window:
            self.batch_rename_window = BatchRenameWindow("Batch Rename", width=300, height=120)
        else:
            self.batch_rename_window.visible = True
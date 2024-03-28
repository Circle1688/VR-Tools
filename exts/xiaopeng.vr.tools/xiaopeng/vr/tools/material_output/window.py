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

class MaterialOutputWindow(ui.Window):
    def __init__(self, title: str, delegate=None, **kwargs):
        super().__init__(title, **kwargs)

        self.materials_path = None
        self.save_path = ""

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
                with ui.HStack(spacing=5, height=0):
                    ui.Label('Looks Path', width=80)
                    with ui.VStack(height=0):
                        ui.Spacer(height=3)
                        self.materials_path_field = ui.StringField(width=ui.Fraction(2), height=22)
                        self.materials_path_field.model.add_value_changed_fn(self.materials_path_changed)
                    ui.Button('Set', width=50, height=22, clicked_fn=self.set_materials_path)
                ui.Button("Output", height=40, clicked_fn=self.open_file_dialog)

    def materials_path_changed(self, model):
        self.materials_path = model.as_string

    def set_materials_path(self):
        path = self.get_select_prim_path()
        if path:
            self.materials_path = path
            self.materials_path_field.model.set_value(path)

    def get_select_prim_path(self):
        _selection = omni.usd.get_context().get_selection()
        paths = _selection.get_selected_prim_paths()
        if paths:
            return str(paths[0])
        return None
    
    def open_file_dialog(self):

        # Get the singleton extension object, but as weakref to guard against the extension being removed.
        file_exporter = get_file_exporter()
        file_exporter.show_window(
            title="Export As ...",
            export_button_label="Save",
            # The callback function called after the user has selected an export location.
            export_handler=self.export_handler,
            filename_url=self.save_path,
            file_extension_types=[(".ovmt", "omniverse material data")],
            should_validate=True
        )
    
    def export_handler(self, filename: str, dirname: str, extension: str = "", selections: List[str] = []):
        # print(f"> Export As '{filename}{extension}' to '{dirname}' with additional selections '{selections}'")
        self.save_path = os.path.join(dirname, filename)

        try:
            material_paths = self.get_children_paths(self.materials_path)
        except Exception as e:
            print(e)
            return
        
        material_data = {}
        for material_path in material_paths:
            material_name, bound_objs = self.get_bound_object_names(material_path)  # get the material binding objects
            material_data[material_name] = bound_objs

        with open(self.save_path + extension, "w", encoding="utf8") as f:
            f.write(json.dumps(material_data))

    
    def get_children_paths(self, parent_path):
        stage = omni.usd.get_context().get_stage()
        parent_prim = stage.GetPrimAtPath(parent_path)
        return [child.GetPrimPath() for child in parent_prim.GetAllChildren()]
    
    def get_bound_object_names(self, material_path):
        stage = omni.usd.get_context().get_stage()
        material_prim_obj = stage.GetPrimAtPath(material_path)

        prim_names = []
        stage_prims = list(stage.Traverse())
        bounds = UsdShade.MaterialBindingAPI.ComputeBoundMaterials(stage_prims, UsdShade.Tokens.allPurpose)
        for stage_prim, material, relationship in zip(stage_prims, bounds[0], bounds[1]):
            material_prim = material.GetPrim()
            if not material_prim.IsValid():
                continue
            
            if material_prim.GetPrimPath() != material_path:
                continue
                
            prim_names.append(stage_prim.GetName())

        material_name = material_prim_obj.GetName()

        return material_name, prim_names
    
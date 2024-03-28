import omni.ext
import omni.ui as ui
import omni.usd
from typing import Union
from pxr import Usd, Sdf, UsdGeom, UsdShade
import os
from omni.kit.widget.stage import StageIcons

class BatchRenameWindow(ui.Window):
    def __init__(self, title: str, delegate=None, **kwargs):
        super().__init__(title, **kwargs)

        self.rename_add = None
        self.replace_path = None
        self.current_selection = 1

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
                    ui.Label('Type', width=50)
                    type_option = ui.ComboBox(self.current_selection, "prefix", "suffix")
                    type_option.model.add_item_changed_fn(self.option_changed)
                with ui.HStack(spacing=5, height=0):
                    ui.Label('Rename', width=50)
                    with ui.VStack(height=0):
                        ui.Spacer(height=3)
                        rename_field = ui.StringField(width=ui.Fraction(2), height=22)
                        rename_field.model.add_value_changed_fn(self.rename_field_changed)
                ui.Button(f" {omni.kit.ui.get_custom_glyph_code('${glyphs}/menu_rename.svg')}  Rename ", 
                          width=50, height=22, clicked_fn=self.rename)
    
    def rename_field_changed(self, model):
        self.rename_add = model.as_string

    def option_changed(self, model, item):
        self.current_selection = model.get_item_value_model().as_int

    def rename(self):
        if self.rename_add:
            paths = self.get_select_prim_paths()
            if paths:
                with omni.kit.undo.group():
                    for path in paths:
                        sub_paths = path.split('/')
                        prim_name = sub_paths[-1]
                        parent_path = '/'.join(sub_paths[:-1])
                        if self.current_selection == 0:
                            path_to = parent_path + '/' + self.rename_add + '_' + prim_name
                        else:
                            path_to = parent_path + '/' + prim_name + '_' + self.rename_add

                        omni.kit.commands.execute('MovePrim',
                                path_from=path,
                                path_to=path_to)


    def get_select_prim_paths(self):
        _selection = omni.usd.get_context().get_selection()
        paths = _selection.get_selected_prim_paths()
        return paths 
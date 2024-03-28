import omni.ext
import omni.ui as ui
import omni.kit.commands
import omni.usd
from typing import Union
from pxr import Usd, Sdf, UsdGeom, UsdShade


class MaterialAssignWindow(ui.Window):
    def __init__(self, title: str, delegate=None, **kwargs):
        super().__init__(title, **kwargs)

        self._usd_context = omni.usd.get_context()
        self._selection = self._usd_context.get_selection()
        self.record_material_path = None

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
            with ui.VStack():
                self.label = ui.Label("Not recorded")

                def on_record():
                    self.record_material()

                def on_select_bound_object():
                    path = self.get_current_select_prim_path()
                    if path:
                        self.select_bound_object(path)

                def on_assign():
                    self.assign_material_to_mesh()

                with ui.VStack():
                    ui.Button("Record Material", clicked_fn=on_record)
                    ui.Button("Select Bound Objects", clicked_fn=on_select_bound_object)
                    ui.Button("Assign Material", clicked_fn=on_assign)

    def record_material(self):
        """
        It record the material
        """

        # returns a list of prim path strings
        path = self.get_current_select_prim_path()
        if path:
            material_path = self.get_material_path_from_mesh(path)
            if material_path:
                print(material_path)
                self.record_material_path = material_path
                self.label.text = str(self.record_material_path)

    def get_current_select_prim_path(self):
        """
        get the path of current select prim
        """

        # returns a list of prim path strings
        paths = self._selection.get_selected_prim_paths()
        if paths:
            # Get path of the first selected prim
            return paths[0] if len(paths) > 0 else None        
        return None

    def get_material_path_from_mesh(self, associated_mesh):
        """
        It get the material of the mesh that is currently selected in the viewport

        :param associated_mesh: The path to the mesh you want to select the material for
        """

        if associated_mesh:
            stage = omni.usd.get_context().get_stage()
            mesh = stage.GetPrimAtPath(associated_mesh)
            if mesh:
                current_material_prims = mesh.GetRelationship('material:binding').GetTargets()
                return current_material_prims[0] if len(current_material_prims) > 0 else None
        return None

    def assign_material_to_mesh(self):
        """
        It assign the material to mesh
        """

        if self.record_material_path:
            paths = self._selection.get_selected_prim_paths()

            if paths:
                omni.kit.commands.execute('BindMaterialCommand',
                        prim_path=paths,
                        material_path=str(self.record_material_path))

    def select_bound_object(self, path):
        """
        It select the bound objects
        path: the path of selected prim
        """

        # get the material path of select prim
        material_path = self.get_material_path_from_mesh(path)

        # get the material prim
        stage = omni.usd.get_context().get_stage()

        prim_paths = []
        stage_prims = list(stage.Traverse())
        bounds = UsdShade.MaterialBindingAPI.ComputeBoundMaterials(stage_prims, UsdShade.Tokens.allPurpose)
        for stage_prim, material, relationship in zip(stage_prims, bounds[0], bounds[1]):
            material_prim = material.GetPrim()
            if not material_prim.IsValid():
                continue
            
            if material_prim.GetPrimPath() != material_path:
                continue
                
            prim_paths.append(str(stage_prim.GetPrimPath()))

        omni.kit.commands.execute('SelectPrimsCommand',
            old_selected_paths=[],
            new_selected_paths=prim_paths,
            expand_in_stage=True)

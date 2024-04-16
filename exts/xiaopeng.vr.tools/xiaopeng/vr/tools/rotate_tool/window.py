import omni.ext
import omni.ui as ui
import omni.usd
from typing import Union
from pxr import Usd, Sdf, UsdGeom, UsdShade, Gf
import os
from omni.kit.widget.stage import StageIcons
import omni.kit.commands as cmd

class RotateToolWindow(ui.Window):
    def __init__(self, title: str, delegate=None, **kwargs):
        super().__init__(title, **kwargs)

        self.prim_path = ""
        self.current_selection = 1
        self.current_speed = 0.5
        self._start = False
        self.count = 0
        self.rotation = None
        self.direction = 0

        self.subscription_handle = None

        self.frame.set_build_fn(self._build_fn)

    def destroy(self):
        # It will destroy all the children
        super().destroy()

    def on_shutdown(self):
        self.subscription_handle = None
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
                    ui.Label('Prim Path', width=80)
                    with ui.VStack(height=0):
                        ui.Spacer(height=3)
                        self.prim_path_field = ui.StringField(width=ui.Fraction(2), height=22)
                        self.prim_path_field.model.add_value_changed_fn(self.prim_path_changed)
                    ui.Button('Set', width=50, height=22, clicked_fn=self.set_prim_path)
                
                with ui.HStack(spacing=5, height=0):
                    ui.Label('Axis', width=50)
                    type_option = ui.ComboBox(self.current_selection, "X", "Y", "Z", width=100)
                    type_option.model.add_item_changed_fn(self.option_changed)
                    ui.Label('Speed', width=50)
                    slider = ui.FloatSlider(min=0.1, max=1)
                    slider.model.set_value(self.current_speed)
                    slider.model.add_value_changed_fn(self.speed_changed)

                with ui.HStack():
                    ui.Button("<<", height=40, clicked_fn=self.left_rotate)
                    ui.Button("Stop", height=40, clicked_fn=self.stop_rotate)
                    ui.Button(">>", height=40, clicked_fn=self.right_rotate)
    
    def option_changed(self, model, item):
        self.current_selection = model.get_item_value_model().as_int

    def speed_changed(self, model: ui.SimpleFloatModel):
        self.current_speed = model.as_float

    def prim_path_changed(self, model):
        self.prim_path = model.as_string
    
    def set_prim_path(self):
        path = self.get_select_prim_path()
        if path:
            self.prim_path = path
            self.prim_path_field.model.set_value(path)

    def get_select_prim_path(self):
        _selection = omni.usd.get_context().get_selection()
        paths = _selection.get_selected_prim_paths()
        if paths:
            return str(paths[0])
        return None
    
    
    def on_update(self, p):
        if self._start and self.prim_path != "":
            stage: Usd.Stage = omni.usd.get_context().get_stage() 
            prim = stage.GetPrimAtPath(self.prim_path)
            if prim.IsValid():
                if self.direction == 0:
                    self.count += self.current_speed
                else:
                    self.count -= self.current_speed
                # translation, rotation, scale = self.get_world_transform_xform(prim)
                # rotation = prim.GetAttribute('xformOp:rotateXYZ').Get()
                # print(rotation)
                if self.current_selection == 0:
                    new_rotation = Gf.Vec3d(self.count, self.rotation[1], self.rotation[2])
                elif self.current_selection == 1:
                    new_rotation = Gf.Vec3d(self.rotation[0], self.count, self.rotation[2])
                else:
                    new_rotation = Gf.Vec3d(self.rotation[0], self.rotation[1], self.count)

                prim.GetAttribute("xformOp:rotateXYZ").Set(new_rotation, 0)
                # # self.count = 0

    def left_rotate(self):
        self.direction = 0
        self.start_rotate()

    def right_rotate(self):
        self.direction = 1
        self.start_rotate()


    def start_rotate(self):
        stage: Usd.Stage = omni.usd.get_context().get_stage() 
        prim = stage.GetPrimAtPath(self.prim_path)
        if prim.IsValid(): 
            self.rotation = prim.GetAttribute('xformOp:rotateXYZ').Get()
            if self.count == 0:
                self.count = self.rotation[self.current_selection]
            if self.subscription_handle is None:
                self.subscription_handle = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self.on_update, name="UPDATE_SUB")
            self._start = True

    def stop_rotate(self):
        self._start = False
        if self.subscription_handle is not None:
            self.subscription_handle = None

    def get_world_transform_xform(self, prim: Usd.Prim):
        """
        Get the local transformation of a prim using Xformable.
        See https://openusd.org/release/api/class_usd_geom_xformable.html
        Args:
            prim: The prim to calculate the world transformation.
        Returns:
            A tuple of:
            - Translation vector.
            - Rotation quaternion, i.e. 3d vector plus angle.
            - Scale vector.
        """
        xform = UsdGeom.Xformable(prim)
        time = Usd.TimeCode.Default() # The time at which we compute the bounding box
        world_transform: Gf.Matrix4d = xform.ComputeLocalToWorldTransform(time)
        translation: Gf.Vec3d = world_transform.ExtractTranslation()
        rotation: Gf.Rotation = world_transform.ExtractRotation()
        scale: Gf.Vec3d = Gf.Vec3d(*(v.GetLength() for v in world_transform.ExtractRotationMatrix()))
        return translation, rotation, scale
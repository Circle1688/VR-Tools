import omni.ext
import omni.ui as ui
import omni.kit.commands
import omni.usd
from typing import Union
from pxr import Usd, Sdf, UsdGeom, UsdShade
import os
from omni.kit.widget.stage import StageIcons

import omni.kit.pipapi
omni.kit.pipapi.install("fuzzywuzzy")

# from fuzzywuzzy import process
from fuzzywuzzy import fuzz

class MatchItem(ui.AbstractItem):
    """Single item of the model"""

    def __init__(self, material, match, matchs):
        super().__init__()
        self.material_model = ui.SimpleStringModel(material)
        self.match_model = ComboModel(matchs, match)

class MatchModel(ui.AbstractItemModel):
    """
    Represents the list of commands registered in Kit.
    It is used to make a single level tree appear like a simple list.
    """

    def __init__(self):
        super().__init__()
        self._childrens = []

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is not None:
            # Since we are doing a flat list, we return the children of root only.
            # If it's not root we return.
            return []

        return self._childrens
    
    def add_item(self, material, match, matchs):
        self._childrens.append(MatchItem(material, match, matchs))
        self._item_changed(None)

    def get_values_dict(self):
        value_dict = {}
        for child in self._childrens:
            material = child.material_model.as_string
            match = child.match_model.get_value_as_string()
            value_dict[material] = match
        return value_dict

    def clear(self):
        self._childrens = []
        self._item_changed(None)

    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 2

    def get_item_value_model(self, item, column_id):
        """
        Return value model.
        It's the object that tracks the specific value.
        In our case we use ui.SimpleStringModel.
        """
        if item and isinstance(item, MatchItem):
            return item.match_model if column_id == 1 else item.material_model
        
class ComboItem(ui.AbstractItem):
    def __init__(self, text):
        super().__init__()
        self.model = ui.SimpleStringModel(text)

class ComboModel(ui.AbstractItemModel):
    def __init__(self, matchs, match):
        super().__init__()
        self.matchs = matchs

        self._current_index = ui.SimpleIntModel()
        self._current_index.add_value_changed_fn(
            lambda a: self._item_changed(None))

        self._items = [
            ComboItem(text)
            for text in matchs
        ]

        self._current_index.set_value(self.matchs.index(match))
        

    def get_item_children(self, item):
        return self._items

    def get_item_value_model(self, item, column_id):
        if item is None:
            return self._current_index
        return item.model
    
    def get_value_as_string(self):
        return self.matchs[self._current_index.get_value_as_int()]
         
class EditableDelegate(ui.AbstractItemDelegate):
    """
    Delegate is the representation layer. TreeView calls the methods
    of the delegate to create custom widgets for each item.
    """

    def __init__(self):
        super().__init__()
        self.subscription = None

    def build_branch(self, model, item, column_id, level, expanded):
        """Create a branch widget that opens or closes subtree"""
        pass

    def build_widget(self, model, item, column_id, level, expanded):
        """Create a widget per column per item"""
        stack = ui.ZStack(height=20)
        with stack:
            value_model = model.get_item_value_model(item, column_id)           
            if column_id == 1:
                with ui.VStack():
                    ui.Spacer(height=2)
                    field = ui.ComboBox(value_model)
                    ui.Spacer(height=2)
            else:
                label = ui.Label(value_model.as_string)

class MaterialMatchWindow(ui.Window):
    def __init__(self, title: str, delegate=None, **kwargs):
        super().__init__(title, **kwargs)

        self.materials_path = None
        self.replace_path = None

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
                    ui.Label('Vred Looks Path', width=140)
                    with ui.VStack(height=0):
                        ui.Spacer(height=3)
                        self.materials_path_field = ui.StringField(width=ui.Fraction(2), height=22)
                        self.materials_path_field.model.add_value_changed_fn(self.materials_path_changed)
                    ui.Button('Set', width=50, height=22, clicked_fn=self.set_materials_path)

                with ui.HStack(spacing=5, height=0):
                    ui.Label('Replace Looks Path', width=140)
                    with ui.VStack(height=0):
                        ui.Spacer(height=3)
                        self.replace_path_field = ui.StringField(width=ui.Fraction(2), height=22)
                        self.replace_path_field.model.add_value_changed_fn(self.replace_path_changed)
                    ui.Button('Set', width=50, height=22, clicked_fn=self.set_replace_path)
                                
                ui.Button(f" {omni.kit.ui.get_custom_glyph_code('${glyphs}/menu_prim.svg')}  Match ",
                                 width=0, height=22, clicked_fn=self.match)
                
                with ui.HStack(height=0):
                    ui.Label('Material')
                    ui.Label('Replace')
                
                with ui.ScrollingFrame(
                    horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                    vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                    style_type_name_override="TreeView",
                ):
                    self._match_model = MatchModel()
                    self._delegate = EditableDelegate()
                    tree_view = ui.TreeView(
                        self._match_model,
                        delegate=self._delegate,
                        root_visible=False,
                        header_visible=False,
                        style_type_name_override="TreeView",
                    )
                
                with ui.HStack(spacing=5, height=0):
                    ui.Separator()
                    self.process_btn = ui.Button(f" {omni.kit.ui.get_custom_glyph_code('${glyphs}/menu_material.svg')}  Replace ",
                                    width=200, height=30, clicked_fn=self.process, enabled=False)
                    
    def materials_path_changed(self, model):
        self.materials_path = model.as_string

    def replace_path_changed(self, model):
        self.replace_path = model.as_string
                
    def set_materials_path(self):
        path = self.get_select_prim_path()
        if path:
            self.materials_path = path
            self.materials_path_field.model.set_value(path)

    def set_replace_path(self):
        path = self.get_select_prim_path()
        if path:
            self.replace_path = path
            self.replace_path_field.model.set_value(path)
                
    def get_select_prim_path(self):
        _selection = omni.usd.get_context().get_selection()
        paths = _selection.get_selected_prim_paths()
        if paths:
            return str(paths[0])
        return None
    
    def get_names_from_paths(self, paths):
        names = []
        for path in paths:
            name = self.get_prim_name(path)
            names.append(name)
        return names

    def match(self):
        self.process_btn.enabled=False
        try:
            material_paths = self.get_children_paths(self.materials_path)
            replace_path = self.get_children_paths(self.replace_path)
        except Exception as e:
            print(e)
            return

        material_names = self.get_names_from_paths(material_paths)

        matchs = self.get_names_from_paths(replace_path)

        results = self.classify_by_similarity(material_names, matchs)

        self._match_model.clear()
        matchs.insert(0, "None")
        for key, value in results.items():
            self._match_model.add_item(key, value, matchs)
        self.process_btn.enabled=True
    
    def process(self):
        results = self._match_model.get_values_dict()
        with omni.kit.undo.group():
            for name in results.keys():
                if results[name] != "None":
                    material_path = self.materials_path + '/' + name
                    prims_paths = self.get_bound_objects_paths(material_path)
                    target_material_path = self.replace_path + '/' + results[name]
                    
                    omni.kit.commands.execute('BindMaterialCommand',
                        prim_path=prims_paths,
                        material_path=target_material_path)

    def get_children_paths(self, parent_path):
        stage = omni.usd.get_context().get_stage()
        parent_prim = stage.GetPrimAtPath(parent_path)
        return [child.GetPrimPath() for child in parent_prim.GetAllChildren()]
    
    def get_bound_objects_paths(self, material_path):
        stage = omni.usd.get_context().get_stage()
        material_prim = stage.GetPrimAtPath(material_path)

        prim_paths = []
        stage_prims = list(stage.Traverse())
        bounds = UsdShade.MaterialBindingAPI.ComputeBoundMaterials(stage_prims, UsdShade.Tokens.allPurpose)
        for stage_prim, material, relationship in zip(stage_prims, bounds[0], bounds[1]):
            material_prim = material.GetPrim()
            if not material_prim.IsValid():
                continue
            
            if material_prim.GetPrimPath() != material_path:
                continue
                
            prim_paths.append(stage_prim.GetPrimPath())
        return prim_paths

            
    def get_prim_name(self, prim_path):
        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath(prim_path)
        return prim.GetName()
    
    def classify_by_similarity(self, texts, labels):
        # results = {}
        # classifications = [process.extractOne(text, labels)[0] for text in texts]
        # for text, classification in zip(texts, classifications):
        #     results[text] = classification

        # return results


        # 设置相似度阈值
        threshold = 60

        # 初始化分类结果字典
        categorized_dict = {}

        # 对于每一个待分类项
        for item in texts:
            max_ratio = 0
            matched_label = "None"
            for label in labels:
                ratio = fuzz.token_set_ratio(item, label)
                if ratio > max_ratio:
                    max_ratio = ratio
                    matched_label = label if max_ratio >= threshold else "None"
            
            categorized_dict[item] = matched_label

        return categorized_dict

    
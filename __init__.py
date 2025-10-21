#-----------------------------------------------------------
# Copyright (C) 2025 Pierre Navaro Auburtin
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------
import sys
import os
import processing


sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import tool_prototype as tp
from PyQt6.QtWidgets import (QWidget, 
                             QMessageBox,
                             QDialog, 
                             QVBoxLayout, 
                             QLabel, QLineEdit, 
                             QPushButton, 
                             QFileDialog, 
                             QHBoxLayout,
                             QComboBox,
                             QLabel, 
                             QSplitter, 
                             QFileDialog,
                             QMainWindow
                             )

from PyQt6.QtGui import QAction,QPixmap
from PyQt6.QtCore import Qt
from qgis.core import (QgsVectorLayer, 
                       QgsProject, 
                       QgsVectorLayerJoinInfo,
                       QgsFeature,
                       QgsWkbTypes,
                       QgsGraduatedSymbolRenderer,
                       QgsStyle,
                       QgsSymbol
                       )

from openpyxl import Workbook
import os


import pandas as pd




def classFactory(iface):
    return CUPPlugin(iface)


class PathInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter City Data File Path")
        self.setMinimumWidth(400)

        # Layout
        layout = QVBoxLayout()

        # Label
        self.label = QLabel("Please enter or select a file path:")
        layout.addWidget(self.label)

        # Text input
        self.path_input = QLineEdit()
        layout.addWidget(self.path_input)

        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)
        layout.addWidget(self.browse_button)

        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.path_input.setText(file_path)

    def get_path(self):
        return self.path_input.text()



class FolderPathDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select folder where the input files are located")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        label = QLabel("Please enter or select a folder path:")
        layout.addWidget(label)

        self.path_edit = QLineEdit()
        layout.addWidget(self.path_edit)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.open_folder_dialog)
        layout.addWidget(browse_button)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Choose Folder")
        if folder_path:
            self.path_edit.setText(folder_path)

    def get_folder_path(self):
        return self.path_edit.text()

class ImageDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Image Viewer")

        # Create a label and set the image
        label = QLabel()
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        label.setScaledContents(True)  # Optional: scales image to fit label

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)

        # Optional: resize the dialog to fit the image
        self.resize(pixmap.width(), pixmap.height())



class ExternalImageViewer(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Image Viewer")
        #self.resize(600, 400)

        layout = QVBoxLayout()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        self.load_image(image_path)

    def load_image(self, image_path):
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Image not found.")

class MainWindow(QWidget):
    def __init__(self,file_path):
        super().__init__()
        self.setWindowTitle("Result selector")

        layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        self.image_paths = {
            "Using reused elements - per element": file_path+'\OUT_FIG\\all_Avoided impact from using reuse.jpg',
            "Reusing - per element": file_path+'\OUT_FIG\\all_Avoided from reuse A1-3 building.jpg',
            "Reusing - per building": file_path+'\OUT_FIG\\per_building_Avoided from reuse A1-3 building.jpg',
            "Using reused elements - per building": file_path+'\OUT_FIG\\per_building_Avoided impact from using reuse.jpg'
            
        }

        for label, path in self.image_paths.items():
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, p=path: self.open_image_viewer(p))
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def open_image_viewer(self, image_path):
        self.viewer = ExternalImageViewer(image_path)
        self.viewer.show()
        


class ResultSelector(QMainWindow):
    def __init__(self,file_path):
        super().__init__()
        self.setWindowTitle("Result selector")
        self.setGeometry(100, 100, 800, 200)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel
        left_panel = self.create_panel("Using the deconstructed materials", "a",file_path)
        splitter.addWidget(left_panel)

        # Right panel
        right_panel = self.create_panel("Using reused materials for the refurbishment", "b",file_path)
        splitter.addWidget(right_panel)

        self.setCentralWidget(splitter)

    def create_panel(self, title, suffix,file_path):
        panel = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel(f"<b>{title}</b>"))
        
        Da={'Potential avoided impact per element':file_path+'\OUT_FIG\\all_Avoided from reuse A1-3 building.jpg',
            'Potential avoided impact per building':file_path+'\OUT_FIG\\per_building_Avoided from reuse A1-3 building.jpg',
            'Comparison based on reuse level':file_path+'\OUT_FIG\\Per level of reuse - Deconstruction.jpg'}
        
        Db={'Potential avoided impact per element':file_path+'\OUT_FIG\\all_Avoided impact from using reuse.jpg',
            'Potential avoided impact per building':file_path+'\OUT_FIG\\per_building_Avoided impact from using reuse.jpg',
            'Comparison based on reuse level':file_path+'\OUT_FIG\\Per level of reuse - Renovation.jpg'}
        if suffix=="a":
            D=Da
        elif suffix=="b":  
            D=Db
        
        for label, path in D.items():
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, p=path: self.open_image(p))
            layout.addWidget(btn)

        panel.setLayout(layout)
        return panel

    def open_image(self, path):
        # You can replace this with actual image paths or use QFileDialog to select
        self.viewer = ExternalImageViewer(path)
        self.viewer.show()


class NameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter the name of the city file")

        self.name = None  # This will store the entered name

        layout = QVBoxLayout()

        self.label = QLabel("Please the name of the city file as shown in QGIS")
        layout.addWidget(self.label)

        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit)

        self.button = QPushButton("OK")
        self.button.clicked.connect(self.accept_name)
        layout.addWidget(self.button)

        self.setLayout(layout)

    def accept_name(self):
        self.name = self.line_edit.text()
        self.accept()  # Close the dialog

class UnifiedInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Input Details")

        self.file_path = ""
        self.folder_path = ""
        self.name = ""

        layout = QVBoxLayout()

        # File path input
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        file_button = QPushButton("Browse File")
        file_button.clicked.connect(self.browse_file)
        file_layout.addWidget(QLabel("City data file path:"))
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(file_button)
        layout.addLayout(file_layout)

        # Folder path input
        folder_layout = QHBoxLayout()
        self.folder_edit = QLineEdit()
        folder_button = QPushButton("Browse Folder")
        folder_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(QLabel("Input data folder path:"))
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(folder_button)
        layout.addLayout(folder_layout)

        # Name input
        name_layout = QHBoxLayout()
        self.name_edit = QLineEdit()
        name_layout.addWidget(QLabel("Name of the city file in QGIS:"))
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept_inputs)
        layout.addWidget(ok_button)

        self.setLayout(layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.file_edit.setText(file_path)

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.folder_edit.setText(folder_path)

    def accept_inputs(self):
        self.file_path = self.file_edit.text()
        self.folder_path = self.folder_edit.text()
        self.name = self.name_edit.text()
        self.accept()

class FacadeOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Façade refurbishment options")
        self.setMinimumSize(300, 200)  # or whatever makes sense
        self.setMaximumSize(16777215, 16777215)  # effectively "no limit"

        # Store selected pairs
        self.selection_pairs = []

        # Main layout
        self.layout = QVBoxLayout()

        # Instruction text
        instruction = QLabel(
            "The left column are the façade systems as detailed in the façade option file and the city file. "
            "The right column is the façade replacement option."
        )
        instruction.setWordWrap(True)
        self.layout.addWidget(instruction)

        # Container for dropdown rows
        self.dropdown_container = QVBoxLayout()

        # Add initial row
        self.add_dropdown_row()

        # + Button to add more rows
        add_button = QPushButton("+")
        add_button.clicked.connect(self.add_dropdown_row)
        self.layout.addWidget(add_button)

        # OK Button to finalize
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.collect_selections)
        self.layout.addWidget(ok_button)
        
        # Default Button to finalize
        default_button = QPushButton("Default")
        default_button.clicked.connect(self.default_selections)
        self.layout.addWidget(default_button)

        # Add dropdown container to main layout
        self.layout.addLayout(self.dropdown_container)
        self.setLayout(self.layout)

    def add_dropdown_row(self):
        row_layout = QHBoxLayout()
    
        left_combo = QComboBox()
        left_combo.addItems([
            "brick wall without insulation", 
            "concrete block without insulation", 
            "concrete wall without insulation",
            "brick wall with insulation",
            "concrete block with insulation",
            "concrete wall with insulation"
        ])
    
        right_combo = QComboBox()
        right_combo.addItems([
            "brick wall without insulation", 
            "concrete block without insulation", 
            "concrete wall without insulation",
            "brick wall with insulation",
            "concrete block with insulation",
            "concrete wall with insulation"
        ])
    
        row_layout.addWidget(left_combo)
        row_layout.addWidget(right_combo)
    
        self.dropdown_container.addLayout(row_layout)
    
        # 👇 This line makes the dialog resize to fit new content
        self.adjustSize()


    def collect_selections(self):
        self.selection_pairs = []
        for i in range(self.dropdown_container.count()):
            row_layout = self.dropdown_container.itemAt(i)
            if isinstance(row_layout, QHBoxLayout):
                left_combo = row_layout.itemAt(0).widget()
                right_combo = row_layout.itemAt(1).widget()
                if left_combo and right_combo:
                    self.selection_pairs.append(
                        (left_combo.currentText(), right_combo.currentText())
                    )
        self.accept()
        
    def default_selections(self):
        self.selection_pairs = [("brick wall without insulation","brick wall with insulation" ),
                                ("concrete block without insulation","concrete block with insulation"),
                                ("concrete wall without insulation","concrete wall with insulation")]
        self.accept()

class CUPPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.main_window = None


    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.path_input.setText(file_path)

    def get_path(self):
        return self.path_input.text()


    def initGui(self):
        self.action = QAction('CUP', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        del self.action
        
    def from_csv_create_colored_layer(self,
                                      csv_file_path,
                                      city_layer_name,
                                      field_color,
                                      color_choice,
                                      result_layer_name):
        ##Import csv
        csv_path = csv_file_path
        #QMessageBox.information(None, 'CUP plugin', str(csv_path))
        uri = f"file:///{csv_path}?type=csv&delimiter=,&detectTypes=yes&geomType=none"
        csv_layer = QgsVectorLayer(uri, "City_Data_CSV", "delimitedtext")


        if not csv_layer.isValid():
            raise Exception("CSV layer failed to load")
        QgsProject.instance().addMapLayer(csv_layer)
        
        ##Create join
        # Get the layers
        target_layer = QgsProject.instance().mapLayersByName(city_layer_name)[0]
        join_layer = QgsProject.instance().mapLayersByName("City_Data_CSV")[0]
        
        # Run the processing algorithm
        result = processing.run("qgis:joinattributestable", {
            'INPUT': target_layer,
            'FIELD': 'fid',               # Field in target layer
            'INPUT_2': join_layer,
            'FIELD_2': 'fid',             # Field in join layer
            'FIELDS_TO_COPY': [],         # Empty = copy all fields
            'METHOD': 1,                  # Take the first matching record
            'DISCARD_NONMATCHING': False,
            'OUTPUT': 'memory:'           # Or use a file path to save
        })
        
        # Add the new layer to the project
        joined_layer = result['OUTPUT']
        fields_to_remove = [field.name() for field in joined_layer.fields() if field.name().startswith('fid_')]
        
        joined_layer.setName(result_layer_name)

        if fields_to_remove:
            joined_layer.startEditing()
            for field_name in fields_to_remove:
                idx = joined_layer.fields().indexOf(field_name)
                joined_layer.deleteAttribute(idx)
            joined_layer.commitChanges()
        
        # Add the cleaned layer to the project
        QgsProject.instance().addMapLayer(joined_layer)


        """
        
        original_layer = QgsProject.instance().mapLayersByName(city_layer_name)[0]
        if not original_layer:
            raise Exception(f"Layer '{city_layer_name}' not found.")
        copied_layer = original_layer.clone()
        copied_layer.setName(result_layer_name)
        QgsProject.instance().addMapLayer(copied_layer)
        
        join_layer = QgsProject.instance().mapLayersByName("City_Data_CSV")[0]

        join_info = QgsVectorLayerJoinInfo()
        join_info.setJoinFieldName("fid")         # Field in join_layer
        join_info.setTargetFieldName("fid")       # Field in copied_layer
        join_info.setJoinLayer(csv_layer)
        join_info.setUsingMemoryCache(True)       # Optional: improves performance
        join_info.setJoinLayerId(csv_layer.id()) # Ensures correct reference
        join_info.setPrefix("") 
        copied_layer.addJoin(join_info)
        
        
        for field in copied_layer.fields():
            print(field.name())
        """


        """
            # Get the original layer
        layer_name = city_layer_name
        original_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not original_layers:
            raise Exception(f"Layer '{layer_name}' not found.")
        original_layer = original_layers[0]
        
            # Create a memory copy of the original layer
        crs = original_layer.crs().authid()
        geometry_type = QgsWkbTypes.displayString(original_layer.wkbType())
        result_layer = QgsVectorLayer(f"{geometry_type}?crs={crs}", result_layer_name, "memory")
        result_provider = result_layer.dataProvider()
        
            # Copy fields from original layer
        result_provider.addAttributes(original_layer.fields())
        result_layer.updateFields()
        
            # Copy features from original layer
        for feat in original_layer.getFeatures():
            new_feat = QgsFeature()
            new_feat.setGeometry(feat.geometry())
            new_feat.setAttributes(feat.attributes())
            result_provider.addFeature(new_feat)
        
        result_layer.updateExtents()
        
        target_fields = [field.name() for field in result_layer.fields()]
        join_fields = [field.name() for field in csv_layer.fields()]
        
        print("Target Layer Fields:", target_fields)
        print("Join Layer Fields:", join_fields)
        QMessageBox.information(None, 'CUP plugin', str(target_fields))
        QMessageBox.information(None, 'CUP plugin', str(join_fields))
        
        field_to_check = "fid"

        if field_to_check in target_fields:
            print(f"'{field_to_check}' exists in the target layer.")
        else:
            print(f"'{field_to_check}' NOT found in the target layer.")
            QMessageBox.information(None, 'CUP plugin', f"'{field_to_check}' NOT found in the target layer.")
        
        if field_to_check in join_fields:
            print(f"'{field_to_check}' exists in the join layer.")
        else:
            print(f"'{field_to_check}' NOT found in the join layer.")
            QMessageBox.information(None, 'CUP plugin', f"'{field_to_check}' NOT found in the join layer.")
        


            # Now perform the join ONLY on the result layer
        QMessageBox.information(None, 'CUP plugin', str(csv_layer))
        QMessageBox.information(None, 'CUP plugin', str(result_layer))
        join_info = QgsVectorLayerJoinInfo()
        join_info.setJoinLayer(csv_layer)
        join_info.setJoinFieldName("fid")
        join_info.setTargetFieldName("fid")
        join_info.setUsingMemoryCache(True)
        join_info.setJoinLayerId(csv_layer.id())
        result_layer.addJoin(join_info)
        
            # Add the result layer to the project
        QgsProject.instance().addMapLayer(result_layer)
        """
        

        result_layer=joined_layer
        ##Graduate for color
            # Field name from joined CSV
        field_name = field_color
        
            # Create color ramp
        style = QgsStyle().defaultStyle()
        color_ramp = style.colorRamp(color_choice)
        
            # Create graduated renderer
        renderer = QgsGraduatedSymbolRenderer()
        renderer.setClassAttribute(field_name)
        renderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
        renderer.updateClasses(result_layer, 5)  # Number of classes
        renderer.updateColorRamp(color_ramp)
        
        result_layer.setRenderer(renderer)
        result_layer.triggerRepaint()

 
    def write_correspondance_table(self, data, filename):
        # Convert list of tuples into a DataFrame
        df = pd.DataFrame(data, columns=["System", "Replacement"])

        # Write to Excel file (overwrites if it exists)
        df.to_csv(filename, index=False)

        print(f"Excel file '{filename}' created successfully.")
        
    def remove_duplicate_keys(self,tuples_list):
        seen = set()
        result = []
        for item in tuples_list:
            key = item[0]
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result



    def run(self):
        
        #unified window input
        dialog = UnifiedInputDialog()
        if dialog.exec():
            city_file_path = dialog.file_path
            folder_path = dialog.folder_path
            city_file_name = dialog.name
            
        dialog = FacadeOptionsDialog()
        if dialog.exec():
            selections = dialog.selection_pairs
            selections=self.remove_duplicate_keys(selections)
            print("Selected façade options:")
            for left, right in selections:
                print(f"System: {left} → Replacement: {right}")
        
        QMessageBox.information(None, 'CUP plugin', str(selections))
        self.write_correspondance_table(selections,folder_path+"/correspondance_table.csv")
        
        #Running the calculations        
        tp.run_circular_urban_planning(folder_path,city_file_path)
        
        #Import the files in QGIS project
        self.from_csv_create_colored_layer(csv_file_path=folder_path+"/city_data_with_ca_lca.csv",
                                      city_layer_name=city_file_name,
                                      field_color='future_avoided/m2',
                                      color_choice="Reds",
                                      result_layer_name="Future_avoided_emissions"
                                      )
        
        self.from_csv_create_colored_layer(csv_file_path=folder_path+"/city_data_with_ca_lca.csv",
                                      city_layer_name=city_file_name,
                                      field_color='reno_avoided/m2',
                                      color_choice="Blues",
                                      result_layer_name="Renovation_with_reused_elements"
                                      )
        #Showing the results
        if self.main_window is None:
            #self.main_window = MainWindow(folder_path)
            self.main_window = ResultSelector(folder_path)
        self.main_window.show()


        

        QMessageBox.information(None, 'CUP plugin', "End of the script")
        
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QFileDialog, QSlider, QGraphicsView, QGraphicsPixmapItem, QGraphicsScene)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk

class PrinterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        v_left_layout = QVBoxLayout()
        lbl_connector = QLabel("First connect to printer:")
        v_left_layout.addWidget(lbl_connector)
        self.port_edit = QLineEdit("Port")
        v_left_layout.addWidget(self.port_edit)
        self.baud_rate_edit = QLineEdit("Baud Rate")
        v_left_layout.addWidget(self.baud_rate_edit)
        btn_connect = QPushButton("Connect")
        v_left_layout.addWidget(btn_connect)
        btn_unlock = QPushButton("Unlock Printer")
        v_left_layout.addWidget(btn_unlock)
        h_jog_layout = QHBoxLayout()
        btn_jog_y = QPushButton("Y+")
        btn_jog_x_minus = QPushButton("X-")
        btn_jog_x_plus = QPushButton("X+")
        btn_jog_y_minus = QPushButton("Y-")
        h_jog_layout.addWidget(btn_jog_y)
        h_jog_layout.addWidget(btn_jog_x_minus)
        h_jog_layout.addWidget(btn_jog_x_plus)
        h_jog_layout.addWidget(btn_jog_y_minus)
        v_left_layout.addLayout(h_jog_layout)
        lbl_print_settings = QLabel("Print settings")
        v_left_layout.addWidget(lbl_print_settings)
        self.ball_diameter_edit = QLineEdit("Ball Diameter (mm)")
        v_left_layout.addWidget(self.ball_diameter_edit)
        self.nozzle_diameter_edit = QLineEdit("Nozzle Diameter (mm)")
        v_left_layout.addWidget(self.nozzle_diameter_edit)
        lbl_stl_handler = QLabel("STL handler")
        v_left_layout.addWidget(lbl_stl_handler)

        btn_open_stl = QPushButton("Open STL file")
        btn_open_stl.clicked.connect(self.open_stl_file)
        v_left_layout.addWidget(btn_open_stl)

        btn_slice_stl = QPushButton("Slice STL")
        btn_slice_stl.clicked.connect(self.show_slices)
        v_left_layout.addWidget(btn_slice_stl)

        lbl_gcode_handler = QLabel("GCODE handler")
        v_left_layout.addWidget(lbl_gcode_handler)
        btn_open_gcode = QPushButton("Open GCODE file")
        v_left_layout.addWidget(btn_open_gcode)
        btn_print = QPushButton("Print")
        v_left_layout.addWidget(btn_print)
        btn_show_stl = QPushButton("Load and Show STL in Vedo")
        btn_show_stl.clicked.connect(self.show_stl)
        v_left_layout.addWidget(btn_show_stl)

        v_right_layout = QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        v_right_layout.addWidget(self.vtkWidget)

        h_main_layout = QHBoxLayout()
        h_main_layout.addLayout(v_left_layout)
        h_main_layout.addLayout(v_right_layout)
        self.setLayout(h_main_layout)
        self.setWindowTitle('Printer Interface')
        self.show()

    def open_stl_file(self):
        options = QFileDialog.Options()
        stlFilePath, _ = QFileDialog.getOpenFileName(self, "Open STL File", "", "STL Files (*.stl);;All Files (*)", options=options)
        if stlFilePath:
            self.selected_stl_path = stlFilePath

    def show_stl(self):
        if hasattr(self, 'selected_stl_path'):
            self.load_and_show_stl_in_vtk(self.vtkWidget, self.selected_stl_path)

    def load_and_show_stl_in_vtk(self, vtk_widget, path_stl):
        reader = vtk.vtkSTLReader()
        reader.SetFileName(path_stl)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        ren = vtk.vtkRenderer()
        ren.AddActor(actor)
        vtk_widget.GetRenderWindow().AddRenderer(ren)
        ren.ResetCamera()
        vtk_widget.GetRenderWindow().Render()

    def show_slices(self):
        if hasattr(self, 'selected_stl_path'):
            self.slice_viewer = SliceViewer(self.selected_stl_path)
            self.slice_viewer.show()

class SliceViewer(QWidget):
    def __init__(self, stl_path):
        super().__init__()
        self.stl_path = stl_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.slider = QSlider(Qt.Vertical)
        self.slider.valueChanged.connect(self.update_slice)
        layout.addWidget(self.slider)
        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)
        layout.addWidget(self.graphics_view)
        self.setLayout(layout)
        self.setWindowTitle('STL Slices')
        self.setGeometry(100, 100, 800, 600)
        self.generate_slices()
        self.slider.setMaximum(len(self.slices) - 1)
        self.update_slice(0)

    def generate_slices(self):
        reader = vtk.vtkSTLReader()
        reader.SetFileName(self.stl_path)
        reader.Update()
        bounds = reader.GetOutput().GetBounds()
        z_min, z_max = bounds[4], bounds[5]
        plane = vtk.vtkPlane()
        plane.SetOrigin(0, 0, z_min)
        plane.SetNormal(0, 0, 1)
        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputConnection(reader.GetOutputPort())
        self.slices = []
        z_position = z_min
        while z_position <= z_max:
            plane.SetOrigin(0, 0, z_position)
            cutter.Update()
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(cutter.GetOutputPort())
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            ren = vtk.vtkRenderer()
            ren_win = vtk.vtkRenderWindow()
            ren_win.SetOffScreenRendering(1)
            ren_win.AddRenderer(ren)
            ren.AddActor(actor)
            ren.SetBackground(1, 1, 1)
            ren_win.Render()
            w2if = vtk.vtkWindowToImageFilter()
            w2if.SetInput(ren_win)
            w2if.Update()
            image = w2if.GetOutput()
            height, width, _ = image.GetDimensions()
            vtk_array = image.GetPointData().GetScalars()
            components = vtk_array.GetNumberOfComponents()
            arr = vtk.util.numpy_support.vtk_to_numpy(vtk_array).reshape(height, width, components)
            qimage = QImage(arr, width, height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            self.slices.append(pixmap)
            z_position += 1

    def update_slice(self, index):
        pixmap = self.slices[index]
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        self.graphics_view.setScene(self.scene)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PrinterApp()
    sys.exit(app.exec_())

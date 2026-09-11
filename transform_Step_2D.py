import sys
import os
import numpy as np
import time
import traceback

# 設定 FreeCAD 路徑
freecad_bin_path = os.path.dirname(sys.executable)
if freecad_bin_path not in sys.path:
    sys.path.append(freecad_bin_path)

def log_error(msg):
    try:
        sys.stderr.buffer.write(f"[Internal Error] {msg}\n".encode('utf-8'))
    except:
        sys.stderr.write(f"[Internal Error] {msg}\n")
    sys.stderr.flush()

# ==========================================
# 【關鍵修正】智慧型視窗模組匯入 (兼容性修正)
# ==========================================
QtWidgets = None
try:
    import FreeCAD
    import FreeCADGui
    import Import
    
    # 嘗試匯入 PySide2 (FreeCAD 0.19 ~ 0.21)
    try:
        from PySide2 import QtWidgets
    except ImportError:
        # 如果失敗，嘗試 PySide6 (FreeCAD 0.22+)
        try:
            from PySide6 import QtWidgets
        except ImportError:
            # 如果都失敗，則不使用進階視窗控制，但不報錯
            QtWidgets = None
            
except ImportError as e:
    log_error(f"核心模組匯入失敗: {e}")
    sys.exit(1)

def make_window_invisible():
    """ 嘗試將視窗變透明並移出螢幕 (如果環境支援) """
    if QtWidgets is None:
        return # 環境不支援，直接跳過，避免崩潰

    try:
        app = QtWidgets.QApplication.instance()
        if not app: return
        for widget in app.topLevelWidgets():
            widget.setWindowOpacity(0.0)
            widget.move(-20000, -20000)
            widget.resize(1, 1)
    except:
        pass

def main():
    if len(sys.argv) < 7:
        log_error("參數不足")
        sys.exit(1)

    step_file = sys.argv[1]
    output_dir = sys.argv[2]
    width = int(sys.argv[3])
    height = int(sys.argv[4])
    zoom = float(sys.argv[5])
    angles_str = sys.argv[6]

    if not os.path.exists(step_file):
        log_error(f"檔案不存在: {step_file}")
        return

    # 解析角度
    angle_list = []
    try:
        groups = angles_str.split(';')
        for g in groups:
            if g.strip():
                parts = g.split(',')
                angle_list.append([float(parts[0]), float(parts[1]), float(parts[2])])
    except:
        sys.exit(1)

    # 1. 啟動 GUI
    try:
        FreeCADGui.showMainWindow()
        # 嘗試隱形 (如果模組存在)
        make_window_invisible()
        
        if QtWidgets:
            app = QtWidgets.QApplication.instance()
            if app: app.processEvents()
    except:
        pass

    doc_name = "RenderJob"
    if doc_name in FreeCAD.listDocuments():
        try:
            FreeCAD.closeDocument(doc_name)
        except:
            pass
    
    try:
        doc = FreeCAD.newDocument(doc_name)
        
        # 2. 匯入
        try:
            Import.insert(step_file, doc_name)
        except Exception as e:
            log_error(f"匯入失敗: {e}")
            return

        if hasattr(FreeCADGui, "updateGui"):
            FreeCADGui.updateGui()
            make_window_invisible()
        
        if not doc.Objects:
            log_error("匯入後無物件")
            return

        # 設定 SolidWorks 風格
        sw_color = (0.78, 0.78, 0.78)
        sw_line_color = (0.0, 0.0, 0.0)

        for obj in doc.Objects:
            if hasattr(obj, "ViewObject") and obj.ViewObject:
                try:
                    obj.ViewObject.ShapeColor = sw_color
                    obj.ViewObject.LineColor = sw_line_color
                    obj.ViewObject.LineWidth = 1.0 
                    obj.ViewObject.DisplayMode = "FlatLines"
                except:
                    continue

        # 3. 取得視圖
        view = None
        for _ in range(30):
            if FreeCADGui.ActiveDocument:
                view = FreeCADGui.ActiveDocument.ActiveView
            if view: break
            if hasattr(FreeCADGui, "updateGui"):
                FreeCADGui.updateGui()
            time.sleep(0.1)
        
        if view is None:
            try:
                view = FreeCADGui.getDocument(doc_name).createView()
            except:
                pass
        
        if view is None:
            log_error("無法建立 ActiveView")
            return

        # 背景設定
        try:
            if hasattr(view, "setGradientBackground"):
                view.setGradientBackground(False)
            if hasattr(view, "setBackgroundColor"):
                view.setBackgroundColor((1.0, 1.0, 1.0))
            elif hasattr(view, "BackgroundColor"):
                view.BackgroundColor = (1.0, 1.0, 1.0)
        except:
            pass

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 4. 截圖迴圈
        for i, angles in enumerate(angle_list):
            try:
                rx, ry, rz = np.radians(angles)
                
                Rx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
                Ry = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
                Rz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
                R = Rz @ Ry @ Rx

                fc_matrix = FreeCAD.Matrix()
                fc_matrix.A11, fc_matrix.A12, fc_matrix.A13 = R[0,0], R[0,1], R[0,2]
                fc_matrix.A21, fc_matrix.A22, fc_matrix.A23 = R[1,0], R[1,1], R[1,2]
                fc_matrix.A31, fc_matrix.A32, fc_matrix.A33 = R[2,0], R[2,1], R[2,2]
                
                rot = FreeCAD.Rotation(fc_matrix)
                view.setCameraOrientation(rot)
                
                view.fitAll()
                try:
                    if hasattr(view, "zoomIn"):
                        view.zoomIn(zoom)
                    elif hasattr(view, "setScale"):
                         view.setScale(view.getScale() * zoom)
                except:
                    pass 

                if hasattr(FreeCADGui, "updateGui"):
                    FreeCADGui.updateGui()

                # ==========================================
                # 【檔名格式維持】
                # ==========================================
                filename = f"view_y{angles[0]}_p{angles[1]}_r{angles[2]}.png"
                full_path = os.path.join(output_dir, filename)
                
                view.saveImage(full_path, width, height, "White")

            except Exception as e:
                log_error(f"截圖失敗 (Angle {i}): {e}")

    except Exception as e:
        log_error(f"未預期的錯誤: {e}")
        traceback.print_exc(file=sys.stderr)

    finally:
        if doc_name in FreeCAD.listDocuments():
            FreeCAD.closeDocument(doc_name)

if __name__ == "__main__":
    main()
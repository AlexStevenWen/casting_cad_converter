import sys
import os
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.IFSelect import IFSelect_RetDone

def StepToSTL_Direct(in_path, out_path, lin_deflection=0.1, ang_deflection=0.5):
    """
    將 STEP 轉換為 STL。
    """
    if not os.path.exists(in_path):
        print(f"錯誤: 找不到輸入檔案: {in_path}")
        return False

    try:
        print(f"正在讀取 STEP: {in_path}")
        
        # 1. 讀取 STEP
        step_reader = STEPControl_Reader()
        status = step_reader.ReadFile(in_path)
        
        if status != IFSelect_RetDone:
            print("錯誤: 無法讀取 STEP 檔案 (格式可能錯誤)。")
            return False
            
        step_reader.TransferRoots()
        shape = step_reader.OneShape()
        
        if shape.IsNull():
            print("錯誤: STEP 檔案中沒有有效的幾何形狀。")
            return False

        # 2. 網格化 (Tessellation)
        # 確保參數是浮點數
        lin_deflection = float(lin_deflection)
        ang_deflection = float(ang_deflection)
        
        print(f"正在生成網格 (精度: {lin_deflection}, 角度: {ang_deflection})...")
        # 這是關鍵步驟，沒有這步 STL 會是空的或失敗
        BRepMesh_IncrementalMesh(shape, lin_deflection, False, ang_deflection)
        
        # 3. 寫入 STL
        print(f"正在寫入 STL: {out_path}")
        stl_writer = StlAPI_Writer()
        stl_writer.ASCIIMode = False  # 使用二進制模式
        
        # 確保輸出資料夾存在
        out_dir = os.path.dirname(out_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # 執行寫入
        status = stl_writer.Write(shape, out_path)
        
        # 檢查寫入結果 (部分 OCC 版本 Write 回傳 void，部分回傳 bool)
        # 這裡我們只確認檔案是否產生
        if os.path.exists(out_path):
            print(f"轉換成功: {out_path}")
            return True
        else:
            print("轉換失敗: 檔案未建立。")
            return False

    except Exception as e:
        print(f"轉換過程中發生例外錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

#Params: [1]=input, [2]=output, [3]=lin(opt), [4]=ang(opt)
if __name__ == "__main__":
    # 這是你漏掉的部分：接收命令列參數並執行
    if len(sys.argv) < 3:
        print("Usage: python transform_OCCstl.py <input_step> <output_stl> [lin_deflection] [ang_deflection]")
        sys.exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2]
    
    # 接收公差參數 (如果 subprocess 有傳的話)
    lin_def = 0.1
    ang_def = 0.5
    
    if len(sys.argv) > 3:
        try:
            lin_def = float(sys.argv[3])
        except:
            pass
            
    if len(sys.argv) > 4:
        try:
            ang_def = float(sys.argv[4])
        except:
            pass

    StepToSTL_Direct(in_file, out_file, lin_def, ang_def)
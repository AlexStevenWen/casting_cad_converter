import sys
import os
import numpy as np
import FreeCAD
import Import
import Part
import Mesh
import io

# 假設你之前的存讀檔函式 (save_contact_dataset, load_dataset_v10) 已經定義在其他地方
# 或是直接整合進來，這裡為了簡潔，我寫了一個通用的內部 loader/saver

class SinglePartTransformer:
    def __init__(self, in_step, in_cloud, out_step, out_cloud, 
                 Fvector=(0, 0, 1), Frotation=0, do_align=True, align_target=(0, 0, 0)):
        """
        針對單一件 STEP 與 單一點雲 進行同步變換 (基於 OCC 內核)。
        """
        self.in_step = in_step
        self.in_cloud = in_cloud
        self.out_step = out_step
        self.out_cloud = out_cloud
        
        # 變換參數
        self.Fvector = Fvector      # 旋轉軸
        self.Frotation = Frotation  # 旋轉角度
        self.do_align = do_align    # 是否將形心對正到目標
        self.align_target = align_target

        # 核心：用來儲存從 STEP 計算出來的矩陣
        self.occ_matrix = None 

    def run(self):
        """
        主執行流程：
        1. 處理 STEP -> 取得變換矩陣 (OCC Matrix)
        2. 讀取點雲 -> 套用矩陣 -> 存檔
        """
        print(f"--- 開始處理 ---")
        print(f"STEP 輸入: {self.in_step}")
        print(f"Cloud 輸入: {self.in_cloud}")

        # 1. 先處理 STEP，這樣才能拿到正確的矩陣
        self._process_step_and_extract_matrix()

        # 2. 再處理點雲
        if os.path.exists(self.in_cloud):
            self._process_cloud_with_matrix()
        else:
            print(f"警告: 找不到點雲檔案 {self.in_cloud}，跳過點雲處理。")
        
        print("--- 處理完成 ---\n")

    def _process_step_and_extract_matrix(self):
        """
        讀取 STEP，計算 Placement，提取矩陣，並匯出變換後的 STEP。
        """
        # 1. 開啟文件
        Import.open(self.in_step)
        doc = FreeCAD.ActiveDocument
        
        # 2. 抓取物件 (假設只有一個主要零件)
        objs = [obj for obj in doc.Objects if hasattr(obj, 'Shape')]
        if not objs:
            raise ValueError(f"STEP 檔中找不到 Shape 物件: {self.in_step}")
        target_obj = objs[0]

        # 3. 計算平移 (Alignment)
        translation_placement = FreeCAD.Placement()
        if self.do_align:
            target_obj.recompute()
            # 獲取 OCC 計算的形心
            centroid = target_obj.Shape.CenterOfMass
            target_pos = FreeCAD.Vector(self.align_target)
            
            # 位移向量 = 目標 - 目前形心
            move_vec = target_pos - centroid
            translation_placement.Base = move_vec
            print(f"OCC 形心計算: {centroid}, 位移向量: {move_vec}")

        # 4. 計算旋轉 (Rotation)
        rotation_placement = FreeCAD.Placement()
        # FreeCAD 旋轉預設是以 (0,0,0) 為軸心
        rotation_placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(self.Fvector), self.Frotation)

        # 5. 組合變換 (先平移，再旋轉)
        # 數學意義: P_final = Rotation * (P_original + Translation)
        total_placement = rotation_placement.multiply(translation_placement)

        # ==========================================================
        # *** 關鍵：提取 OCC 4x4 矩陣 ***
        # ==========================================================
        mat = total_placement.toMatrix()
        self.occ_matrix = np.array([
            [mat.A11, mat.A12, mat.A13, mat.A14],
            [mat.A21, mat.A22, mat.A23, mat.A24],
            [mat.A31, mat.A32, mat.A33, mat.A34],
            [mat.A41, mat.A42, mat.A43, mat.A44]
        ], dtype=np.float64)
        # ==========================================================

        # 6. 應用到物件並匯出
        target_obj.Placement = total_placement
        doc.recompute()
        
        # 確保輸出目錄存在
        out_dir = os.path.dirname(self.out_step)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
                
        Part.export([target_obj], self.out_step)
        print(f"STEP 已匯出: {self.out_step}")
        
        FreeCAD.closeDocument(doc.Name)

    def _process_cloud_with_matrix(self):
        """
        使用提取出的 occ_matrix 變換點雲 (支援 4 種格式)。
        """
        # 1. 載入點雲 (使用通用載入器)
        data = self._load_any_cloud(self.in_cloud)
        if data is None: 
            return

        N, D = data.shape
        print(f"點雲格式: ({N}, {D})")
        
        # 提取旋轉 (3x3) 與 平移 (3,)
        R = self.occ_matrix[0:3, 0:3]
        T = self.occ_matrix[0:3, 3]

        # 2. 座標變換 (前三欄 XYZ)
        xyz = data[:, 0:3]
        # 公式: P_new = P_old @ R.T + T
        xyz_transformed = np.dot(xyz, R.T) + T
        data[:, 0:3] = xyz_transformed

        # 3. 法向量變換 (如果有)
        # 判斷維度 D
        # D=3: XYZ
        # D=4: XYZ + I
        # D=6: XYZ + NxNyNz
        # D=7: XYZ + NxNyNz + I
        
        if D >= 6:
            # 假設 Index 3,4,5 是法向量
            normals = data[:, 3:6]
            # 法向量只旋轉，不平移
            normals_transformed = np.dot(normals, R.T)
            data[:, 3:6] = normals_transformed
        
        # 4. 強度 (Intensity) / 額外維度
        # 如果是 (N,4) -> Index 3 是強度，保持不變
        # 如果是 (N,7) -> Index 6 是強度，保持不變
        # 只要我們不覆蓋它，它就會跟著點一起移動 (因為是同一列數據)

        # 5. 存檔
        self._save_any_cloud(data, self.out_cloud)

    def _load_any_cloud(self, path):
        """簡易通用讀取器 (.npz, .h5, .ply, .npy)"""
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext == '.npz':
                with np.load(path) as f:
                    # 嘗試抓常見的 key，或是第一個 key
                    keys = list(f.keys())
                    if 'data' in keys: return f['data']
                    if 'point_cloud' in keys: return f['point_cloud']
                    return f[keys[0]]
            elif ext == '.npy':
                return np.load(path)
            # 這裡可以根據你的需求加入 .h5 或 .ply 讀取
            else:
                print(f"尚未實作此格式讀取: {ext}")
                return None
        except Exception as e:
            print(f"讀取點雲失敗: {e}")
            return None

    def _save_any_cloud(self, data, path):
        """簡易通用存檔器"""
        try:
            cloud_dir = os.path.dirname(self.out_cloud)
            if cloud_dir:
                os.makedirs(cloud_dir, exist_ok=True)
            ext = os.path.splitext(path)[1].lower()
            if ext == '.npz':
                np.savez_compressed(path, data=data)
            elif ext == '.npy':
                np.save(path, data)
            else:
                # 預設存 npy 如果副檔名不認識
                np.save(path + ".npy", data)
            print(f"點雲已匯出: {path}")
        except Exception as e:
            print(f"存檔點雲失敗: {e}")


# ==========================================
# 主程式入口
# ==========================================
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python transform_single.py <in_step> <in_cloud> <out_step> <out_cloud> [Fvector] [Frotation] [align_target]")
        print("Example: python transform_single.py part.step part.npz out_part.step out_part.npz '0,0,1' 90 '0,0,0'")
    else:
        in_step = sys.argv[1]
        in_cloud = sys.argv[2]
        out_step = sys.argv[3]
        out_cloud = sys.argv[4]
        
        # 參數解析
        Fvector_str = sys.argv[5] if len(sys.argv) > 5 else "0,0,1"
        Frotation = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
        align_target_str = sys.argv[7] if len(sys.argv) > 7 else "0,0,0"

        # 轉換字串為 Tuple
        Fvector = tuple(map(float, Fvector_str.split(",")))
        align_target = tuple(map(float, align_target_str.split(",")))

        # 執行
        transformer = SinglePartTransformer(
            in_step, in_cloud, out_step, out_cloud,
            Fvector=Fvector, 
            Frotation=Frotation, 
            do_align=True, 
            align_target=align_target
        )
        transformer.run()
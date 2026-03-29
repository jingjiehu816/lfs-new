# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_ts_profile_table.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR 
import warnings
warnings.filterwarnings('ignore')

# 🎯 匹配实际文件名
INPUT_CSV = os.path.join(DATA_OUT_DIR, 'TS_Profile_Evaluation_20230101-20241231.csv')
LAYERS = ['0-300m', '300-500m', '500-1000m']

def get_ts_data_rows(var_type='T'): # T or S
    if not os.path.exists(INPUT_CSV): 
        print(f"❌ 找不到 TS Profile 数据文件: {INPUT_CSV}")
        return None
    
    df = pd.read_csv(INPUT_CSV)
    final_rows = []
    
    # 🎯 遍历区域，跳过南海 (SCS)
    for reg_key, reg_info in REGIONS.items():
        if reg_key == 'SCS': 
            continue
            
        for ly in LAYERS:
            # 🎯 布局调整：[区域名, 深度层, Bias, MAE, RMSE]
            row = [reg_info['name'], ly]
            
            for m in ['Bias', 'MAE', 'RMSE']:
                col = f"{reg_key}_{var_type}_{m}_{ly}"
                if col in df.columns:
                    val = df[col].mean()
                    row.append(val)
                else:
                    row.append(np.nan)
            final_rows.append(row)
    return final_rows

def draw_ts_table(data, var_label, unit):
    rows_n = len(data) + 1
    # 调整画布比例
    fig, ax = plt.subplots(figsize=(12, rows_n * 0.5 + 1), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, rows_n); ax.axis('off')
    
    # 🎯 五列布局：Region, Layer, Bias, MAE, RMSE
    x_c = [0.15, 0.40, 0.60, 0.78, 0.93]
    headers = ['Region', 'Layer', f'Bias {unit}', f'MAE {unit}', f'RMSE {unit}']
    
    # 1. 画表头
    for j, h in enumerate(headers):
        ax.text(x_c[j], rows_n - 0.5, h, ha='center', va='center', weight='bold', size=12)
    
    # 2. 画内容
    for i, row in enumerate(reversed(data)):
        y_pos = i + 0.5
        # 区域名和深度层
        ax.text(x_c[0], y_pos, row[0], ha='center', va='center', size=11, weight='bold')
        ax.text(x_c[1], y_pos, row[1], ha='center', va='center', size=11)
        # 数值指标
        for j, val in enumerate(row[2:]):
            txt = f"{val:.4f}" if not np.isnan(val) else "N/A"
            ax.text(x_c[j+2], y_pos, txt, ha='center', va='center', size=11)

    # 3. 装饰线
    ax.plot([0.02, 0.98], [rows_n, rows_n], 'k', lw=2)
    ax.plot([0.02, 0.98], [rows_n-1, rows_n-1], 'k', lw=1)
    ax.plot([0.02, 0.98], [0, 0], 'k', lw=2)
    
    plt.title(f'TS Profile {var_label} Vertical Evaluation (No SCS)', pad=25, weight='bold', size=15)
    
    # 🎯 覆盖保存
    save_path = os.path.join(PLOT_OUT_DIR, f'Table_TS_Profile_{var_label}.png')
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    print(f"✅ TS Profile {var_label} 表格已生成（已剔除南海）: {save_path}")

if __name__ == '__main__':
    for v, u in [('T', '(℃)'), ('S', '(PSU)')]:
        data = get_ts_data_rows(v)
        if data:
            draw_ts_table(data, v, u)
# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_tl_regional_table.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR 
import warnings
warnings.filterwarnings('ignore')

# 🎯 读取分区域统计表
INPUT_CSV = os.path.join(DATA_OUT_DIR, 'Thermocline_Evaluation_20230101-20241231.csv')
VARS = {'thickness': 'Thickness', 'upper_depth': 'Upper Boundary', 'lower_depth': 'Lower Boundary'}

def get_regional_data():
    if not os.path.exists(INPUT_CSV): 
        print(f"❌ 找不到分区域数据文件: {INPUT_CSV}"); return None
    
    df = pd.read_csv(INPUT_CSV)
    final_rows = []
    
    # 🎯 包含所有区域，不再过滤 SCS
    for reg_key, reg_info in REGIONS.items():
        for v_key, v_name in VARS.items():
            row = [reg_info['name'], v_name]
            for m in ['Bias', 'MAE', 'RMSE']:
                col = f"{reg_key}_{v_key}_{m}"
                # 如果某区域（如 SCS）完全没数据，mean 会返回 NaN
                val = df[col].mean() if col in df.columns else np.nan
                row.append(val)
            final_rows.append(row)
    return final_rows

def draw_regional_table(data):
    rows_n = len(data) + 1
    # 根据区域数量动态调整高度
    fig, ax = plt.subplots(figsize=(12, rows_n * 0.45 + 1), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, rows_n); ax.axis('off')
    
    x_c = [0.15, 0.42, 0.62, 0.78, 0.93]
    headers = ['Region', 'Variable', 'Bias (m)', 'MAE (m)', 'RMSE (m)']
    
    # 画表头
    for j, h in enumerate(headers):
        ax.text(x_c[j], rows_n - 0.5, h, ha='center', va='center', weight='bold', size=12)
    
    # 画内容
    for i, row in enumerate(reversed(data)):
        y_pos = i + 0.5
        ax.text(x_c[0], y_pos, row[0], ha='center', va='center', size=11, weight='bold')
        ax.text(x_c[1], y_pos, row[1], ha='center', va='center', size=11)
        for j, val in enumerate(row[2:]):
            txt = f"{val:.3f}" if not np.isnan(val) else "N/A"
            ax.text(x_c[j+2], y_pos, txt, ha='center', va='center', size=11)

    ax.plot([0.02, 0.98], [rows_n, rows_n], 'k', lw=2)
    ax.plot([0.02, 0.98], [rows_n-1, rows_n-1], 'k', lw=1)
    ax.plot([0.02, 0.98], [0, 0], 'k', lw=2)
    
    plt.title('Regional Thermocline Evaluation (Full Set)', pad=25, weight='bold', size=15)
    out_file = os.path.join(PLOT_OUT_DIR, 'Table_Thermocline_Regional.png')
    plt.savefig(out_file, bbox_inches='tight')
    plt.close()
    print(f"✅ 温跃层全区域评估表已生成: {out_file}")

if __name__ == '__main__':
    d = get_regional_data()
    if d: draw_regional_table(d)
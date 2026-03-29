# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_mld_table.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR
import warnings
warnings.filterwarnings('ignore')

# 🎯 修复：匹配你 data 目录下的实际文件名
INPUT_CSV = os.path.join(DATA_OUT_DIR, 'MLD_Evaluation_20230101-20241231.csv')
TIME_PERIODS = {'1-7 d': range(1, 8), '8-15 d': range(8, 16), '16-30 d': range(16, 31)}
PERIODS = list(TIME_PERIODS.keys())

def get_mld_data_rows(metric):
    """从 CSV 提取指定指标的数据"""
    if not os.path.exists(INPUT_CSV):
        print(f"❌ 找不到数据文件: {INPUT_CSV}")
        return None
    
    df = pd.read_csv(INPUT_CSV)
    rows = []
    for r_key, r_info in REGIONS.items():
        row = [r_info['name']]
        for days in TIME_PERIODS.values():
            col = f'{r_key}_{metric}'
            # 兼容不同脚本可能产生的大小写差异
            if col not in df.columns:
                col = f'{r_key}_{metric.capitalize()}'
            
            if col in df.columns:
                val = df[df['forecast_day'].isin(days)][col].mean()
            else:
                val = np.nan
            row.append(val)
        rows.append(row)
    return rows

def draw_mld_table(data, metric):
    """绘制 MLD 评估表格"""
    # 1个区域名列 + 3个时效列
    w_first, w_rest = 0.28, (1.0 - 0.28) / 3
    col_widths = [w_first] + [w_rest] * 3
    x_pos = [0] + list(np.cumsum(col_widths))
    x_centers = [(x_pos[i] + x_pos[i+1])/2 for i in range(len(col_widths))]

    total_rows = 2 + len(data)
    fig, ax = plt.subplots(figsize=(10, total_rows * 0.8), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, total_rows); ax.axis('off')

    # 1. 写入数据记录
    for i, row in enumerate(reversed(data)):
        y_c = i + 0.5
        ax.text(0.02, y_c, row[0], ha='left', va='center', weight='bold', size=13)
        for j, val in enumerate(row[1:]):
            txt = f"{val:.2f}" if not np.isnan(val) else "N/A"
            ax.text(x_centers[j+1], y_c, txt, ha='center', va='center', size=13)

    # 2. 写入表头
    y_sub, y_super = len(data) + 0.5, len(data) + 1.5
    ax.text(x_centers[0], y_sub, "Study Region", ha='center', va='center', weight='bold', size=14)
    for j in range(3):
        ax.text(x_centers[j+1], y_sub, PERIODS[j], ha='center', va='center', weight='bold', size=13)

    # 大标题 (指标名)
    ax.text((x_pos[1] + x_pos[4]) / 2, y_super, f"{metric} (m)", ha='center', va='center', weight='bold', size=15)

    # 3. 绘制实线
    kws = {'color': 'k', 'solid_capstyle': 'butt'}
    ax.plot([0, 1], [total_rows, total_rows], lw=2, **kws) # 顶线
    ax.plot([x_pos[1]+0.01, x_pos[4]-0.01], [len(data)+1, len(data)+1], lw=1, **kws) # 指标下划线
    ax.plot([0, 1], [len(data), len(data)], lw=1, **kws) # 分隔线
    ax.plot([0, 1], [0, 0], lw=2, **kws) # 底线

    plt.title(f'Mixed Layer Depth (MLD) {metric} Evaluation', pad=25, fontsize=16, weight='bold')
    
    out_file = os.path.join(PLOT_OUT_DIR, f'Table_MLD_{metric}_Combined.png')
    plt.savefig(out_file, bbox_inches='tight')
    print(f"✅ MLD {metric} 表格已生成: {out_file}")
    plt.close()

if __name__ == '__main__':
    # 依次为 Bias, MAE, RMSE 生成三张表格
    for m in ['Bias', 'MAE', 'RMSE']:
        tbl_data = get_mld_data_rows(m)
        if tbl_data:
            draw_mld_table(tbl_data, m)
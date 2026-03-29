# /data03/hjj/hjj/LFS-new/newwork/region/02_plot_eke_table.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR 
import warnings
warnings.filterwarnings('ignore')

TIME_PERIODS = {'1-7 d': range(1, 8), '8-15 d': range(8, 16), '16-30 d': range(16, 31)}
PERIODS = list(TIME_PERIODS.keys())
SEASONS = ['Spring', 'Summer', 'Autumn', 'Winter']

def get_data(metric):
    dfs = []
    for s in SEASONS:
        f_path = os.path.join(DATA_OUT_DIR, f'EKE_TimeSeries_{s}.csv')
        # 如果某个季节跑漏了，生成一个空的防报错
        if os.path.exists(f_path): dfs.append(pd.read_csv(f_path))
        else: dfs.append(pd.DataFrame(columns=['forecast_day']))
    
    rows = []
    for r_key, r_info in REGIONS.items():
        row = [r_info['name']]
        # 依次填入春、夏、秋、冬
        for df in dfs:
            for days in TIME_PERIODS.values():
                col = f'{r_key}_{metric}' # 匹配 01 脚本的大写 Bias, MAE, RMSE
                if col in df.columns and not df.empty:
                    val = df[df['forecast_day'].isin(days)][col].mean()
                else:
                    val = np.nan
                row.append(val)
        rows.append(row)
    return rows

def draw(data, metric):
    # 🎯 自适应 13 列布局 (1个名字 + 4个季节*3个时效)
    w_f = 0.16
    w_rest = (1.0 - w_f) / 12
    x_pos = [0] + list(np.cumsum([w_f] + [w_rest]*12))
    x_centers = [(x_pos[i] + x_pos[i+1])/2 for i in range(13)]

    total_rows = 2 + len(data)
    # 画布拉宽到 18，防止文字重叠
    fig, ax = plt.subplots(figsize=(18, total_rows * 0.7 + 0.5), dpi=300)
    ax.set_xlim(0, 1); ax.set_ylim(0, total_rows); ax.axis('off')

    for i, row in enumerate(reversed(data)):
        y_c = i + 0.5
        ax.text(0.01, y_c, row[0], ha='left', va='center', weight='bold', size=12)
        for j, val in enumerate(row[1:]):
            ax.text(x_centers[j+1], y_c, f"{val:.1f}" if not np.isnan(val) else "-", ha='center', va='center', size=12)

    y_sub, y_super = len(data) + 0.5, len(data) + 1.5
    ax.text(x_centers[0], y_sub, "Study Region", ha='center', weight='bold', size=13)
    
    # 写入下层表头 (1-7d, 8-15d...)
    for j in range(12): 
        ax.text(x_centers[j+1], y_sub, PERIODS[j % 3], ha='center', weight='bold', size=11)

    # 写入上层表头 (四季) 并画下划线
    for k, season in enumerate(SEASONS):
        x_s = (x_pos[1 + k*3] + x_pos[4 + k*3]) / 2
        ax.text(x_s, y_super, season, ha='center', weight='bold', size=15)
        ax.plot([x_pos[1 + k*3]+0.01, x_pos[4 + k*3]-0.01], [len(data)+1, len(data)+1], 'k', lw=1)

    # 画外框实线
    ax.plot([0, 1], [total_rows, total_rows], 'k', lw=2)
    ax.plot([0, 1], [len(data), len(data)], 'k', lw=1)
    ax.plot([0, 1], [0, 0], 'k', lw=2)

    plt.title(f'EKE {metric} Evaluation (cm²/s²)', pad=20, fontsize=16, weight='bold')
    plt.savefig(os.path.join(PLOT_OUT_DIR, f'Table_EKE_{metric}_Combined.png'), bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    for m in ['Bias', 'MAE', 'RMSE']:
        d = get_data(m)
        if d: draw(d, m)
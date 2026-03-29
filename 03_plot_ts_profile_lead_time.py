# /data03/hjj/hjj/LFS-new/newwork/region/03_plot_ts_profile_lead_time.py
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR
import warnings

warnings.filterwarnings('ignore')

INPUT_CSV = os.path.join(DATA_OUT_DIR, 'TS_Profile_Evaluation_20230101-20241231.csv')
LAYERS = ['0-300m', '300-500m', '500-1000m']

def calc_bxp_stats(arr):
    """计算箱线图统计量"""
    arr = arr.dropna().values
    if len(arr) == 0: return None
    return {
        'med': np.percentile(arr, 50),
        'q1': np.percentile(arr, 25),
        'q3': np.percentile(arr, 75),
        'whislo': np.percentile(arr, 5),
        'whishi': np.percentile(arr, 95),
        'fliers': [] 
    }

def get_stats(var_type='T'):
    """提取统计量，跳过南海 (SCS)"""
    if not os.path.exists(INPUT_CSV): return None
    df = pd.read_csv(INPUT_CSV)
    all_days_stats = []
    
    for d in range(1, 31):
        df_d = df[df['forecast_day'] == d]
        day_res = {}
        # 遍历区域，跳过南海
        for r_k in REGIONS.keys():
            if r_k == 'SCS': continue 
            for ly in LAYERS:
                for m in ['Bias', 'RMSE', 'MAE']:
                    col = f"{r_k}_{var_type}_{m}_{ly}"
                    if col in df_d.columns:
                        day_res[col] = calc_bxp_stats(df_d[col])
        all_days_stats.append(day_res)
    return all_days_stats

def draw_ts_lead_time_panel(var_type, unit):
    """绘制 TS Profile (T/S) 趋势图 (不含南海)"""
    stats = get_stats(var_type)
    if not stats: return

    # 过滤掉南海后的区域列表
    active_regions = {k: v for k, v in REGIONS.items() if k != 'SCS'}
    n_reg = len(active_regions)
    
    # 🎯 优化：减小 figsize 宽度，设置 top 留出图例空间
    fig = plt.figure(figsize=(15, 4 * n_reg), dpi=200)
    # 🎯 优化：gridspec_kw 调整间距和顶部空间
    outer_gs = fig.add_gridspec(n_reg, 1, hspace=0.3, top=0.92)

    for idx, (r_k, r_i) in enumerate(active_regions.items()):
        inner_gs = outer_gs[idx].subgridspec(2, 1, hspace=0.08)
        ax_top = fig.add_subplot(inner_gs[0])
        ax_bot = fig.add_subplot(inner_gs[1])
        
        # 默认取代表层 0-300m
        ly = '0-300m' 
        b_box, r_box, m_box = [], [], []
        
        for d_idx, day_data in enumerate(stats):
            b_col, r_col, m_col = f"{r_k}_{var_type}_Bias_{ly}", f"{r_k}_{var_type}_RMSE_{ly}", f"{r_k}_{var_type}_MAE_{ly}"
            if day_data.get(b_col):
                b, r, m = day_data[b_col].copy(), day_data[r_col].copy(), day_data[m_col].copy()
                b['label'] = r['label'] = m['label'] = d_idx + 1
                b_box.append(b); r_box.append(r); m_box.append(m)

        # 绘制
        ax_top.bxp(b_box, positions=np.arange(1, 31), patch_artist=True, showfliers=False, widths=0.3,
                   boxprops={'facecolor': 'lightblue'}, medianprops={'color': 'red'})
        ax_top.bxp(r_box, positions=np.arange(1, 31) + 0.35, patch_artist=True, showfliers=False, widths=0.3,
                   boxprops={'facecolor': 'lightgreen'}, medianprops={'color': 'black'})
        ax_bot.bxp(m_box, positions=np.arange(1, 31) + 0.15, patch_artist=True, showfliers=False, widths=0.4,
                   boxprops={'facecolor': 'moccasin'}, medianprops={'color': 'darkorange'})

        # 美化
        for i, ax in enumerate([ax_top, ax_bot]):
            ax.set_xlim(0, 32); ax.set_xticks([1, 7, 15, 30])
            ax.grid(axis='y', ls=':', alpha=0.5)
            if i == 0:
                ax.axhline(0, color='k', ls='--', alpha=0.5)
                ax.set_title(f"{r_i['name']} - {ly}", weight='bold', size=13)
                ax.set_xticklabels([])
            else:
                ax.set_xticklabels(['1', '7', '15', '30'], weight='bold')

        ax_top.set_ylabel(f'Bias/RMSE {unit}', size=10)
        ax_bot.set_ylabel(f'MAE {unit}', size=10)

    # 图例
    leg = [Line2D([0], [0], color='red', marker='s', markerfacecolor='lightblue', label='Bias'),
           Line2D([0], [0], color='black', marker='s', markerfacecolor='lightgreen', label='RMSE'),
           Line2D([0], [0], color='darkorange', marker='s', markerfacecolor='moccasin', label='MAE')]
    # 🎯 优化： bbox_to_anchor 微调位置， frameon=False
    fig.legend(handles=leg, loc='upper center', bbox_to_anchor=(0.5, 0.98), ncol=3, fontsize=12, frameon=False)
    
    plt.suptitle(f'TS Profile {var_type} Lead Time Evaluation (No SCS)', fontsize=18, y=1.01, weight='bold')
    out_file = os.path.join(PLOT_OUT_DIR, f'Boxplot_TS_Profile_{var_type}_LeadTime.png')
    plt.savefig(out_file, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✅ TS Profile {var_type} 箱线图已生成: {out_file}")

if __name__ == '__main__':
    draw_ts_lead_time_panel('T', '(℃)')
    draw_ts_lead_time_panel('S', '(PSU)')
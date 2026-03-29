# /data03/hjj/hjj/LFS-new/newwork/region/03_plot_mld_lead_time.py
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR
import warnings

warnings.filterwarnings('ignore')

# 🎯 指向 MLD 统计总表
INPUT_CSV = os.path.join(DATA_OUT_DIR, 'MLD_Evaluation_20230101-20241231.csv')

def calc_bxp_stats(arr):
    """计算箱线图所需的统计量"""
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

def get_stats():
    """按天汇总 1-30 天的统计量"""
    if not os.path.exists(INPUT_CSV): return None
    df = pd.read_csv(INPUT_CSV)
    all_s = []
    for d in range(1, 31):
        df_d = df[df['forecast_day'] == d]
        res = {}
        for r_k in REGIONS.keys():
            for m in ['Bias', 'RMSE', 'MAE']:
                col = f'{r_k}_{m}'
                res[col] = calc_bxp_stats(df_d[col]) if col in df_d.columns else None
        all_s.append(res)
    return all_s

def draw_reg_panel(ax_top, ax_bot, stats, r_k, title, is_left=False):
    """为单个区域绘制上下两层的箱线图"""
    b_box, r_box, m_box = [], [], []
    for i, s in enumerate(stats):
        if s and s.get(f'{r_k}_Bias'):
            # 准备 Bias, RMSE, MAE 数据
            b, r, m = s[f'{r_k}_Bias'].copy(), s[f'{r_k}_RMSE'].copy(), s[f'{r_k}_MAE'].copy()
            for x in [b, r, m]: x['label'] = i + 1
            b_box.append(b); r_box.append(r); m_box.append(m)
    
    # 绘制上图 (Bias & RMSE)
    ax_top.bxp(b_box, positions=np.arange(1, 31), patch_artist=True, showfliers=False, widths=0.35,
               boxprops={'facecolor': 'lightblue'}, medianprops={'color': 'red'})
    ax_top.bxp(r_box, positions=np.arange(1, 31) + 0.4, patch_artist=True, showfliers=False, widths=0.35,
               boxprops={'facecolor': 'lightgreen'}, medianprops={'color': 'black'})
    
    # 绘制下图 (MAE)
    ax_bot.bxp(m_box, positions=np.arange(1, 31) + 0.2, patch_artist=True, showfliers=False, widths=0.4,
               boxprops={'facecolor': 'moccasin'}, medianprops={'color': 'darkorange'})
    
    # 坐标轴美化
    for ax_idx, ax in enumerate([ax_top, ax_bot]):
        ax.set_xlim(0, 32); ax.set_xticks([1.2, 7.2, 15.2, 30.2])
        ax.grid(axis='y', ls=':', alpha=0.5)
        if ax_idx == 0:
            ax.set_xticklabels([]) # 隐藏上图刻度文字
            ax.tick_params(axis='x', length=0)
        else:
            ax.set_xticklabels(['1', '7', '15', '30'], weight='bold')
            
    ax_top.set_title(title, weight='bold', size=14)
    ax_top.axhline(0, color='k', ls='--', alpha=0.5)
    if is_left:
        ax_top.set_ylabel('Bias & RMSE (m)', weight='bold')
        ax_bot.set_ylabel('MAE (m)', weight='bold')

def main():
    stats = get_stats()
    if not stats:
        print("❌ 无法获取统计数据，请检查 CSV 文件。")
        return

    fig = plt.figure(figsize=(20, 12), dpi=200)
    gs = fig.add_gridspec(2, 2, hspace=0.15, wspace=0.15)
    
    for idx, (r_k, r_i) in enumerate(REGIONS.items()):
        inner_gs = gs[idx // 2, idx % 2].subgridspec(2, 1, hspace=0.05)
        ax_t, ax_b = fig.add_subplot(inner_gs[0]), fig.add_subplot(inner_gs[1])
        draw_reg_panel(ax_t, ax_b, stats, r_k, r_i['name'], is_left=(idx % 2 == 0))
    
    # 添加图例
    leg = [Line2D([0], [0], color='red', marker='s', markerfacecolor='lightblue', label='Bias'),
           Line2D([0], [0], color='black', marker='s', markerfacecolor='lightgreen', label='RMSE'),
           Line2D([0], [0], color='darkorange', marker='s', markerfacecolor='moccasin', label='MAE')]
    fig.legend(handles=leg, loc='upper center', bbox_to_anchor=(0.5, 0.96), ncol=3, fontsize=13)
    
    plt.suptitle('Mixed Layer Depth (MLD) Forecast Error by Lead Time', fontsize=20, y=1.02, weight='bold')
    
    out_file = os.path.join(PLOT_OUT_DIR, 'Boxplot_MLD_LeadTime.png')
    plt.savefig(out_file, bbox_inches='tight')
    plt.close()
    print(f"✅ MLD 时效趋势箱线图已生成: {out_file}")

if __name__ == '__main__':
    main()
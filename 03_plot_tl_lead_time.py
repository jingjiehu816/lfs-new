# /data03/hjj/hjj/LFS-new/newwork/region/03_plot_tl_lead_time.py
import os, numpy as np, pandas as pd, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from config_regions import DATA_OUT_DIR, PLOT_OUT_DIR
import warnings
warnings.filterwarnings('ignore')

INPUT_CSV = os.path.join(DATA_OUT_DIR, 'Thermocline_Stats_Full.csv')
VARS = {
    'upper_depth': {'title': 'Upper Boundary Depth'},
    'lower_depth': {'title': 'Lower Boundary Depth'},
    'thickness':   {'title': 'Thermocline Thickness'}
}

def calc_bxp(arr):
    arr = arr.dropna().values
    return {'med': np.percentile(arr, 50), 'q1': np.percentile(arr, 25), 'q3': np.percentile(arr, 75),
            'whislo': np.percentile(arr, 5), 'whishi': np.percentile(arr, 95), 'fliers': []} if len(arr)>0 else None

def get_stats():
    if not os.path.exists(INPUT_CSV): 
        print(f"❌ 找不到 TL 数据文件: {INPUT_CSV}，请把文件复制过来！")
        return None
    df = pd.read_csv(INPUT_CSV)
    day_col = 'Day' if 'Day' in df.columns else 'forecast_day'
    all_s = []
    for d in range(1, 31):
        df_d = df[df[day_col] == d]
        res = {}
        for v in VARS.keys():
            # 这里自动兼容原表，如果有 MAE 就画，没有就跳过
            for m in ['Bias', 'RMSE', 'MAE']: 
                if f'{v}_{m}' in df_d.columns:
                    res[f'{v}_{m}'] = calc_bxp(df_d[f'{v}_{m}'])
        all_s.append(res)
    return all_s

def main():
    stats = get_stats()
    if not stats: return
    
    # 修复 matplotlib 报错，并缩小横向间距
    fig, axes = plt.subplots(2, 3, figsize=(22, 10), gridspec_kw={'hspace': 0.1, 'wspace': 0.15})
    
    for i, (v_k, v_i) in enumerate(VARS.items()):
        # Top: Bias/RMSE
        b_box, r_box, m_box = [], [], []
        for d, s in enumerate(stats):
            if s and f'{v_k}_Bias' in s and s[f'{v_k}_Bias']:
                b, r = s[f'{v_k}_Bias'].copy(), s[f'{v_k}_RMSE'].copy()
                b['label'] = r['label'] = d+1
                b_box.append(b); r_box.append(r)
            if s and f'{v_k}_MAE' in s and s[f'{v_k}_MAE']:
                m = s[f'{v_k}_MAE'].copy()
                m['label'] = d+1
                m_box.append(m)
                
        axes[0,i].bxp(b_box, positions=np.arange(1,31), patch_artist=True, showfliers=False, widths=0.35, boxprops={'facecolor':'lightblue'}, medianprops={'color':'red'})
        axes[0,i].bxp(r_box, positions=np.arange(1,31)+0.4, patch_artist=True, showfliers=False, widths=0.35, boxprops={'facecolor':'lightgreen'}, medianprops={'color':'black'})
        axes[0,i].set_title(v_i['title'], weight='bold', size=15)
        
        # Bottom: MAE
        if m_box:
            axes[1,i].bxp(m_box, positions=np.arange(1,31)+0.2, patch_artist=True, showfliers=False, widths=0.4, boxprops={'facecolor':'moccasin'}, medianprops={'color':'darkorange'})
        
        for ax_idx, ax in enumerate([axes[0,i], axes[1,i]]):
            ax.set_xlim(0, 32); ax.set_xticks([1.2, 7.2, 15.2, 30.2])
            ax.grid(axis='y', ls=':', alpha=0.5)
            ax.axhline(0, color='k', ls='--', alpha=0.5)
            # 隐藏上图横坐标，只保留下图横坐标
            if ax_idx == 0:
                ax.set_xticklabels([])
                ax.tick_params(axis='x', length=0)
            else:
                ax.set_xticklabels(['1', '7', '15', '30'], weight='bold')

    axes[0,0].set_ylabel('Bias & RMSE (m)', weight='bold')
    axes[1,0].set_ylabel('MAE (m)', weight='bold')
    
    leg = [Line2D([0],[0], color='red', marker='s', markerfacecolor='lightblue', label='Bias'),
           Line2D([0],[0], color='black', marker='s', markerfacecolor='lightgreen', label='RMSE'),
           Line2D([0],[0], color='darkorange', marker='s', markerfacecolor='moccasin', label='MAE')]
    fig.legend(handles=leg, loc='upper center', bbox_to_anchor=(0.5, 0.94), ncol=3, fontsize=12)
    
    plt.savefig(os.path.join(PLOT_OUT_DIR, 'Boxplot_Thermocline_LeadTime.png'), dpi=300, bbox_inches='tight')

if __name__ == '__main__': main()
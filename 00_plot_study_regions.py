# /data03/hjj/hjj/LFS-new/newwork/region/00_plot_study_regions.py
import os
import matplotlib.pyplot as plt
import warnings
from config_regions import REGIONS, PLOT_OUT_DIR

warnings.filterwarnings('ignore')

def main():
    os.makedirs(PLOT_OUT_DIR, exist_ok=True)
    
    # 创建画布
    fig = plt.figure(figsize=(12, 8), dpi=300)
    
    # =======================================================
    # 智能地图引擎检测：尝试加载 cartopy
    # =======================================================
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        
        ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=180))
        # 添加真实地球要素
        ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='k', zorder=1)
        ax.add_feature(cfeature.OCEAN, facecolor='aliceblue', zorder=0)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5, zorder=2)
        ax.set_extent([95, 185, -5, 55], crs=ccrs.PlateCarree())
        
        gl = ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False
        use_cartopy = True
        
    except ImportError:
        print("⚠️ 提示：未检测到 cartopy 库，将绘制基础坐标系示意图。")
        ax = plt.axes()
        ax.set_facecolor('aliceblue')
        ax.set_xlim(95, 185)
        ax.set_ylim(-5, 55)
        ax.grid(linestyle='--', alpha=0.5)
        ax.set_xlabel('Longitude', weight='bold')
        ax.set_ylabel('Latitude', weight='bold')
        use_cartopy = False

    # =======================================================
    # 🎯 核心逻辑：读取新版 [min, max] 坐标，自动补齐成闭合矩形的 5 个顶点
    # =======================================================
    for r_key, r_info in REGIONS.items():
        lon_min, lon_max = r_info['lon']
        lat_min, lat_max = r_info['lat']
        
        # 自动生成：左下 -> 右下 -> 右上 -> 左上 -> 回到左下
        box_lon = [lon_min, lon_max, lon_max, lon_min, lon_min]
        box_lat = [lat_min, lat_min, lat_max, lat_max, lat_min]
        
        kwargs = {
            'color': r_info['color'],
            'linestyle': r_info.get('linestyle', '-'),
            'linewidth': 3.0,
            'label': r_info['name'],
            'zorder': 3
        }
        
        if use_cartopy:
            kwargs['transform'] = ccrs.PlateCarree()
            
        ax.plot(box_lon, box_lat, **kwargs)
        
        # 添加文字标签 (放在区域左上角)
        text_x = lon_min + 1.5
        text_y = lat_max - 2.5
        
        if use_cartopy:
            ax.text(text_x, text_y, r_info['short_name'], color=r_info['color'], 
                    fontsize=14, weight='bold', transform=ccrs.PlateCarree(),
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=2), zorder=4)
        else:
            ax.text(text_x, text_y, r_info['short_name'], color=r_info['color'], 
                    fontsize=14, weight='bold',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=2), zorder=4)

    plt.legend(loc='lower right', fontsize=12, framealpha=0.9)
    plt.title('LFS Evaluation Study Regions', fontsize=18, weight='bold', pad=15)
    
    out_file = os.path.join(PLOT_OUT_DIR, '00_Study_Regions_Map.png')
    plt.savefig(out_file, bbox_inches='tight')
    print(f"✅ 区域示意图已成功生成: {out_file}")
    plt.close()

if __name__ == '__main__':
    main()
# /data03/hjj/hjj/LFS-new/newwork/region/04_plot_eke_spatial.py
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import os
import numpy as np
import warnings
from config_regions import REGIONS, DATA_OUT_DIR, PLOT_OUT_DIR

warnings.filterwarnings('ignore')

# 🎯 辅助函数：自动计算色标上限
def get_vmax(da, p=98):
    vals = da.values.flatten()
    vals = vals[~np.isnan(vals)]
    return np.percentile(np.abs(vals), p) if len(vals) > 0 else 1.0

def main():
    os.makedirs(PLOT_OUT_DIR, exist_ok=True)
    
    # 🎯 严格匹配你 data 目录下的文件命名
    f_summer = os.path.join(DATA_OUT_DIR, 'Spatial_EKE_Map_Summer.nc')
    f_winter = os.path.join(DATA_OUT_DIR, 'Spatial_EKE_Map_Winter.nc')
    
    if not (os.path.exists(f_summer) and os.path.exists(f_winter)):
        print(f"❌ 找不到空间场 NC 文件，请确认 Stage 1 已生成 Summer/Winter 地图。")
        return

    ds_s = xr.open_dataset(f_summer)
    ds_w = xr.open_dataset(f_winter)

    for reg_key, reg_info in REGIONS.items():
        print(f"正在渲染 {reg_info['name']} 的 2x3 空间分布图...")
        
        # 根据区域跨度自动调整画布比例
        lat_min, lat_max = reg_info['lat']
        lon_min, lon_max = reg_info['lon']
        asp = (lat_max - lat_min) / (lon_max - lon_min)
        figsize = (13, 11) if asp > 0.8 else (18, 9)
        cbar_pad = 0.07 if asp > 0.8 else 0.11

        fig, axes = plt.subplots(2, 3, figsize=figsize, 
                                 subplot_kw={'projection': ccrs.PlateCarree()}, 
                                 gridspec_kw={'wspace': 0.03, 'hspace': 0.05}, dpi=150)
        
        im_main, im_bias = None, None
        
        # 计算该区域的动态 vmax
        v_eke = max(get_vmax(ds_s['mod_eke'].sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))),
                    get_vmax(ds_s['obs_eke'].sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max))))
        v_bias = get_vmax(ds_s['mean_bias'].sel(lat=slice(lat_min, lat_max), lon=slice(lon_min, lon_max)))

        for row, season_name, ds in zip([0, 1], ['Summer', 'Winter'], [ds_s, ds_w]):
            # 截取子区域（多扩 2 度）
            sub = ds.sel(lat=slice(lat_min - 2, lat_max + 2), lon=slice(lon_min - 2, lon_max + 2))
            
            panels = [
                (0, sub['mod_eke'],  'YlOrRd', 0, v_eke, 'Forecast (Mod)'),
                (1, sub['obs_eke'],  'YlOrRd', 0, v_eke, 'Observation (Obs)'),
                (2, sub['mean_bias'], 'RdBu_r', -v_bias, v_bias, 'Bias (Mod - Obs)')
            ]
            
            for col, data, cmap, vmin, vmax, title_suffix in panels:
                ax = axes[row, col]
                ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())
                ax.add_feature(cfeature.LAND, facecolor='lightgray', zorder=2)
                ax.coastlines(linewidth=0.8, zorder=3)
                
                im = data.plot(ax=ax, transform=ccrs.PlateCarree(), cmap=cmap, 
                               vmin=vmin, vmax=vmax, add_colorbar=False, zorder=1)
                
                if col == 0 and row == 0: im_main = im
                if col == 2 and row == 0: im_bias = im
                
                if row == 0: ax.set_title(title_suffix, fontsize=15, pad=10, weight='bold')
                else: ax.set_title("")
                
                ax.text(0.03, 0.92, season_name, transform=ax.transAxes, fontsize=12, 
                        weight='bold', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

                gl = ax.gridlines(draw_labels=True, linewidth=0, color='none')
                gl.top_labels = gl.right_labels = False
                if col > 0: gl.left_labels = False
                if row == 0: gl.bottom_labels = False
                gl.xformatter, gl.yformatter = LONGITUDE_FORMATTER, LATITUDE_FORMATTER

        # 底部色标
        cbar_m = fig.colorbar(im_main, ax=axes[:, 0:2].ravel().tolist(), orientation='horizontal', shrink=0.8, pad=cbar_pad, aspect=40)
        cbar_m.set_label('Absolute EKE ($cm^2/s^2$)', fontsize=12, weight='bold')
        
        cbar_b = fig.colorbar(im_bias, ax=axes[:, 2].ravel().tolist(), orientation='horizontal', shrink=0.8, pad=cbar_pad, aspect=20)
        cbar_b.set_label('EKE Bias ($cm^2/s^2$)', fontsize=12, weight='bold')

        plt.suptitle(f'EKE Spatial Distribution: {reg_info["name"]}', fontsize=16, y=0.98, weight='bold')
        
        # 🎯 保持原有命名覆盖
        out_file = os.path.join(PLOT_OUT_DIR, f'Spatial_EKE_Bias_{reg_key}_Combined.png')
        plt.savefig(out_file, bbox_inches='tight', dpi=300)
        plt.close()
        print(f"✅ 已生成 2x3 分布图: {out_file}")

    ds_s.close(); ds_w.close()

if __name__ == '__main__':
    main()
# /data03/hjj/hjj/LFS-new/newwork/region/01_calc_tl.py
import os, glob, re, warnings
import numpy as np, pandas as pd, xarray as xr
import multiprocessing as mp
from config_regions import REGIONS, DATA_OUT_DIR, CPU_NUM

warnings.filterwarnings('ignore')

# 🎯 路径指向你之前脚本 SAVE_ROOT 定义的目录
INPUT_ROOT = '/data03/hjj/hjj/LFS-new/TL/mod/' 

def process_single_case(case_dir):
    try:
        # 解析 case_20230101_10km 得到 20230101
        case_date_str = os.path.basename(case_dir).split('_')[1]
    except: 
        return []

    # 🎯 修改点 1：匹配你旧脚本生成的文件名 thermo_dayXX_YYYY-MM-DD.nc
    nc_files = glob.glob(os.path.join(case_dir, 'thermo_day*.nc'))
    if not nc_files:
        return []

    results = []
    for nc_file in nc_files:
        try:
            fname = os.path.basename(nc_file)
            # 提取 day01 中的 1
            day_match = re.search(r'day(\d+)', fname)
            if not day_match: continue
            
            forecast_day = int(day_match.group(1))
            rec = {'case_date': case_date_str, 'forecast_day': forecast_day}

            with xr.open_dataset(nc_file, decode_times=False) as ds:
                # 🎯 修改点 2：匹配你旧脚本保存的变量名 diff_xxx
                mapping = {
                    'thickness': 'diff_thickness',
                    'upper_depth': 'diff_upper_depth',
                    'lower_depth': 'diff_lower_depth'
                }
                
                vars_to_calc = {}
                for v_key, v_nc in mapping.items():
                    if v_nc in ds:
                        vars_to_calc[v_key] = ds[v_nc].squeeze().values
                
                if not vars_to_calc: continue
                
                lat = ds['lat'].squeeze().values
                lon = ds['lon'].squeeze().values

            lon_2d, lat_2d = np.meshgrid(lon, lat) if lon.ndim == 1 else (lon, lat)
            w_2d = np.cos(np.radians(lat_2d))

            for r_key, r_info in REGIONS.items():
                lon_norm = np.mod(lon_2d, 360)
                mask = (lon_norm >= r_info['lon'][0]) & (lon_norm <= r_info['lon'][1]) & \
                       (lat_2d >= r_info['lat'][0]) & (lat_2d <= r_info['lat'][1])

                for var_name, diff_data in vars_to_calc.items():
                    valid_mask = mask & ~np.isnan(diff_data)
                    if np.sum(valid_mask) > 0:
                        w, d = w_2d[valid_mask], diff_data[valid_mask]
                        sw = np.sum(w)
                        rec[f'{r_key}_{var_name}_Bias'] = np.sum(d * w) / sw
                        rec[f'{r_key}_{var_name}_RMSE'] = np.sqrt(np.sum((d**2) * w) / sw)
                        rec[f'{r_key}_{var_name}_MAE']  = np.sum(np.abs(d) * w) / sw
                    else:
                        rec[f'{r_key}_{var_name}_Bias'] = np.nan
                        rec[f'{r_key}_{var_name}_RMSE'] = np.nan
                        rec[f'{r_key}_{var_name}_MAE']  = np.nan

            results.append(rec)
        except Exception: 
            continue
    return results

def main():
    all_case_dirs = sorted(glob.glob(os.path.join(INPUT_ROOT, "case_*_10km")))
    total = len(all_case_dirs)
    if total == 0: 
        print(f"❌ 错误：在 {INPUT_ROOT} 下未找到任何 case 目录！")
        return

    final_results = []
    print(f"🚀 开始扫描并汇总 {total} 个 Case 的分区域统计...")
    
    with mp.Pool(CPU_NUM) as pool:
        for i, res in enumerate(pool.imap_unordered(process_single_case, all_case_dirs)):
            if res: 
                final_results.extend(res)
            if (i + 1) % max(int(total / 10), 1) == 0 or (i + 1) == total:
                print(f"    -> 进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)", flush=True)

    if not final_results:
        print("❌ 错误：未收集到数据。请确认 NC 文件包含 diff_thickness 等变量。")
        return

    df = pd.DataFrame(final_results)
    
    # 排序并保存
    sort_cols = [c for c in ['case_date', 'forecast_day'] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols)

    csv_out = os.path.join(DATA_OUT_DIR, 'Thermocline_Evaluation_20230101-20241231.csv')
    df.to_csv(csv_out, index=False)
    print(f"✅ 分区域 TL 汇总表已生成: {csv_out}")

if __name__ == "__main__": 
    main()
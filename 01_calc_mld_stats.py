# /data03/hjj/hjj/LFS-new/newwork/region/01_calc_mld_stats.py
# /data03/hjj/hjj/LFS-new/newwork/region/01_calc_mld_stats.py
import os, glob, re, warnings
import numpy as np, pandas as pd, xarray as xr
import multiprocessing as mp
from config_regions import REGIONS, DATA_OUT_DIR, CPU_NUM

warnings.filterwarnings('ignore')

INPUT_ROOT = '/data03/hjj/hjj/LFS-new/mld2/mod/'

def process_single_case(case_dir):
    try:
        case_date_str = os.path.basename(case_dir).split('_')[1]
    except:
        return []

    nc_files = glob.glob(os.path.join(case_dir, 'mld_day*.nc'))
    results = []
    
    for nc_file in nc_files:
        try:
            fname = os.path.basename(nc_file)
            # 🎯 修复 1：去掉正则里的下划线限制，只要有 day 加数字就能匹配！
            day_match = re.search(r'day(\d+)', fname)
            if not day_match: continue
            
            forecast_day = int(day_match.group(1))
            rec = {'case_date': case_date_str, 'forecast_day': forecast_day}

            with xr.open_dataset(nc_file, decode_times=False) as ds:
                diff = ds['diff'].squeeze().values
                lat = ds['lat'].squeeze().values
                lon = ds['lon'].squeeze().values

            # 🎯 修复 2：智能判断经纬度维度！一维才组装，二维直接用！
            if lon.ndim == 1 and lat.ndim == 1:
                lon_2d, lat_2d = np.meshgrid(lon, lat)
            else:
                lon_2d, lat_2d = lon, lat

            # 🎯 修复 3：矩阵形状防崩溃校验
            if lon_2d.shape != diff.shape:
                if lon_2d.shape == diff.T.shape:
                    diff = diff.T
                else:
                    print(f"\n[❌ 形状不匹配跳过] {fname} diff:{diff.shape} 经纬度:{lon_2d.shape}")
                    continue

            w_2d = np.cos(np.radians(lat_2d))

            for r_key, r_info in REGIONS.items():
                bounds = r_info
                lon_norm = np.mod(lon_2d, 360)
                mask = (lon_norm >= bounds['lon'][0]) & (lon_norm <= bounds['lon'][1]) & \
                       (lat_2d >= bounds['lat'][0]) & (lat_2d <= bounds['lat'][1])

                valid_mask = mask & ~np.isnan(diff)
                
                if np.sum(valid_mask) > 0:
                    w = w_2d[valid_mask]
                    d = diff[valid_mask]
                    sw = np.sum(w)
                    if sw > 0:
                        rec[f'{r_key}_Bias'] = np.sum(d * w) / sw
                        rec[f'{r_key}_MAE']  = np.sum(np.abs(d) * w) / sw
                        rec[f'{r_key}_RMSE'] = np.sqrt(np.sum((d**2) * w) / sw)
                    else:
                        rec[f'{r_key}_Bias'] = rec[f'{r_key}_MAE'] = rec[f'{r_key}_RMSE'] = np.nan
                else:
                    rec[f'{r_key}_Bias'] = rec[f'{r_key}_MAE'] = rec[f'{r_key}_RMSE'] = np.nan

            results.append(rec)
        except Exception as e:
            print(f"\n[⚠️ 文件处理报错] {fname}: {e}")
            continue
            
    return results

def main():
    all_case_dirs = sorted(glob.glob(os.path.join(INPUT_ROOT, "case_*_10km")))
    total = len(all_case_dirs)
    if total == 0: 
        print("❌ 未在目录找到任何 case_*_10km 文件夹！")
        return
    
    final_results = []
    with mp.Pool(CPU_NUM) as pool:
        for i, res in enumerate(pool.imap_unordered(process_single_case, all_case_dirs)):
            if res: final_results.extend(res)
            if (i + 1) % max(int(total / 10), 1) == 0 or (i + 1) == total:
                print(f"    -> MLD 进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)", flush=True)

    # 🎯 终极诊断：告诉你到底是 0 行，还是全是 NaN！
    if not final_results:
        print("\n❌ 严重警告：成功扫描了文件，但没有生成哪怕 1 行数据！请检查 nc 文件里是不是根本没有 diff 变量，或者 day 数字匹配失败！")
        return

    df = pd.DataFrame(final_results).sort_values(by=['case_date', 'forecast_day'])
    
    # 检查是否除了日期外全是 NaN
    data_cols = [c for c in df.columns if c not in ['case_date', 'forecast_day']]
    if df[data_cols].isna().all().all():
        print("\n❌ 严重警告：CSV 虽然生成了，但是计算出来的偏差【全都是 NaN】！")
        print("    原因极大概率是：你划定的四个海区经纬度范围里，所有的 diff 数据都是缺测值。")
    
    csv_out = os.path.join(DATA_OUT_DIR, 'MLD_Evaluation_20230101-20241231.csv')
    df.to_csv(csv_out, index=False)
    print(f"\n🎉 MLD 数据已保存至: {csv_out} (总计成功提取 {len(df)} 行有效数据记录！)")

if __name__ == "__main__": main()
# /data03/hjj/hjj/LFS-new/newwork/region/01_calc_eke.py
import os, glob, time, random, warnings
import numpy as np, pandas as pd, xarray as xr
import multiprocessing as mp
from datetime import datetime, timedelta

# 🎯 导入终极配置
from config_regions import CPU_NUM, START_DATE, END_DATE, DATA_OUT_DIR, REGIONS

warnings.filterwarnings('ignore')

# --- 本地配置 ---
MAX_WAIT_SECONDS = 5
OBS_BASE_PATH = '/data04/LFS/diag/OSCAR/'
MOD_BASE_PATH = '/data04/LFS/LFSv1.0/ext_fct/10km/'
TMP_NC_PATH = os.path.join(DATA_OUT_DIR, 'tmp_2d')
CLIM_FILE = '/data03/hjj/hjj/LFS-new/newwork/OSCAR_clim_12months_FINAL.nc'
os.makedirs(TMP_NC_PATH, exist_ok=True)

global_clim, global_grid = {}, {}

def init_worker(clim_dict, grid_dict):
    global global_clim, global_grid
    global_clim, global_grid = clim_dict, grid_dict

def get_region_mask(lon_2d, lat_2d, bounds):
    # 使用统一的 [min, max] 索引
    return (lon_2d >= bounds['lon'][0]) & (lon_2d <= bounds['lon'][1]) & \
           (lat_2d >= bounds['lat'][0]) & (lat_2d <= bounds['lat'][1])

def calc_eke(u, v, u_clim, v_clim):
    return 0.5 * ((u - u_clim)**2 + (v - v_clim)**2) * 10000 

def process_single_case(case_dir):
    time.sleep(random.uniform(0, MAX_WAIT_SECONDS))
    try:
        case_date = datetime.strptime(os.path.basename(case_dir).split('_')[1], '%Y%m%d')
    except: return None

    # 标准四季划分
    month = case_date.month
    if month in [3, 4, 5]: season = 'Spring'
    elif month in [6, 7, 8]: season = 'Summer'
    elif month in [9, 10, 11]: season = 'Autumn'
    else: season = 'Winter'

    results_1d = []
    grid_shape = global_grid['shape']
    sum_bias, sum_mse, sum_obs, sum_mod, valid_cnt = (np.zeros(grid_shape) for _ in range(5))

    for day_idx in range(1, 31):
        fcst_date = case_date + timedelta(days=day_idx - 1)
        valid_month_idx = fcst_date.month - 1
        
        obs_f = os.path.join(OBS_BASE_PATH, f"oscar_currents_interim_{fcst_date.strftime('%Y%m%d')}.nc")
        case_mod_d_str = fcst_date.strftime('%Y-%m-%d')
        uu_f = os.path.join(case_dir, f"uu-{case_mod_d_str}_10km.nc")
        vv_f = os.path.join(case_dir, f"vv-{case_mod_d_str}_10km.nc")

        if not (os.path.exists(obs_f) and os.path.exists(uu_f) and os.path.exists(vv_f)): continue

        try:
            with xr.open_dataset(obs_f, decode_times=False) as ds_o:
                obs_u, obs_v = ds_o['u'][0].values, ds_o['v'][0].values
                if obs_u.shape != grid_shape: obs_u, obs_v = obs_u.T, obs_v.T
            
            with xr.open_dataset(uu_f, decode_times=False) as ds_u, \
                 xr.open_dataset(vv_f, decode_times=False) as ds_v:
                mod_u = ds_u['uu'][0, 0].interp(lat=global_grid['lat'], lon=global_grid['lon']).values
                mod_v = ds_v['vv'][0, 0].interp(lat=global_grid['lat'], lon=global_grid['lon']).values

            u_c, v_c = global_clim['u'][valid_month_idx], global_clim['v'][valid_month_idx]
            obs_eke = calc_eke(obs_u, obs_v, u_c, v_c)
            mod_eke = calc_eke(mod_u, mod_v, u_c, v_c)
            bias_2d = mod_eke - obs_eke
            
            m_val = ~np.isnan(bias_2d)
            sum_bias[m_val] += bias_2d[m_val]
            sum_mse[m_val]  += bias_2d[m_val]**2
            sum_obs[m_val]  += obs_eke[m_val]
            sum_mod[m_val]  += mod_eke[m_val]
            valid_cnt[m_val] += 1

            rec = {'season': season, 'case_date': case_date.strftime('%Y%m%d'), 'forecast_day': day_idx}
            for reg_name, reg_mask in global_grid['masks'].items():
                m = m_val & reg_mask
                if np.sum(m) > 0:
                    rec[f'{reg_name}_obs_eke'] = np.nanmean(obs_eke[m])
                    rec[f'{reg_name}_mod_eke'] = np.nanmean(mod_eke[m])
                    rec[f'{reg_name}_Bias']    = np.nanmean(bias_2d[m])
                    rec[f'{reg_name}_RMSE']    = np.sqrt(np.nanmean(bias_2d[m]**2))
                    rec[f'{reg_name}_MAE']     = np.nanmean(np.abs(bias_2d[m]))
                else:
                    rec[f'{reg_name}_obs_eke'] = np.nan
            results_1d.append(rec)
        except: continue
            
    if results_1d:
        with np.errstate(invalid='ignore'):
            ds_out = xr.Dataset({
                'mean_bias': (['lat', 'lon'], sum_bias / valid_cnt),
                'rmse':      (['lat', 'lon'], np.sqrt(sum_mse / valid_cnt)),
                'obs_eke':   (['lat', 'lon'], sum_obs / valid_cnt),
                'mod_eke':   (['lat', 'lon'], sum_mod / valid_cnt),
                'count':     (['lat', 'lon'], valid_cnt)
            }, coords={'lat': global_grid['lat'], 'lon': global_grid['lon']})
            # 临时保存单个 case 的空间场
            ds_out.to_netcdf(os.path.join(TMP_NC_PATH, f"eke_2d_{case_date.strftime('%Y%m%d')}_{season}.nc"))

    return results_1d

def main():
    ds_clim = xr.open_dataset(CLIM_FILE).load()
    lon_arr, lat_arr = ds_clim['lon'].values, ds_clim['lat'].values
    lon_2d, lat_2d = np.meshgrid(lon_arr, lat_arr)
    
    clim_dict = {'u': ds_clim['u'].values, 'v': ds_clim['v'].values}
    grid_dict = {
        'lon': lon_arr, 'lat': lat_arr, 'shape': (len(lat_arr), len(lon_arr)),
        'masks': {v['short_name']: get_region_mask(lon_2d, lat_2d, v) for k, v in REGIONS.items()}
    }
    ds_clim.close()

    all_cases = sorted(glob.glob(os.path.join(MOD_BASE_PATH, "case_*_10km")))
    target_cases = [c for c in all_cases if START_DATE <= os.path.basename(c).split('_')[1] <= END_DATE]
    if not target_cases: return

    seasons = ['Spring', 'Summer', 'Autumn', 'Winter']
    # 建立主进程累加器，避免最后使用 mfdataset
    accumulators = {s: {
        'mean_bias': np.zeros(grid_dict['shape']),
        'rmse_sq': np.zeros(grid_dict['shape']),
        'obs_eke': np.zeros(grid_dict['shape']),
        'mod_eke': np.zeros(grid_dict['shape']),
        'count': np.zeros(grid_dict['shape'])
    } for s in seasons}

    final_1d = []
    total = len(target_cases)
    with mp.Pool(CPU_NUM, initializer=init_worker, initargs=(clim_dict, grid_dict)) as pool:
        for i, res in enumerate(pool.imap_unordered(process_single_case, target_cases)):
            if res: 
                final_1d.extend(res)
                # 实时读取生成的临时 NC 并累加，然后立即删除
                tmp_files = glob.glob(os.path.join(TMP_NC_PATH, "*.nc"))
                for f in tmp_files:
                    s_name = f.split('_')[-1].replace('.nc', '')
                    with xr.open_dataset(f) as ds_tmp:
                        cnt = ds_tmp['count'].values
                        accumulators[s_name]['mean_bias'] += ds_tmp['mean_bias'].values * cnt
                        accumulators[s_name]['rmse_sq'] += (ds_tmp['rmse'].values**2) * cnt
                        accumulators[s_name]['obs_eke'] += ds_tmp['obs_eke'].values * cnt
                        accumulators[s_name]['mod_eke'] += ds_tmp['mod_eke'].values * cnt
                        accumulators[s_name]['count'] += cnt
                    os.remove(f)

            if (i + 1) % max(int(total / 10), 1) == 0 or (i + 1) == total:
                print(f"    -> EKE 进度: {i+1}/{total} ({(i+1)/total*100:.1f}%)", flush=True)

    # 1. 保存 1D 统计 CSV
    df = pd.DataFrame(final_1d).dropna(subset=['case_date'])
    df.to_csv(os.path.join(DATA_OUT_DIR, 'EKE_Evaluation_20230101-20241231.csv'), index=False)

    # 2. 输出 4 个季节的 CSV 供绘图
    for s in seasons:
        df_s = df[df['season'] == s]
        if not df_s.empty:
            df_s.to_csv(os.path.join(DATA_OUT_DIR, f'EKE_TimeSeries_{s}.csv'), index=False)

    # 3. 输出季节空间场 NC
    print("    -> 正在输出季节空间分布图...", flush=True)
    for s in seasons:
        acc = accumulators[s]
        valid = acc['count'] > 0
        ds_final = xr.Dataset({
            'mean_bias': (['lat', 'lon'], np.where(valid, acc['mean_bias'] / acc['count'], np.nan)),
            'rmse':      (['lat', 'lon'], np.where(valid, np.sqrt(acc['rmse_sq'] / acc['count']), np.nan)),
            'obs_eke':   (['lat', 'lon'], np.where(valid, acc['obs_eke'] / acc['count'], np.nan)),
            'mod_eke':   (['lat', 'lon'], np.where(valid, acc['mod_eke'] / acc['count'], np.nan)),
            'count':     (['lat', 'lon'], acc['count'])
        }, coords={'lat': lat_arr, 'lon': lon_arr})
        ds_final.to_netcdf(os.path.join(DATA_OUT_DIR, f'Spatial_EKE_Map_{s}.nc'))

    if os.path.exists(TMP_NC_PATH): os.rmdir(TMP_NC_PATH)
    print("✅ EKE 计算与空间场输出全部完成!")

if __name__ == "__main__": main()
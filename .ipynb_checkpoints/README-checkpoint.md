#LFS-Evaluation-Pipeline 是一套专为 **LICOM Forecast System (LFS) v1.0** 全球海洋预报系统设计的自动化评估工具集。该工具集严格遵循 **OceanPredict IV-TT Class 4** 评估框架，实现了对模式预报误差的快速提取、统计与多维度可视化。

## 🌟 核心功能

- **多变量覆盖**：支持海表流速 (Currents)、涡动能 (EKE)、海表温盐 (SST/SSS)、混合层深度 (MLD)、温跃层结构 (Thermocline) 及 TS 剖面。
- **标准化指标**：全流程计算 Bias、MAE、RMSE。
- **精细化分区**：内置南海 (SCS)、黑潮主轴 (Kuroshio)、黑潮延伸体 (KE) 及西太平洋 (WPac) 的自动化掩膜提取。
- **工业级计算**：基于 `multiprocessing` 的并行引擎与 `xarray` 内存优化。

## 📁 目录结构

* `config_regions.py`：全局坐标、路径及并行核心配置
* `run_pipeline.py`：总控脚本（一键执行全流程）
* `00_plot_study_regions.py`：绘制研究区域地图
* `01_calc_*.py`：数据生产脚本（并行提取误差）
* `02_plot_*_table.py`：绘制三段式评估表格 (Bias/MAE/RMSE)
* `03_plot_*_lead_time.py`：绘制预报时效趋势箱线图
* `04_plot_eke_spatial.py`：绘制空间分布图

## 🚀 快速上手

建议在终端使用 `nohup` 挂起运行：
nohup python run_pipeline.py > evaluate.log 2>&1 &

## 📧 作者
虎靖杰 (Hu Jingjie)

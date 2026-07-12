"""demo_malta_worldpop.py - WorldPop raster challenge: share of 65+
among the k nearest neighbours, Malta 2020. Needs: pip install rasterio
and the unzipped WorldPop tifs in ./malta/"""
import pandas as pd
from equipop import project_to_metric, snap_to_grid, run_knn_stats
from equipop.raster import rasters_to_points
from equipop.cells import CellData

df = rasters_to_points({
    "pop": "malta/mlt_t_*_2020_CN_100m_R2025A_v1.tif",
    "old": "malta/mlt_t_{65,70,75,80,85,90}_2020_CN_100m_R2025A_v1.tif"})
df = snap_to_grid(project_to_metric(df, lat_col="lat", lon_col="lon"),
                  unit_size=100)                     # auto: UTM 33N
g = df.groupby(["E_grid", "N_grid"], as_index=False)[["pop", "old"]].sum()

cd = CellData(E=g["E_grid"].to_numpy(), N=g["N_grid"].to_numpy(),
              n=g["pop"].to_numpy(), binary_sums={"old65": g["old"].to_numpy()},
              value_arrays={}, unit_size=100)
res = run_knn_stats(cd, k_values=[12,25,50,100,200,400,800,1600,3200,6400,12800],
                    stats={"old65": ["ratio"]})
res.to_csv("malta_65plus_output.csv", index=False)
print(res.filter(regex="R_old65").describe().round(3).to_string())

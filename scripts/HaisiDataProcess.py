# -*- coding:utf-8 -*-
import shapefile

fpath = '/Users/chuwenjie/PycharmProjects/MultiViewAgent/data/PDNA_HTI_2010_BuildingDamageAssessment/PDNA_HTI_2010_Atlas_of_Building_Damage_Assessment_UNOSAT_JRC_WB_v2.shp'
sf = shapefile.Reader(fpath,encoding='latin-1')
# sf.load_shx('/Users/chuwenjie/PycharmProjects/MultiViewAgent/data/PDNA_HTI_2010_BuildingDamageAssessment/PDNA_HTI_2010_Atlas_of_Building_Damage_Assessment_UNOSAT_JRC_WB_v2.shx')
# sf.load_dbf('/Users/chuwenjie/PycharmProjects/MultiViewAgent/data/PDNA_HTI_2010_BuildingDamageAssessment/PDNA_HTI_2010_Atlas_of_Building_Damage_Assessment_UNOSAT_JRC_WB_v2.dbf')
shapes = sf.shapes()
shape = sf.shape(0)
# print(shape.parts)
# print(shape.points)
# print(shape.shapeType)
# print(shape.shapeTypeName)
bx = sf.records()
Records = []
recd = []
for rec in bx:
    for i in rec:
        recd.append(i)
    Records.append(recd)
    print(recd)
    recd.clear()




# # %matplotlib inline
# import matplotlib
# import shapely, geopandas, fiona
# import seaborn as sns
# from fiona.crs import from_epsg, from_string
#
#
# shp_df = geopandas.GeoDataFrame.from_file(tpath)
# shp_df.head()
# shp_df.plot()






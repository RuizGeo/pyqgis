try:
    from osgeo import ogr
except:
    import ogr
else:
    print 'Error import ogr'
    
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
ini = time.time()

# get the driver
driver = ogr.GetDriverByName('ESRI Shapefile')
#Acessar layer ativo em Canvas
layer = qgis.utils.iface.activeLayer()
#Obter caminho shape
pathSHP =layer.dataProvider().dataSourceUri()
pathSHP = pathSHP.split('|')
#Ler layer OGR
shapefile = ogr.Open(str(pathSHP[0]))
#Obter layer
layerOGR = shapefile.GetLayer()
#Iterando sobre a geometria
features = layer.getFeatures()
dados=[]

for i,f in enumerate(features):
        featureOGR = layerOGR.GetFeature(i)  
        #Acessar todos os atributos do ponto
        featureOGR.items().values()
        layerOGR.SetSpatialFilter(featureOGR.GetGeometryRef().Buffer(1))
        d=[layerOGR.GetFeature(i).GetField("z") for j in xrange(layerOGR.GetFeatureCount())]
        media = sum(d)/len(d)

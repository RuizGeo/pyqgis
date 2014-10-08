##Filter points cloud=group
##Samples_points_cloud=vector
##Class_field=field Samples_points_cloud
##Points_clould=vector
##Z_field=field Points_clould
##Number_of_nearest_neighbor=number 30
##Weight_standard_deviation=number 0.5

#Import Numpy
import numpy as np
#Import time
import time
'''Import library to QGIS'''
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
#Import Utils to use Canvas
import qgis.utils
#import CART
from sklearn import tree
#import processing
import processing

class filterPointsClould:
    
    def createSample(self):
        '''
        Input sample shapefile points
        Create array from shapefile points
        Output training (dict) and class (list)
        '''
        #Open layer sample 
        layer_sample = processing.getObject(Samples_points_cloud)
        #Get index fields
        self.idx_field_class = layer_sample.fieldNameIndex(Class_field)
        #Get all fields
        fields = layer_sample.pendingFields()
        #Create list index fields
        self.idx_fields_sample = [i for i in range(len(fields))]
        print 'self.idx_field_class: ',self.idx_field_class, type(self.idx_field_class)
        
        self.idx_fields_sample.remove(self.idx_field_class)
        print 'self.idx_fields_sample: ',self.idx_fields_sample,type(self.idx_fields_sample)
        #iniciar variaveis auxiliares
        classes=[]
        training=[]
        #Iterando sobre a geometria
        layer_features = layer_sample.getFeatures()
        
        #Atribuir os fields em list
        fields_sample = [str(v.name ()) for i, v in enumerate(fields) if i in self.idx_fields_sample]
       
        if self.idx_field_class != -1:
            #percorrer layer samples
            for feat in layer_features:
                #Obter atributos
                attrs = feat.attributes()
                #Criar array para as classes de amostras
                classes.append(attrs[self.idx_field_class])
                #criar array para os valores z,r,g e b
                for i, v in enumerate(self.idx_fields_sample):
                    training.append(attrs[v])
 
            self.clas = np.asarray(classes)
            self.trein = np.asarray(training)
            n_col = len(self.idx_fields_sample)
            self.trein=self.trein.reshape(self.clas.shape[0],n_col )
            print self.clas.shape[0], self.trein.shape,n_col
            #Delete variables
            del(classes)
            del(training)
            del(fields)
            del(fields_sample)
            
        else:
            print 'Error create array'
            
    def createDatas (self):
            '''
            Create shapefile memory points
            Input shapefile points
            Output shapefile memory points, Datas (numpy)
            '''
            #Open points cloud datas
            self.layer_datas = processing.getObject(Points_clould)
            #Get all fields
            self.fields_datas = self.layer_datas.pendingFields()
            #Get index field Z points cloud
            self.idx_z_datas = self.layer_datas.fieldNameIndex(Z_field)
            #Create list index fields
            self.idx_fields_datas = [i for i in range(len(self.fields_datas))]
            print 'self.idx_fields_datas: ', self.idx_fields_datas
            #inicia variaveis
            attrs_registro=[]
            data=[]
            self.datasIDs = np.array([])
            # create layer temporary
            self.vl = QgsVectorLayer("Point?crs=EPSG:32722", "temporary_points", "memory")
            #Get provider
            pr = self.vl.dataProvider()
            #Iniciar edicao 
            self.vl.startEditing()
            
            #obter apenas fields dos indexs
            #fields_vl = [self.fields_datas[v] for v in self.idx_fields_datas]
               
            #Add QgsFileds in temporary file
            print 'criou temp e iniciou a edicao'
            time.sleep(5)
            self.fields_datas=[self.fields_datas[v] for v in range(len(self.fields_datas))]
            pr.addAttributes(self.fields_datas)
            
            #Iterando sobre a geometria
            layer_features = self.layer_datas.getFeatures()
            print 'Add attributes e obtve layers'
            time.sleep(5)
            for feat in layer_features:
                #obter geometria
                geom =feat.geometry()
                #Obter attributes
                attrs = feat.attributes()
                #Get FID
                self.datasIDs = np.append(self.datasIDs, feat.id())
                #criar array para os valores z,r,g e b
                attrs_registro = [attrs[i] for i in self.idx_fields_datas]
                #Add attributes in data array
                data.append(attrs_registro)
                fet = QgsFeature()
                #Set geometry
                fet.setGeometry( QgsGeometry.fromPoint(geom.asPoint() ))
                #Set attributes in temporary
                fet.setAttributes(attrs_registro)
                #Use provider to add features
                pr.addFeatures([fet])
                #update temporary
                self.vl.updateExtents()
            #Create array from Datas list
            self.datas = np.asarray(data)
            #commite changes
            self.vl.commitChanges()
            #Delete variables
            del(data)
            
            
    def classifierTree(self):
        '''
        Create model tree 
        Input treining (numpy array), class (numpy array) and datas (numpy)
        Output array Numyp with classification of Datas
        '''
        #Choose type classification
        clf = tree.DecisionTreeClassifier()
        #Crate model classification tree
        modelTree = clf.fit(self.trein, self.clas)
        #Apply model classification in Datas
        self.classificationDatas = modelTree.predict(self.datas)
    def deleteFeaturesDatas(self):
        '''
        Delete features class = no terrain
        Input memory shape and Datas classification 
        Output memory shape without class = terrain
        '''
        #Start editing memory shape
        self.vl.startEditing()
        #Loop about memory shape
        for i, feat in enumerate (self.vl.getFeatures()):
            #Assess class = variable no terrain
            if self.classificationDatas[i] == 1:
                #Delete FID
                self.vl.deleteFeature(feat.id()) 
                #Update memory shape
                self.vl.updateExtents()
            else:
                pass
        #Commite change
        self.vl.commitChanges()
        
    def filterNN(self):
        '''
        Apply filter interval confidence
        Input memory shape 
        Output memory shape without features out interval confidence
        '''
        #Open edition layer temporary
        self.vl.startEditing()
        #Get Z of file Datas 
        z = self.datas[:,self.idx_z_datas]

        #create spatial index
        spIndex = QgsSpatialIndex()
        #Inserir features para gerar os grupos de distancias
        for f in self.vl.getFeatures():
            spIndex .insertFeature(f)
        #start variables 
        numberPoints = int(Number_of_nearest_neighbor)
        weight_stedv = Weight_standard_deviation
        print 'Number_of_nearest_neighbor: ',Number_of_nearest_neighbor
        print 'Weight_standard_deviation: ',Weight_standard_deviation
        #Filter nearestNeighbor
        for feature in self.vl.getFeatures():
            #Get Z attributes
            z_datas = feature.attributes()[self.idx_z_datas]
            #Get geometry of features
            geom = feature.geometry()
            #Get IDs from Nearest Neighbor
            nearestIds = spIndex.nearestNeighbor(geom.asPoint(),numberPoints)
            #Get values of Datas
            values_datas = z[np.where(np.in1d(self.datasIDs,np.asarray(nearestIds)))]
            #Calculate mean
            mean = values_datas.sum()/len(values_datas)
            stedv = values_datas.std(ddof=1)
            stedv = abs(stedv)
            dv = stedv * weight_stedv
            #Eval interval confidence
            if z_datas > (mean - dv) and z_datas < (mean + dv):
                pass
            else:
                
                try:
                    self.vl.deleteFeature(feature.id())   
                    self.vl.updateExtents()
                    
                except:

                    print 'Error delete FID: ',feature.id()
            
        #Send changes layer temporary
        self.vl.commitChanges()
        #Insert memory shape QGIS
        QgsMapLayerRegistry.instance().addMapLayer(self.vl)
        
ini=time.time()

#Create Sample 
func = filterPointsClould()
print 'Create FilterPointsCloud()'
#create sample
func.createSample()
print 'create sample'
#Create func Dataset
func.createDatas()
print 'create datas'
#Create func to classifier decision tree
func.classifierTree()
print 'model tree'
#Delete features from classifier Decision Tree
func.deleteFeaturesDatas()
print 'deleteFeatures'
#Filter
func.filterNN()
print 'Filter'
fim = time.time()
print "Tempo em minutos: ", (fim-ini)/60

# -*- coding: utf-8 -*-
from numpy import array, linalg, repeat
from math import atan
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsPoint, QgsGeometry,
                       QgsFeature)
                       
def get_a_from_2p(xa, xc, ya, yc):
    s1 = array([[xa, 1],[xc, 1]])
    s2 = array([ya, yc])

    w = linalg.solve(s1,s2)
    a = w[0]
    return(a)

def licz_kat(a1,a2):
    tgalfa = abs((a1-a2)/(1+(a1*a2)))
    alfa = atan(tgalfa)
    truealfa = alfa * 57.29577951308
    return(truealfa)


class GenJenksK(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def createInstance(self):
        return GenJenksK()

    def name(self):
        return 'generalizacjajenksakatowa'

    def displayName(self):
        return 'Generalizacja Jenksa Kątowa'

    def group(self):
        return 'Generalizacje'

    def groupId(self):
        return 'generalizacje'

    def initAlgorithm(self, config=None):
        #Dodanie warstwy liniowej którą chcemy zgeneralizować
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                'Warstwa liniowa do generalizacji',
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        #Określenie granicznej długości linii  prostopadłej
        self.addParameter(
            QgsProcessingParameterNumber(
                'Kat',
                'Wartość graniczna kąta',
                QgsProcessingParameterNumber.Double,
                0,
                minValue = 0,
            )
        )

        #Przygotowanie warstwy outputowej
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                'Output layer'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )
        gr = self.parameterAsDouble(parameters, 'Kat', context)
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs()
        )

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break
            
            geom = feature.geometry()
            g = geom.asMultiPolyline()
            wyn = [g[0][0]]
            booltable = repeat([1], len(g[0]))
            for i in range(0,len(g[0])-2):
                if booltable[i] == 0:
                    pass
                else:
                    x = g[0][i][0]
                    y = g[0][i][1]
                    j = i
                    if i == len(g[0])-2:
                        booltable[i+1] == 1
                    if booltable[i+1] == 1:
                        xc = g[0][i+1][0]
                        yc = g[0][i+1][1]
                        xd = g[0][i+2][0]
                        yd = g[0][i+2][1]
                    else:
                        while booltable[j+1] == 0:
                            xc = g[0][j+2][0]
                            yc = g[0][j+2][1]
                            xd = g[0][j+3][0]
                            yd = g[0][j+3][1]
                            j = j + 1
                            
                    if x == xc or x == xd:
                        xc = xc + 0.000001
                        
                    a1 = get_a_from_2p(x,xc,y,yc)
                    a2 = get_a_from_2p(x,xd,y,yd)
                    if a1 == -(1/a2):
                        kat = 90
                    else:
                        kat = licz_kat(a1,a2)
                        if (x > xc and x < xd) or (x < xc and x > xd):
                            kat = 180 - kat
                    if kat >= gr:
                        wyn.append(g[0][i+1])
                    else:
                        booltable[i+1] = 0
                        i = i - 1
            wyn.append(g[0][len(g[0])-1])
            booltable = []
            punkty = []
            
            for j in range(1,len(wyn)+1):
                punkty.append(QgsPoint(wyn[j-1]))
            linia = QgsGeometry.fromPolyline(punkty)
            f = QgsFeature()
            f.setGeometry(linia)
            sink.addFeature(f, QgsFeatureSink.FastInsert)
            punkty = []
                
            wyn.append(g[0][len(g[0])-1])
            
            wyn = []
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

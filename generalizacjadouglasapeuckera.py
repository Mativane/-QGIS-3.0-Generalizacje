# -*- coding: utf-8 -*-
from numpy import array, linalg
from math import sqrt
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterNumber,
                       QgsPoint, QgsGeometry,
                       QgsFeature)
                       
def p2row(xa, xc, ya, yc):

    s1 = array([[xa, 1],[xc, 1]])
    s2 = array([ya, yc])

    w = linalg.solve(s1,s2)
    a = w[0]
    c = w[1]
    b = -1
    return [a,b,c]


def odl_pro(x,y,a,b,c):

    d = abs((a*x)+(b*y)+c)/sqrt((a**2)+(b**2))
    return d

def DPcore(A, B, Imin, Imax, g, gr, wyn):
    print("HO!")
    if Imin + 1 == Imax:
        return None
    w = p2row(A[0], B[0], A[1], B[1])
    max = 0
    iter = 0
    if Imin + 2 == Imax:
        max = odl_pro(g[0][Imin+1][0], g[0][Imin+1][1], w[0], w[1], w[2])
        iter = Imin+1
    else:
        for i in range(Imin+1, Imax-1):
            maybemax = odl_pro(g[0][i][0], g[0][i][1], w[0], w[1], w[2])
            if maybemax > max:
                max = maybemax
                iter = i
    if max < gr:
        return None
    else:
        wyn.append(g[0][iter])
        DPcore(A, g[0][iter], Imin, iter, g, gr, wyn), DPcore(g[0][iter], B, iter, Imax, g, gr, wyn)
        return wyn


def sorter(klucz, x):
    output = []
    for i in klucz:

        for j in x:
            if j == i:
                output.append(j)
    return output

class GenDP(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def createInstance(self):
        return GenDP()

    def name(self):
        return 'generalizacjadouglasapeuckera'

    def displayName(self):
        return 'Generalizacja Douglasa Peuckera'

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
                'Prosta_Prostokatna',
                'Wartość graniczna generalizacji',
                QgsProcessingParameterNumber.Double,
                0,
                minValue = 0
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
        gr = self.parameterAsDouble(parameters, 'Prosta_Prostokatna', context)
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
            wyn = DPcore(g[0][0], g[0][len(g[0])-1], 0, len(g[0])-1, g, gr, wyn)
            if wyn == None:
                wyn = [g[0][0]]
            wyn.append(g[0][len(g[0])-1])
            wyn = sorter(g[0],wyn)
            punkty = []
            for j in range(0,len(wyn)):
                punkty.append(QgsPoint(wyn[j]))
            linia = QgsGeometry.fromPolyline(punkty)
            f = QgsFeature()
            f.setGeometry(linia)
            sink.addFeature(f, QgsFeatureSink.FastInsert)

            wyn = []
            feedback.setProgress(int(current * total))

        return {self.OUTPUT: dest_id}

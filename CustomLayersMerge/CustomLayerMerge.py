import os
import json
import unicodedata
import nuke
import nukescripts

NODE_MARGIN = 110


class mergeLayers(nukescripts.PythonPanel):
    def __init__(self, ):
        nukescripts.PythonPanel.__init__(self, 'Merge layers')
        self.customName = nuke.String_Knob('customName', 'Custom layers name', 'Light')
        self.customName.setTooltip('Insert the parts of the names you want to use, separated by ", " (comma + space)')
        self.loadJsonBtn = nuke.Script_Knob('Load preset')
        self.loadJsonBtn.setTooltip('Load previously saved settings')
        self.loadJsonBtn.clearFlag(nuke.STARTLINE)
        self.saveJsonBtn = nuke.Script_Knob('Save preset')
        self.saveJsonBtn.setTooltip('Save your current settings')
        self.saveJsonBtn.clearFlag(nuke.STARTLINE)

        self.loadAllCheck = nuke.Boolean_Knob('extractAll', 'Extract all existing layers')
        self.loadAllCheck.setFlag(nuke.STARTLINE)

        self.operationNames = ['atop', 'average', 'color-burn', 'color-dodge', 'conjoint-over', 'copy',
                                                'difference', 'disjoint-over', 'divide', 'exclusion', 'from',
                                                'geometric', 'hard-light', 'hypot', 'in', 'mask', 'matte', 'max', 'min',
                                                'minus', 'multiply', 'out', 'over', 'overlay', 'plus', 'screen',
                                                'soft-light', 'stencil', 'under', 'xor']
        self.operation = nuke.Enumeration_Knob('operation', 'Merge operation', self.operationNames)
        self.operation.setValue('plus')
        for k in (self.customName, self.loadJsonBtn, self.saveJsonBtn, self.loadAllCheck, self.operation):
            self.addKnob(k)

    def knobChanged(self, knob):
        if knob in [self.loadJsonBtn, ]:
            self.loadJson()
        elif knob in [self.saveJsonBtn, ]:
            self.saveJson()

    def loadJson(self):

        # Get script path
        # scriptPath = os.path.abspath(__file__)
        scriptPath = 'C:/Users/TristanLG/Desktop/'
        presetFilePath = scriptPath + 'preset.json'

        # Open file browser
        if os.path.isfile(presetFilePath):
            with open(presetFilePath) as presetFile:
                data = json.load(presetFile)
                operation = data['operation']['value']
                customName = data['customName']['value']
                useAll = data['loadAll']['value']

                operation = unicodedata.normalize('NFKD', operation).encode('ascii', 'ignore')

                self.customName.setValue(customName)
                self.operation.setValue(operation)
                self.loadAllCheck.setValue(useAll)

        else:
            print('no preset file found')

    def saveJson(self):

        # Extract infos
        prefixes = self.customName.value()
        operation = self.operation.value()
        useAll = self.loadAllCheck.value()

        # Get script path
        # scriptPath = os.path.abspath(__file__)
        scriptPath = 'C:/Users/TristanLG/Desktop/'

        # Create JSON datas
        data = {}
        data['operation'] = {'value': operation}
        data['customName'] = {'value': prefixes}
        data['loadAll'] = {'value': useAll}

        presetFilePath = scriptPath + 'preset.json'

        with open(presetFilePath, 'w') as presetFile:
            json.dump(data, presetFile)

    def extractPrefixes(self, prefixes):

        prefixes = prefixes.split(', ')

        return prefixes

    def layerMerge(self, prefixes, operation, selection):

            prefixes = self.extractPrefixes(prefixes)
            useAll = self.loadAllCheck.value()

            # Unselect selection
            for node in selection:
                node['selected'].setValue(False)

            for node in selection:
                # Check if the node is a read node
                if node.Class() == 'Read':

                    # Select actual read
                    node['selected'].setValue(True)

                    # Get it's position
                    baseXPose = node['xpos'].value()
                    baseYPose = node['ypos'].value()

                    # Get it's channels and layers
                    channels = node.channels()
                    layers = list(set([c.split('.')[0] for c in channels]))
                    usedLayers = []
                    usedGrades = []

                    shuffleYPos = baseYPose + NODE_MARGIN * 1.5

                    # For each layer found if it's a light layer
                    print(useAll)
                    if not useAll:
                        for i, layer in enumerate(layers):
                            for prefix in prefixes:
                                # If specified prefix is found in the layer's name
                                if prefix in layer:
                                    usedLayers.append(layer)
                    else:
                        usedLayers = layers

                    # Find start XPos
                    if (len(usedLayers) % 2) == 0:
                        # Number of layers is even
                        factor = float(len(usedLayers) / 2)
                        shuffleXPos = baseXPose - (NODE_MARGIN * (factor) - NODE_MARGIN / 2)
                    else:
                        # Number of layers is odd
                        factor = int((len(usedLayers) - 1) / 2)
                        shuffleXPos = baseXPose - (NODE_MARGIN * factor)

                    # For each light layer
                    for i, layer in enumerate(usedLayers):

                            # Create a shuffle node
                            shuffleNode = nuke.nodes.Shuffle(inputs=[node])
                            shuffleNode['in'].setValue(layer)
                            shuffleNode['postage_stamp'].setValue(True)

                            # Position the shuffle node
                            shuffleNode['xpos'].setValue(shuffleXPos)
                            shuffleNode['ypos'].setValue(shuffleYPos)

                            # Create a grade node
                            gradeNode = nuke.nodes.Grade()
                            gradeNode.setInput(0, shuffleNode)

                            # Position the grade node
                            gradeYPos = gradeNode['ypos'].value()
                            gradeNode['ypos'].setValue(gradeYPos + 150)

                            # Store the grade node for later merging
                            usedGrades.append(gradeNode)

                            # Update next xPose
                            shuffleXPos += NODE_MARGIN

                    # Unselect the read node
                    node['selected'].setValue(False)

                    # Create a merge Node
                    mergeNode = nuke.createNode('Merge2')

                    for i, o in enumerate(self.operationNames):
                        if operation == o:
                            mergeNode.knob('operation').setValue(i)
                            break

                    # Connect the grade nodes to the merge
                    for i, node in enumerate(usedGrades):
                        if i < 2:
                            mergeNode.setInput(i, node)
                        elif i >= 2:
                            mergeNode.setInput(i + 1, node)

                    # Position merge
                    mergeNode['ypos'].setValue(shuffleYPos + NODE_MARGIN * 2)
                    mergeNode['xpos'].setValue(baseXPose)

def main():

    selection = nuke.selectedNodes()

    # Check if there's a read in the selection
    readIsPresent = False
    for node in selection:
        if node.Class() == 'Read':
            readIsPresent = True
            break

    if readIsPresent:
        panel = mergeLayers()
        if panel.showModalDialog():
            panel.layerMerge(panel.customName.value(), panel.operation.value(), selection)

    # If there's no read nor selection
    else:
        nuke.message('Please select at least one Read node')
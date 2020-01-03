import os
import json
import unicodedata
import nuke
import nukescripts

NODE_MARGIN = 110


class mergeLayers(nukescripts.PythonPanel):
    def __init__(self, ):
        nukescripts.PythonPanel.__init__(self, 'Merge layers')

        usedKnobs = []

        # Custom name
        self.customName = nuke.String_Knob('customName', 'Custom layers name', 'Light')
        self.customName.setTooltip('Insert the parts of the names you want to use, separated by ", " (comma + space)')
        usedKnobs.append(self.customName)

        # Preset buttons
        self.loadJsonBtn = nuke.Script_Knob('Load preset')
        self.loadJsonBtn.setTooltip('Load previously saved settings')
        self.loadJsonBtn.clearFlag(nuke.STARTLINE)
        usedKnobs.append(self.loadJsonBtn)

        self.saveJsonBtn = nuke.Script_Knob('Save preset')
        self.saveJsonBtn.setTooltip('Save your current settings')
        self.saveJsonBtn.clearFlag(nuke.STARTLINE)
        usedKnobs.append(self.saveJsonBtn)

        # Options
        self.loadAllCheck = nuke.Boolean_Knob('extractAll', 'Extract all existing layers')
        self.loadAllCheck.setFlag(nuke.STARTLINE)
        self.loadAllCheck.setTooltip('Extract all the existing layers without using the custom name option')
        usedKnobs.append(self.loadAllCheck)

        self.addGrade = nuke.Boolean_Knob('addGrade', 'Add grade nodes')
        self.addGrade.setTooltip('Add a grade node after each shuffle')
        self.addGrade.setFlag(nuke.STARTLINE)
        usedKnobs.append(self.addGrade)

        self.addCC = nuke.Boolean_Knob('addCC', 'Add color correct nodes')
        self.addCC.setTooltip('Add a color correct node after each shuffle')
        self.addCC.setFlag(nuke.STARTLINE)
        usedKnobs.append(self.addCC)

        self.separatedMerges = nuke.Boolean_Knob('separatedMerges', 'Separated merges')
        self.separatedMerges.setTooltip('Add multiple merges instead of just one for all the layers')
        self.separatedMerges.setFlag(nuke.STARTLINE)
        usedKnobs.append(self.separatedMerges)

        # Merge operation
        self.operationNames = ['atop', 'average', 'color-burn', 'color-dodge', 'conjoint-over', 'copy',
                                                'difference', 'disjoint-over', 'divide', 'exclusion', 'from',
                                                'geometric', 'hard-light', 'hypot', 'in', 'mask', 'matte', 'max', 'min',
                                                'minus', 'multiply', 'out', 'over', 'overlay', 'plus', 'screen',
                                                'soft-light', 'stencil', 'under', 'xor']
        self.operation = nuke.Enumeration_Knob('operation', 'Merge operation', self.operationNames)
        self.operation.setValue('plus')
        usedKnobs.append(self.operation)

        for k in usedKnobs:
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
            useGrade = self.addGrade.value()
            useCC = self.addCC.value()
            separateMerges = self.separatedMerges.value()

            # Unselect selection
            for node in selection:
                node['selected'].setValue(False)

            for node in selection:
                # Check if the node is a read node
                if node.Class() == 'Read':

                    mergeInputs = []

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

                    lastMerge = ''

                    # For each layer
                    for i, layer in enumerate(usedLayers):

                        # Create a shuffle node
                        shuffleNode = nuke.nodes.Shuffle(inputs=[node])
                        shuffleNode['in'].setValue(layer)
                        shuffleNode['postage_stamp'].setValue(True)

                        # Position the shuffle node
                        shuffleNode['xpos'].setValue(shuffleXPos)
                        shuffleNode['ypos'].setValue(shuffleYPos)

                        parent = shuffleNode

                        if useGrade:
                            # Create a grade node
                            gradeNode = nuke.nodes.Grade()
                            gradeNode.setInput(0, parent)

                            # Position the grade node
                            gradeYPos = gradeNode['ypos'].value()
                            gradeNode['ypos'].setValue(gradeYPos + 150)

                            parent = gradeNode

                            if not useCC:
                                mergeInputs.append(gradeNode)

                        if useCC:
                            # Create a grade node
                            ccNode = nuke.nodes.ColorCorrect()
                            ccNode.setInput(0, parent)

                            # Position the grade node
                            ccYPos = ccNode['ypos'].value()
                            ccNode['ypos'].setValue(ccYPos + 150)

                            mergeInputs.append(ccNode)

                        elif not useGrade:
                            mergeInputs.append(shuffleNode)

                        if separateMerges:

                            node['selected'].setValue(False)

                            if i == 0:
                                # Create a dot Node
                                dotNode = nuke.createNode('Dot')

                                # Connect the node to the dot
                                dotNode.setInput(0, mergeInputs[i])

                                # Position the dot
                                dotNode['ypos'].setValue(shuffleYPos + 4 + NODE_MARGIN * 2)
                                dotNode['xpos'].setValue(shuffleXPos + 34)

                                lastMerge = dotNode

                            else:
                                # Create a merge Node
                                mergeNode = nuke.createNode('Merge2')

                                for j, o in enumerate(self.operationNames):
                                    if operation == o:
                                        mergeNode.knob('operation').setValue(j)
                                        break

                                # Connect the nodes to the merge
                                mergeNode.setInput(0, lastMerge)
                                mergeNode.setInput(1, mergeInputs[i])

                                # Position merge
                                mergeNode['ypos'].setValue(shuffleYPos + NODE_MARGIN * 2)
                                mergeNode['xpos'].setValue(shuffleXPos)

                                node['selected'].setValue(True)
                                mergeNode['selected'].setValue(False)

                                lastMerge = mergeNode

                        # Update next xPose
                        shuffleXPos += NODE_MARGIN

                    if not separateMerges:
                        # Unselect the read node
                        node['selected'].setValue(False)

                        # Create a merge Node
                        mergeNode = nuke.createNode('Merge2')

                        for i, o in enumerate(self.operationNames):
                            if operation == o:
                                mergeNode.knob('operation').setValue(i)
                                break

                        # Connect the grade nodes to the merge
                        for i, node in enumerate(mergeInputs):
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

import nuke
from CustomLayersMerge import loader

customMenu = nuke.menu("Nuke").addMenu("Custom").addCommand('Custom Layers Merge', loader.main)

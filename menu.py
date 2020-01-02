import nuke
from CustomLayersMerge import CustomLayerMerge

customMenu = nuke.menu("Nuke").addMenu("Custom").addCommand('Custom Layers Merge', CustomLayerMerge.main)

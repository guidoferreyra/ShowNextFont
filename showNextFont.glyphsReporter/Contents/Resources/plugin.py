# encoding: utf-8


from GlyphsApp.plugins import *
from GlyphsApp import *

class showNextFont(ReporterPlugin):

	def settings(self):
		self.menuName = Glyphs.localize({'en': u'Next Font'})

	# default centering setting:
		Glyphs.registerDefault("com.guidoferreyra.showNextFont.fill", 0)
	
	def drawNextFont( self, layer ):
		try:
			thisGlyph = layer.parent
			thisFont = thisGlyph.parent
			thisMaster = thisFont.selectedFontMaster
			masters = thisFont.masters
			nextFont = Glyphs.fonts[1]
			nextFontMasters = nextFont.masters
			nextGlyph = nextFont.glyphs[thisGlyph.name]

			try:
				# Glyphs 2 (Python 2.7)
				activeMasterIndex = masters.index(thisMaster)
			except:
				# Glyphs 1 (Python 2.6)
				for i, k in enumerate(masters):
					if thisMaster == masters[i]:
						activeMasterIndex = i
			
			if len(masters) != len(nextFontMasters):
				nextLayer = nextGlyph.layers[0]
			else:
				nextLayer = nextGlyph.layers[activeMasterIndex]

			drawingColor = 0.91, 0.32, 0.06, 0.45			
			# draw path AND components:
			NSColor.colorWithCalibratedRed_green_blue_alpha_( *drawingColor ).set()
			#thisBezierPathWithComponent = Layer.copyDecomposedLayer().bezierPath
			
			try:
				thisBezierPathWithComponent = nextLayer.copyDecomposedLayer().bezierPath()
			except:
	 			thisBezierPathWithComponent = nextLayer.copyDecomposedLayer().bezierPath
			
			if thisBezierPathWithComponent:
				if Glyphs.defaults["com.guidoferreyra.showNextFont.fill"]:
					thisBezierPathWithComponent.fill()
				else:
					drawingColor = 0.91, 0.32, 0.06, 0.9
					NSColor.colorWithCalibratedRed_green_blue_alpha_( *drawingColor ).set()
					thisBezierPathWithComponent.setLineWidth_(0)
					thisBezierPathWithComponent.stroke()


		except Exception, e:
			pass

	def background(self, layer):
		self.drawNextFont( layer )
		

	def inactiveLayerBackground(self, layer):
		self.drawNextFont( layer )

	def needsExtraMainOutlineDrawingForInactiveLayer_(self, layer):
		return True
	
	def syncViews(self, layer):
		try:
			layer = Glyphs.font.selectedLayers[0]
			thisFont = layer.parent.parent
			thisMaster = thisFont.selectedFontMaster
			thisScale = thisFont.currentTab.scale
			thisViewportX = thisFont.currentTab.viewPort.origin.x
			thisViewportY = thisFont.currentTab.viewPort.origin.y
			thisTextCursor = thisFont.currentTab.textCursor

			thisMasterIndex = thisFont.masterIndex
			thisText = thisFont.currentTab.text
			try:
				for i in range(len(Glyphs.fonts)):
					if i != 0:
						otherFont = Glyphs.fonts[i]
						
						otherFont.newTab('')
						otherCurrentTab = otherFont.currentTab

						if thisMasterIndex <= len(otherFont.masters):
							otherFont.masterIndex = thisMasterIndex
						otherCurrentTab.scale = thisScale
						otherCurrentTab.viewPort.origin.x = thisViewportX
						otherCurrentTab.viewPort.origin.y = thisViewportY
						otherCurrentTab.text = thisText
						otherCurrentTab.textCursor = thisTextCursor

			except Exception, e:
				Glyphs.showMacroWindow()
				print "Sync Edit views Error (Inside Loop): %s" % e

		except Exception, e:
			Glyphs.showMacroWindow()
			print "Sync Edit views Error: %s" % e

	def conditionalContextMenus(self):

		# Empty list of context menu items
		contextMenus = []

		if not Glyphs.defaults["com.guidoferreyra.showNextFont.fill"]:
			contextMenus.append(
				{
					'name': Glyphs.localize({
						'en': u'Fill next font'
					}), 'action': self.toggleFill
				},
			)
		else:
			contextMenus.append(
				{
					'name': Glyphs.localize({
						'en': u'Outline next font'
					}), 'action': self.toggleFill
				},
			)

		# Execute only if layers are actually selected
		if Glyphs.font.selectedLayers:
			layer = Glyphs.font.selectedLayers[0]
	
			contextMenus.append({'name': Glyphs.localize({'en': u'Sync edit views'}), 'action': self.syncViews})

		# Return list of context menu items
		return contextMenus

	def toggleFill(self):	
		Glyphs.defaults["com.guidoferreyra.showNextFont.fill"] = not Glyphs.defaults["com.guidoferreyra.showNextFont.fill"]

		
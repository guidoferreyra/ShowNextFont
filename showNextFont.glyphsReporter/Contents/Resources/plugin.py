# encoding: utf-8

###########################################################################################################
#
#
# Reporter Plugin
#
# Read the docs:
# https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals

import objc
from Cocoa import NSAffineTransform, NSColor, NSBezierPath, NSRect
from GlyphsApp import Glyphs, OFFCURVE
from GlyphsApp.plugins import ReporterPlugin


class showNextFont(ReporterPlugin):

    @objc.python_method
    def settings(self):
        self.menuName = Glyphs.localize({"en": "Next Font"})

        # default fill setting:
        Glyphs.registerDefault("com.guidoferreyra.showNextFont.fill", 0)
        # default show nodes setting:
        Glyphs.registerDefault("com.guidoferreyra.showNextFont.showNodes", 1)

    @objc.python_method
    def drawNextFont(self, layer):
        if len(Glyphs.fonts) < 2:
            return

        try:
            thisGlyph = layer.parent
            thisFont = thisGlyph.parent
            thisMaster = thisFont.selectedFontMaster
            masters = thisFont.masters
            nextFont = Glyphs.fonts[1]
            nextFontMasters = nextFont.masters
            nextGlyph = nextFont.glyphs[thisGlyph.name]
            if nextGlyph is None:
                # Glyph is missing in next font
                return

            activeMasterIndex = masters.index(thisMaster)

            if len(masters) != len(nextFontMasters):
                nextLayer = nextGlyph.layers[0]
            else:
                nextLayer = nextGlyph.layers[activeMasterIndex]

            scale = thisFont.currentTab.scale

            drawingColor = 0.91, 0.32, 0.06, 0.45
            # draw path AND components:
            NSColor.colorWithCalibratedRed_green_blue_alpha_(*drawingColor).set()

            try:
                thisBezierPathWithComponent = (
                    nextLayer.copyDecomposedLayer().bezierPath()
                )
            except:  # noqa: E722
                thisBezierPathWithComponent = nextLayer.copyDecomposedLayer().bezierPath

            # Apply UPM scaling if needed
            scaleFactor = 1.0
            if thisFont.upm != nextFont.upm:
                scaleFactor = thisFont.upm / nextFont.upm
                transform = NSAffineTransform.new()
                transform.scaleBy_(scaleFactor)
                thisBezierPathWithComponent = transform.transformBezierPath_(
                    thisBezierPathWithComponent
                )

            # Draw the main path
            if thisBezierPathWithComponent:
                if Glyphs.defaults["com.guidoferreyra.showNextFont.fill"]:
                    thisBezierPathWithComponent.fill()
                else:
                    drawingColor = 0.91, 0.32, 0.06, 0.9
                    NSColor.colorWithCalibratedRed_green_blue_alpha_(
                        *drawingColor
                    ).set()
                    thisBezierPathWithComponent.setLineWidth_(0)
                    thisBezierPathWithComponent.stroke()

            # Draw nodes and handles if enabled
            if Glyphs.defaults["com.guidoferreyra.showNextFont.showNodes"]:
                self.drawNodesAndHandles(nextLayer, scaleFactor, scale)

        except Exception as e:
            print(e)

    @objc.python_method
    def drawNodesAndHandles(self, nextLayer, scaleFactor, scale):
        try:
            oncurveColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.91, 0.32, 0.06, 0.9
            )
            offcurveColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.91, 0.32, 0.06, 0.7
            )
            handleLineColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                0.91, 0.32, 0.06, 0.4
            )

            nodeSize = 8 / scale
            handleLineWidth = 1 / scale

            for path in nextLayer.paths:
                nodes = path.nodes
                if not nodes:
                    continue

                self.drawHandleLines(
                    nodes, scaleFactor, handleLineWidth, handleLineColor
                )

                for node in nodes:
                    x = node.position.x * scaleFactor
                    y = node.position.y * scaleFactor

                    if node.type == OFFCURVE:
                        self.drawNode(x, y, nodeSize * 0.6, offcurveColor)
                    else:
                        self.drawNode(x, y, nodeSize, oncurveColor)

        except Exception as e:
            print(f"Error drawing nodes and handles: {e}")

    @objc.python_method
    def drawHandleLines(self, nodes, scaleFactor, lineWidth, color):
        try:
            nodeCount = len(nodes)
            for i, node in enumerate(nodes):
                if node.type == OFFCURVE:
                    x = node.position.x * scaleFactor
                    y = node.position.y * scaleFactor

                    prevOnCurve = self.findAdjacentOnCurveNode(nodes, i, -1)
                    nextOnCurve = self.findAdjacentOnCurveNode(nodes, i, 1)

                    if prevOnCurve is not None and nextOnCurve is not None:
                        prevNode = nodes[prevOnCurve]
                        nextNode = nodes[nextOnCurve]

                        if i < nodeCount - 1 and nodes[i + 1].type == OFFCURVE:
                            prevX = prevNode.position.x * scaleFactor
                            prevY = prevNode.position.y * scaleFactor
                            self.drawLine(prevX, prevY, x, y, lineWidth, color)
                        elif i > 0 and nodes[i - 1].type == OFFCURVE:
                            nextX = nextNode.position.x * scaleFactor
                            nextY = nextNode.position.y * scaleFactor
                            self.drawLine(x, y, nextX, nextY, lineWidth, color)
                        else:
                            nextX = nextNode.position.x * scaleFactor
                            nextY = nextNode.position.y * scaleFactor
                            self.drawLine(x, y, nextX, nextY, lineWidth, color)
        except Exception as e:
            print(f"Error drawing handle lines: {e}")

    @objc.python_method
    def findAdjacentOnCurveNode(self, nodes, currentIndex, direction):
        """Find the nearest oncurve node in the given direction (1 for forward, -1 for backward)"""
        nodeCount = len(nodes)
        i = currentIndex

        while True:
            i = (i + direction) % nodeCount
            if i == currentIndex:  # We've looped back, no oncurve found
                break
            if nodes[i].type != OFFCURVE:
                return i
        return None

    @objc.python_method
    def drawNode(self, x, y, size, color):
        path = NSBezierPath.alloc().init()
        rect = NSRect((x - size / 2, y - size / 2), (size, size))
        ovalInRect = NSBezierPath.bezierPathWithOvalInRect_(rect)
        path.appendBezierPath_(ovalInRect)
        color.set()
        path.fill()

    @objc.python_method
    def drawLine(self, x1, y1, x2, y2, lineWidth, color):
        color.set()
        myPath = NSBezierPath.bezierPath()
        myPath.moveToPoint_((x1, y1))
        myPath.lineToPoint_((x2, y2))
        myPath.setLineWidth_(lineWidth)
        myPath.stroke()

    @objc.python_method
    def background(self, layer):
        self.drawNextFont(layer)

    @objc.python_method
    def inactiveLayerBackground(self, layer):
        self.drawNextFont(layer)

    @objc.python_method
    def needsExtraMainOutlineDrawingForInactiveLayer_(self, layer):
        return True

    def syncViews_(self, layer):
        try:
            layer = Glyphs.font.selectedLayers[0]
            thisFont = layer.parent.parent
            # thisMaster = thisFont.selectedFontMaster
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

                        otherFont.newTab("")
                        otherCurrentTab = otherFont.currentTab

                        if thisMasterIndex <= len(otherFont.masters):
                            otherFont.masterIndex = thisMasterIndex
                        otherCurrentTab.scale = thisScale
                        otherCurrentTab.viewPort.origin.x = thisViewportX
                        otherCurrentTab.viewPort.origin.y = thisViewportY
                        otherCurrentTab.text = thisText
                        otherCurrentTab.textCursor = thisTextCursor
            except Exception as e:
                Glyphs.showMacroWindow()
                print("Sync Edit views Error (Inside Loop): %s" % e)

        except Exception as e:
            Glyphs.showMacroWindow()
            print("Sync Edit views Error: %s" % e)

    @objc.python_method
    def conditionalContextMenus(self):
        # Empty list of context menu items
        contextMenus = []

        contextMenus.append(
            {
                "name": Glyphs.localize({"en": "‘Show Next Font’ Options:"}),
                "action": None,
            },
        )

        # Fill/Outline toggle
        if not Glyphs.defaults["com.guidoferreyra.showNextFont.fill"]:
            contextMenus.append(
                {
                    "name": Glyphs.localize({"en": "Fill next font"}),
                    "action": self.toggleFill,
                },
            )
        else:
            contextMenus.append(
                {
                    "name": Glyphs.localize({"en": "Outline next font"}),
                    "action": self.toggleFill,
                },
            )

        # Show/Hide nodes toggle
        if Glyphs.defaults["com.guidoferreyra.showNextFont.showNodes"]:
            contextMenus.append(
                {
                    "name": Glyphs.localize({"en": "Hide nodes"}),
                    "action": self.toggleNodes,
                },
            )
        else:
            contextMenus.append(
                {
                    "name": Glyphs.localize({"en": "Show nodes"}),
                    "action": self.toggleNodes,
                },
            )

        # Execute only if layers are actually selected
        if Glyphs.font.selectedLayers:
            contextMenus.append(
                {
                    "name": Glyphs.localize({"en": "Sync edit views"}),
                    "action": self.syncViews_,
                }
            )

        # Return list of context menu items
        return contextMenus

    def toggleFill(self):
        Glyphs.defaults["com.guidoferreyra.showNextFont.fill"] = not Glyphs.defaults[
            "com.guidoferreyra.showNextFont.fill"
        ]

    def toggleNodes(self):
        Glyphs.defaults["com.guidoferreyra.showNextFont.showNodes"] = (
            not Glyphs.defaults["com.guidoferreyra.showNextFont.showNodes"]
        )

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__

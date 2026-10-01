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

from typing import TYPE_CHECKING, Any

import objc
from AppKit import NSAffineTransform, NSBezierPath, NSColor, NSKeyedArchiver, NSRect
from GlyphsApp import OFFCURVE, Glyphs
from GlyphsApp.plugins import ReporterPlugin

if TYPE_CHECKING:
    from GlyphsApp import GSLayer


def nsc(r: float, g: float, b: float, a: float) -> NSColor:
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)


def nsc_arch(r: float, g: float, b: float, a: float):
    result, _err = (
        NSKeyedArchiver.archivedDataWithRootObject_requiringSecureCoding_error_(
            nsc(r, g, b, a), True, None
        )
    )
    return result


class showNextFont(ReporterPlugin):
    @objc.python_method
    def settings(self) -> None:
        self.menuName = Glyphs.localize({"en": "Next Font"})

        Glyphs.registerDefaults(
            {
                "comGuidoferreyraShowNextFontFill": False,
                "comGuidoferreyraShowNextFontShowNodes": True,
                "comGuidoferreyraShowNextFontShowSidebearings": False,
                "comGuidoferreyraShowNextFontSyncEditViews": False,
                "comGuidoferreyraShowNextFontColor": nsc_arch(0.91, 0.32, 0.06, 0.45),
            }
        )

        if Glyphs.versionNumber < 4.0:
            return

        # Glyphs 4: Make settings editable from the Advanced Preferences dialog
        GSAdvancedPreferences = objc.lookUpClass("GSAdvancedPreferences")
        GSAdvancedPreferences.sharedAdvancedPreferences().registerEntries_forCategory_(
            [
                {
                    "title": "Fill next font",
                    "key": "comGuidoferreyraShowNextFontFill",
                    "type": "bool",
                },
                {
                    "title": "Show nodes",
                    "key": "comGuidoferreyraShowNextFontShowNodes",
                    "type": "bool",
                },
                {
                    "title": "Show sidebearings",
                    "key": "comGuidoferreyraShowNextFontShowSidebearings",
                    "type": "bool",
                },
                {
                    "title": "Sync edit views",
                    "key": "comGuidoferreyraShowNextFontSyncEditViews",
                    "type": "bool",
                },
                {
                    "title": "Fill color",
                    "key": "comGuidoferreyraShowNextFontColor",
                    "type": "color",
                },
            ],
            "Show Next Font",
        )

    @objc.python_method
    def drawNextFont(self, layer: "GSLayer") -> None:
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

            # draw path AND components:
            Glyphs.colorDefaults["comGuidoferreyraShowNextFontColor"].set()

            thisBezierPathWithComponent = nextLayer.completeBezierPath

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
                if Glyphs.defaults["comGuidoferreyraShowNextFontFill"]:
                    thisBezierPathWithComponent.fill()
                else:
                    Glyphs.colorDefaults[
                        "comGuidoferreyraShowNextFontColor"
                    ].colorWithAlphaComponent_(0.9).set()
                    thisBezierPathWithComponent.setLineWidth_(0)  # ?
                    thisBezierPathWithComponent.stroke()

                # Draw nodes and handles if enabled
                if Glyphs.defaults["comGuidoferreyraShowNextFontShowNodes"]:
                    self.drawNodesAndHandles(nextLayer, scaleFactor, scale)

            if Glyphs.defaults["comGuidoferreyraShowNextFontShowSidebearings"]:
                self.drawSideBearings(layer, nextLayer, scaleFactor, scale)

        except Exception as e:  # noqa: BLE001
            print(e)

    @objc.python_method
    def drawSideBearings(
        self,
        thisLayer: "GSLayer",
        nextLayer: "GSLayer",
        scaleFactor: float,
        scale: float,
    ) -> None:
        try:
            line_width = 1 / scale
            color = Glyphs.colorDefaults[
                "comGuidoferreyraShowNextFontColor"
            ].colorWithAlphaComponent_(0.7)
            x0 = 0
            x1 = nextLayer.width * scaleFactor
            y0 = thisLayer.descender * scaleFactor
            y1 = thisLayer.ascender * scaleFactor
            self.drawLine(x0, y0, x0, y1, line_width, color)
            self.drawLine(x1, y0, x1, y1, line_width, color)
        except Exception as e:  # noqa: BLE001
            print(f"Error sidebearings: {e}")

    @objc.python_method
    def drawNodesAndHandles(
        self, nextLayer: "GSLayer", scaleFactor: float, scale: float
    ) -> None:
        try:
            oncurveColor = Glyphs.colorDefaults[
                "comGuidoferreyraShowNextFontColor"
            ].colorWithAlphaComponent_(0.9)
            offcurveColor = Glyphs.colorDefaults[
                "comGuidoferreyraShowNextFontColor"
            ].colorWithAlphaComponent_(0.7)
            handleLineColor = Glyphs.colorDefaults[
                "comGuidoferreyraShowNextFontColor"
            ].colorWithAlphaComponent_(0.4)

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

        except Exception as e:  # noqa: BLE001
            print(f"Error drawing nodes and handles: {e}")

    @objc.python_method
    def drawHandleLines(
        self, nodes, scaleFactor: float, lineWidth: float, color: NSColor
    ) -> None:
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
        except Exception as e:  # noqa: BLE001
            print(f"Error drawing handle lines: {e}")

    @objc.python_method
    def findAdjacentOnCurveNode(
        self, nodes, currentIndex: int, direction: int
    ) -> int | None:
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
    def drawNode(self, x: float, y: float, size: float, color: NSColor) -> None:
        path = NSBezierPath.alloc().init()
        rect = NSRect((x - size / 2, y - size / 2), (size, size))
        ovalInRect = NSBezierPath.bezierPathWithOvalInRect_(rect)
        path.appendBezierPath_(ovalInRect)
        color.set()
        path.fill()

    @objc.python_method
    def drawLine(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        lineWidth: float,
        color: NSColor,
    ) -> None:
        color.set()
        myPath = NSBezierPath.bezierPath()
        myPath.moveToPoint_((x1, y1))
        myPath.lineToPoint_((x2, y2))
        myPath.setLineWidth_(lineWidth)
        myPath.stroke()

    @objc.python_method
    def background(self, layer: "GSLayer") -> None:
        self.drawNextFont(layer)

    @objc.python_method
    def inactiveLayerBackground(self, layer: "GSLayer") -> None:
        self.drawNextFont(layer)

    @objc.python_method
    def needsExtraMainOutlineDrawingForInactiveLayer_(self, layer: "GSLayer") -> bool:
        return True

    def syncViews_(self, layer: "GSLayer") -> None:
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
            except Exception as e:  # noqa: BLE001
                Glyphs.showMacroWindow()
                print(f"Sync Edit views Error (Inside Loop): {e}")

        except Exception as e:  # noqa: BLE001
            Glyphs.showMacroWindow()
            print(f"Sync Edit views Error: {e}")

    @objc.python_method
    def conditionalContextMenus(self) -> list[dict[str, Any]]:
        # Empty list of context menu items
        contextMenus = []

        if Glyphs.versionNumber >= 4.0:
            return contextMenus

        contextMenus.append(
            {
                "name": Glyphs.localize({"en": "‘Show Next Font’ Options:"}),
                "action": None,
            },
        )

        # Fill/Outline toggle
        if not Glyphs.defaults["comGuidoferreyraShowNextFontFill"]:
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
        if Glyphs.defaults["comGuidoferreyraShowNextFontShowNodes"]:
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

    def toggleFill(self) -> None:
        Glyphs.defaults["comGuidoferreyraShowNextFontFill"] = not Glyphs.defaults[
            "comGuidoferreyraShowNextFontFill"
        ]

    def toggleNodes(self) -> None:
        Glyphs.defaults["comGuidoferreyraShowNextFontShowNodes"] = not Glyphs.defaults[
            "comGuidoferreyraShowNextFontShowNodes"
        ]

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__

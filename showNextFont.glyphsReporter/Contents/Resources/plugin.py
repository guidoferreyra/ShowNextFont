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

from math import radians, tan
from typing import TYPE_CHECKING, Any

import objc
from AppKit import NSAffineTransform, NSBezierPath, NSColor, NSKeyedArchiver, NSRect
from GlyphsApp import OFFCURVE, Glyphs
from GlyphsApp.drawingTools import restore, save
from GlyphsApp.plugins import ReporterPlugin

if TYPE_CHECKING:
    from GlyphsApp import GSLayer

BASE_COLOR = (0.91, 0.32, 0.06, 0.45)


def fallbackColor() -> NSColor:
    return nsc(*BASE_COLOR)


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
                "comGuidoferreyraShowNextFontShowAnchors": False,
                "comGuidoferreyraShowNextFontShowSidebearings": False,
                "comGuidoferreyraShowNextFontColor": nsc_arch(*BASE_COLOR),
                "comGuidoferreyraShowNextFontMatchAngle": False,
                "comGuidoferreyraShowNextFontCenter": False,
            }
        )

        if Glyphs.versionNumber < 4.0:
            return

        # Glyphs 4: Make settings editable from the Advanced Preferences dialog
        GSAdvancedPreferences = objc.lookUpClass("GSAdvancedPreferences")
        GSAdvancedPreferences.sharedAdvancedPreferences().registerEntries_forCategory_(
            [
                {
                    "title": "Fill color",
                    "key": "comGuidoferreyraShowNextFontColor",
                    "type": "color",
                },
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
                    "title": "Show anchors",
                    "key": "comGuidoferreyraShowNextFontShowAnchors",
                    "type": "bool",
                },
                {
                    "title": "Show sidebearings",
                    "key": "comGuidoferreyraShowNextFontShowSidebearings",
                    "type": "bool",
                },
                {
                    "title": "Match italic angle",
                    "key": "comGuidoferreyraShowNextFontMatchAngle",
                    "type": "bool",
                },
                {
                    "title": "Center layer horizontally",
                    "key": "comGuidoferreyraShowNextFontCenter",
                    "type": "bool",
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

            if activeMasterIndex >= len(nextFontMasters):
                nextLayer = nextGlyph.layers[0]
            else:
                nextLayer = nextGlyph.layers[activeMasterIndex]

            view_scale = thisFont.currentTab.scale

            thisBezierPathWithComponent = nextLayer.completeBezierPath

            save()

            # Apply UPM scaling if needed
            tr = NSAffineTransform.new()
            upm_scale = 1.0
            if thisFont.upm != nextFont.upm:
                upm_scale = thisFont.upm / nextFont.upm
                tr.scaleXBy_yBy_(upm_scale, upm_scale)

            # Slant by Italic Angle difference
            if Glyphs.defaults["comGuidoferreyraShowNextFontMatchAngle"]:
                slant = layer.italicAngle - nextLayer.italicAngle
                if abs(slant) > 0.1:
                    half_x_height = upm_scale * nextLayer.master.xHeight * 0.5
                    tr.shearXBy_yBy_atCenter_(
                        tan(radians(slant)), 0, (0, half_x_height)
                    )

            # Center width if requested
            shift = 0
            if Glyphs.defaults["comGuidoferreyraShowNextFontCenter"]:
                shift = (layer.width - nextLayer.width * upm_scale) * 0.5
                tr.translateXBy_yBy_(shift / upm_scale, 0)

            thisBezierPathWithComponent.transformUsingAffineTransform_(tr)

            # Draw the main path with components
            if thisBezierPathWithComponent:
                if Glyphs.defaults["comGuidoferreyraShowNextFontFill"]:
                    Glyphs.colorDefaults["comGuidoferreyraShowNextFontColor"].set()
                    thisBezierPathWithComponent.fill()
                else:
                    (
                        Glyphs.colorDefaults["comGuidoferreyraShowNextFontColor"]
                        or fallbackColor()
                    ).colorWithAlphaComponent_(0.9).set()
                    thisBezierPathWithComponent.setLineWidth_(0)
                    thisBezierPathWithComponent.stroke()

                # Draw nodes and handles if enabled
                if Glyphs.defaults["comGuidoferreyraShowNextFontShowNodes"]:
                    self.drawNodesAndHandles(nextLayer, view_scale, tr)

            if Glyphs.defaults["comGuidoferreyraShowNextFontShowAnchors"]:
                self.drawAnchors(nextLayer, view_scale, tr)

            restore()

            if Glyphs.defaults["comGuidoferreyraShowNextFontShowSidebearings"]:
                save()
                if Glyphs.defaults["comGuidoferreyraShowNextFontMatchAngle"]:
                    tr = NSAffineTransform.alloc().init()
                    slant = layer.italicAngle
                    if abs(slant) > 0.1:
                        half_x_height = upm_scale * nextLayer.master.xHeight * 0.5
                        tr.shearXBy_yBy_atCenter_(
                            tan(radians(slant)), 0, (0, half_x_height)
                        )
                    tr.concat()
                self.drawSideBearings(layer, nextLayer, view_scale, upm_scale, shift)
                restore()

        except Exception as e:  # noqa: BLE001
            print(e)

    @objc.python_method
    def drawSideBearings(
        self,
        thisLayer: "GSLayer",
        nextLayer: "GSLayer",
        view_scale: float,
        upm_scale: float,
        shift_x: float,
    ) -> None:
        try:
            line_width = 1 / view_scale
            color = (
                Glyphs.colorDefaults["comGuidoferreyraShowNextFontColor"]
                or fallbackColor()
            ).colorWithAlphaComponent_(0.7)
            x0 = shift_x
            x1 = nextLayer.width * upm_scale + shift_x
            y0 = thisLayer.descender
            y1 = thisLayer.ascender
            self.drawLine(x0, y0, x0, y1, line_width, color)
            self.drawLine(x1, y0, x1, y1, line_width, color)
        except Exception as e:  # noqa: BLE001
            print(f"Error sidebearings: {e}")

    @objc.python_method
    def drawAnchors(
        self,
        nextLayer: "GSLayer",
        view_scale: float,
        transform: NSAffineTransform,
    ) -> None:
        try:
            size = 8 / view_scale
            lineWidth = 1 / view_scale
            (
                Glyphs.colorDefaults["comGuidoferreyraShowNextFontColor"]
                or fallbackColor()
            ).colorWithAlphaComponent_(0.7).set()
            path = NSBezierPath.alloc().init()
            for anchor in nextLayer.anchors:
                pt = transform.transformPoint_(anchor.position)
                rect = NSRect((pt.x - size / 2, pt.y - size / 2), (size, size))
                ovalInRect = NSBezierPath.bezierPathWithOvalInRect_(rect)
                path.appendBezierPath_(ovalInRect)
            path.setLineWidth_(lineWidth)
            path.stroke()

        except Exception as e:  # noqa: BLE001
            print(f"Error anchors: {e}")

    @objc.python_method
    def drawNodesAndHandles(
        self,
        nextLayer: "GSLayer",
        view_scale: float,
        transform: NSAffineTransform,
    ) -> None:
        try:
            oncurveColor = (
                Glyphs.colorDefaults["comGuidoferreyraShowNextFontColor"]
                or fallbackColor()
            ).colorWithAlphaComponent_(0.9)
            offcurveColor = (
                Glyphs.colorDefaults["comGuidoferreyraShowNextFontColor"]
                or fallbackColor()
            ).colorWithAlphaComponent_(0.7)
            handleLineColor = (
                Glyphs.colorDefaults["comGuidoferreyraShowNextFontColor"]
                or fallbackColor()
            ).colorWithAlphaComponent_(0.4)

            nodeSize = 8 / view_scale
            handleLineWidth = 1 / view_scale

            for path in nextLayer.paths:
                for node in path.nodes:
                    pt = transform.transformPoint_(node.position)
                    x = pt.x
                    y = pt.y
                    if node.type == OFFCURVE:
                        self.drawNode(x, y, nodeSize * 0.6, offcurveColor)
                    else:
                        self.drawNode(x, y, nodeSize, oncurveColor)
                        for adjacent in (node.nextNode, node.prevNode):
                            if adjacent.type == OFFCURVE:
                                pt = transform.transformPoint_(adjacent.position)
                                self.drawLine(
                                    x,
                                    y,
                                    pt.x,
                                    pt.y,
                                    handleLineWidth,
                                    handleLineColor,
                                )

                    # self.drawHandleLines(nodes, handleLineWidth, handleLineColor)

        except Exception as e:  # noqa: BLE001
            print(f"Error drawing nodes and handles: {e}")

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
            view_scale = thisFont.currentTab.scale
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
                        otherCurrentTab.scale = view_scale
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

        if Glyphs.versionNumber < 4.0:
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
                        "name": Glyphs.localize({"en": "Fill Next Font"}),
                        "action": self.toggleFill,
                    },
                )
            else:
                contextMenus.append(
                    {
                        "name": Glyphs.localize({"en": "Outline Next Font"}),
                        "action": self.toggleFill,
                    },
                )

            # Show/Hide nodes toggle
            if Glyphs.defaults["comGuidoferreyraShowNextFontShowNodes"]:
                contextMenus.append(
                    {
                        "name": Glyphs.localize({"en": "Hide Nodes"}),
                        "action": self.toggleNodes,
                    },
                )
            else:
                contextMenus.append(
                    {
                        "name": Glyphs.localize({"en": "Show Nodes"}),
                        "action": self.toggleNodes,
                    },
                )

        # Execute only if layers are actually selected
        if Glyphs.font.selectedLayers:
            contextMenus.append(
                {
                    "name": Glyphs.localize({"en": "Sync Edit Views"}),
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

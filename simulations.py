import xml.etree.ElementTree


class SVG(xml.etree.ElementTree.Element):
    def __str__(self):
        return xml.etree.ElementTree.tostring(
            svg.svg(
                self._builder.__getattr__("defs")(*self._builder.defs),
                self,
                **self._builder._svg_attributes
            )
        ).decode()

    def _repr_svg_(self):
        return str(self)


class SVGBuilder:
    def __init__(self, **attributes):
        self._svg_attributes = dict(version="1.1", xmlns="http://www.w3.org/2000/svg")
        self._svg_attributes.update(attributes)
        self.defs = []

    def __getattr__(self, tag):
        def build(*children, **attributes):
            text = []
            out = SVG(
                tag,
                {
                    key.rstrip("_").replace("_", "-"): str(value)
                    for key, value in attributes.items()
                },
            )
            for child in children:
                if isinstance(child, xml.etree.ElementTree.Element):
                    out.append(child)
                else:
                    text.append(str(child))
            out.text = "".join(text)
            out._builder = self
            return out

        return build

    def __call__(self, points):
        return " ".join(
            " ".join(map(str, x)) if isinstance(x, tuple) else str(x) for x in points
        )


svg = SVGBuilder(width="400px", height="400px", viewBox="0 0 450 450")

arrow = svg.marker(
    svg.path(d=svg([("M", 0, 0), ("L", 30, 15), ("L", 0, 30), ("L", 5, 15), ("z",)])),
    id_="arrow",
    viewBox="0 0 30 30",
    refX=15,
    refY=15,
    markerWidth=10,
    markerHeight=10,
    orient="auto-start-reverse",
)
svg.defs.append(arrow)


def show(world):
    out = svg.g()
    for i, row in enumerate(world):
        for j, cell in enumerate(row):
            fill = "orange" if cell else "lightblue"
            out.append(
                svg.rect(
                    x=40 * j + 5,
                    y=40 * i + 5,
                    width=35,
                    height=35,
                    stroke="black",
                    fill=fill,
                )
            )
    return out


def label_axis(g, labels=("time", "space")):
    g.extend(
        [
            svg.path(
                d=svg([("M", 415, 10), ("L", 415, 385)]),
                stroke="black",
                marker_end="url(#arrow)",
            ),
            svg.text(
                labels[0],
                font_size="20",
                text_anchor="middle",
                dominant_baseline="hanging",
                transform="translate(425, 200) rotate(-90)",
            ),
            svg.path(
                d=svg([("M", 10, 415), ("L", 385, 415)]),
                stroke="black",
                marker_end="url(#arrow)",
            ),
            svg.text(
                labels[1],
                font_size="20",
                text_anchor="middle",
                dominant_baseline="hanging",
                transform="translate(200, 425)",
            ),
        ]
    )
    return g


def arrow_down(g, i, j):
    g.append(
        svg.path(
            d=svg([("M", 40 * j + 25, 40 * i + 25), ("L", 40 * j + 25, 40 * i + 55)]),
            stroke="black",
            marker_end="url(#arrow)",
        )
    )


def arrow_right(g, i, j):
    g.append(
        svg.path(
            d=svg([("M", 40 * j + 25, 40 * i + 25), ("L", 40 * j + 55, 40 * i + 25)]),
            stroke="black",
            marker_end="url(#arrow)",
        )
    )


def arrow_down_right(g, i, j):
    g.append(
        svg.path(
            d=svg([("M", 40 * j + 25, 40 * i + 25), ("L", 40 * j + 55, 40 * i + 55)]),
            stroke="black",
            marker_end="url(#arrow)",
        )
    )


__all__ = ["show", "label_axis", "arrow_down", "arrow_right", "arrow_down_right"]

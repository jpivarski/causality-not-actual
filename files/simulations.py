import ast
import xml.etree.ElementTree


class SVG(xml.etree.ElementTree.Element):
    def __str__(self):
        return xml.etree.ElementTree.tostring(
            svg.svg(
                self._builder.__getattr__("defs")(*self._builder.defs),
                self,
                **self._builder._svg_attributes,
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


class Computation:
    def __init__(self, label, dependencies):
        self.label = label
        self.dependencies = dependencies

    def __repr__(self):
        if len(self.dependencies) == 0:
            return f"<Computation {self.label!r} has no dependencies>"
        else:
            return f"<Computation {self.label!r} depends on {', '.join(repr(x) for x in self.dependencies)}>"


class PythonToGraph(ast.NodeVisitor):
    def __init__(self):
        self.symbol_table = {}
        self.final_results = []

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            this = ast.unparse(node)
            if this not in self.symbol_table:
                self.symbol_table[this] = Computation(this, [])
            if this in self.final_results:
                self.final_results.remove(this)

    def visit_Call(self, node):
        assert isinstance(node.func, ast.Name), "not implemented"
        this = ast.unparse(node)
        args = []
        for arg in node.args:
            self.visit(arg)
            args.append(ast.unparse(arg))
        self.symbol_table[this] = Computation(this, args)

    def visit_Constant(self, node):
        this = ast.unparse(node)
        self.symbol_table[this] = Computation(this, [])

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        this = ast.unparse(node)
        arg = ast.unparse(node.operand)
        self.symbol_table[this] = Computation(this, [arg])

    def visit_BinOp(self, node):
        self.generic_visit(node)
        this = ast.unparse(node)
        left = ast.unparse(node.left)
        right = ast.unparse(node.right)
        self.symbol_table[this] = Computation(this, [left, right])

    def visit_Assign(self, node):
        assert len(node.targets) == 1, "not implemented"
        assert isinstance(node.targets[0], ast.Name), "not implemented"
        assert node.targets[0].id not in self.symbol_table, "not implemented"
        self.generic_visit(node)
        this = node.targets[0].id
        value = ast.unparse(node.value)
        self.symbol_table[this] = Computation(this, [value])
        self.final_results.append(this)


def draw_computation_graph(expression):
    graph = PythonToGraph()
    graph.visit(ast.parse(expression))

    svg2 = SVGBuilder(width=600, height=len(graph.symbol_table) * 50)
    svg2.defs.append(arrow)

    g = svg2.g()
    order = {}
    for i, label in enumerate(graph.symbol_table):
        if label in graph.final_results:
            color = "gold"
        elif len(graph.symbol_table[label].dependencies) == 0:
            color = "ghostwhite"
        else:
            color = "lightyellow"
        g.append(
            svg2.rect(
                x=5, y=50 * i + 12, width=170, height=25, stroke="black", fill=color
            )
        )
        g.append(
            svg2.text(
                label,
                x=90,
                y=50 * i + 24,
                text_anchor="middle",
                dominant_baseline="central",
            )
        )
        order[label] = i

    drawn = set()
    for to_i, label in enumerate(graph.symbol_table):
        for dependency in graph.symbol_table[label].dependencies:
            from_i = order[dependency]
            radius = (to_i - from_i) * 10
            if (from_i, to_i) not in drawn:
                g.append(
                    svg2.path(
                        d=svg2(
                            [
                                ("M", 175, 50 * from_i + 30),
                                ("A", radius, radius, 0, 0, 1, 175, 50 * to_i + 20),
                            ]
                        ),
                        stroke="black",
                        fill="none",
                        marker_end="url(#arrow)",
                    )
                )
            drawn.add((from_i, to_i))

    return g


__all__ = [
    "show",
    "label_axis",
    "arrow_down",
    "arrow_right",
    "arrow_down_right",
    "draw_computation_graph",
]

"""BPMN rendering style definitions."""

# Color palette
COLORS = {
    "startEvent": {"fill": "#E8F5E9", "stroke": "#4CAF50", "stroke_width": 2},
    "endEvent": {"fill": "#FFEBEE", "stroke": "#F44336", "stroke_width": 3},
    "intermediateCatchEvent": {"fill": "#FFF8E1", "stroke": "#FF9800", "stroke_width": 2},
    "intermediateThrowEvent": {"fill": "#FFF8E1", "stroke": "#FF9800", "stroke_width": 2},
    "boundaryEvent": {"fill": "#FFF8E1", "stroke": "#FF9800", "stroke_width": 2},
    "task": {"fill": "#E3F2FD", "stroke": "#1976D2", "stroke_width": 1.5},
    "userTask": {"fill": "#E3F2FD", "stroke": "#1976D2", "stroke_width": 1.5},
    "serviceTask": {"fill": "#F3E5F5", "stroke": "#7B1FA2", "stroke_width": 1.5},
    "scriptTask": {"fill": "#E0F2F1", "stroke": "#00796B", "stroke_width": 1.5},
    "businessRuleTask": {"fill": "#FFF3E0", "stroke": "#E65100", "stroke_width": 1.5},
    "sendTask": {"fill": "#E8EAF6", "stroke": "#283593", "stroke_width": 1.5},
    "receiveTask": {"fill": "#E8EAF6", "stroke": "#283593", "stroke_width": 1.5},
    "manualTask": {"fill": "#EFEBE9", "stroke": "#4E342E", "stroke_width": 1.5},
    "callActivity": {"fill": "#E3F2FD", "stroke": "#1565C0", "stroke_width": 2.5},
    "subProcess": {"fill": "#FAFAFA", "stroke": "#616161", "stroke_width": 1.5},
    "exclusiveGateway": {"fill": "#FFF9C4", "stroke": "#F9A825", "stroke_width": 2},
    "parallelGateway": {"fill": "#FFF9C4", "stroke": "#F9A825", "stroke_width": 2},
    "inclusiveGateway": {"fill": "#FFF9C4", "stroke": "#F9A825", "stroke_width": 2},
    "eventBasedGateway": {"fill": "#FFF9C4", "stroke": "#F9A825", "stroke_width": 2},
    "complexGateway": {"fill": "#FFF9C4", "stroke": "#F9A825", "stroke_width": 2},
    "participant": {"fill": "#FAFAFA", "stroke": "#424242", "stroke_width": 1.5},
    "sequenceFlow": {"stroke": "#616161", "stroke_width": 1.5},
    "messageFlow": {"stroke": "#616161", "stroke_width": 1.5},
    "association": {"stroke": "#9E9E9E", "stroke_width": 1},
}

DEFAULT_STYLE = {"fill": "#E3F2FD", "stroke": "#1976D2", "stroke_width": 1.5}
FLOW_DEFAULT = {"stroke": "#616161", "stroke_width": 1.5}

FONT_FAMILY = "'Noto Sans CJK SC', 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 'Hiragino Sans GB', Arial, Helvetica, sans-serif"
FONT_SIZE_NODE = 12
FONT_SIZE_EDGE = 10
FONT_COLOR = "#333333"
BACKGROUND_COLOR = "#FFFFFF"

# Gateway marker symbols
GATEWAY_MARKERS = {
    "exclusiveGateway": "X",
    "parallelGateway": "+",
    "inclusiveGateway": "O",
    "eventBasedGateway": "⬠",
    "complexGateway": "✱",
}

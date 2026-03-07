{
  "schema_version": "1.1",
  "drawing_type": "空间平面布点",
  "layout_data": {
    "space": {
      "count": 1,
      "name": "标准型接报案室",
      "size": {
        "length_m": 6,
        "width_m": 4,
        "height_m": 3
      },
      "coordinate_system": {
        "origin": "top_left",
        "x_direction": "right",
        "y_direction": "down"
      }
    },
    "fixed_elements": [
      {
        "name": "接报案台",
        "size": {
          "width_m": 2,
          "depth_m": 0.8
        },
        "position": {
          "anchor": "north",
          "align": "center",
          "offset_m": 0.3
        }
      }
    ],
    "devices": [
      {
        "type": "摄像机",
        "count": 2,
        "install_method": "墙角高位",
        "layout_strategy": "diagonal",
        "constraints": {
          "offset_from_wall_mm": 300,
          "install_height_m": 2.8,
          "target_elements": ["接报案台"],
          "avoid_elements": []
        }
      },
      {
        "type": "拾音器",
        "count": 1,
        "install_method": "桌面固定",
        "layout_strategy": "single_side",
        "constraints": {
          "target_elements": ["接报案台"],
          "avoid_elements": []
        }
      }
    ]
  },
  "validation": {
    "coverage_check": "通过",
    "blind_area_risk": "无明显盲区",
    "structure_conflict": "无",
    "risk_notes": []
  },
  "optimization_suggestions": []
}
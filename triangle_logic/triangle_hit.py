def triangle_normal_components(triangle_data, triangle_index):
    nx_arr = triangle_data["normal_x"]
    ny_arr = triangle_data["normal_y"]
    nz_arr = triangle_data["normal_z"]

    return nx_arr[triangle_index], ny_arr[triangle_index], nz_arr[triangle_index]


def make_triangle_hit_record(triangle_data, triangle_index):
    color_r_arr = triangle_data["color_r"]
    color_g_arr = triangle_data["color_g"]
    color_b_arr = triangle_data["color_b"]

    reflection_arr = triangle_data["reflection"]
    transparency_arr = triangle_data["transparency"]
    ior_arr = triangle_data["ior"]

    return {
        "type": "triangle",
        "triangle_index": triangle_index,
        "color_r": color_r_arr[triangle_index],
        "color_g": color_g_arr[triangle_index],
        "color_b": color_b_arr[triangle_index],
        "reflection": reflection_arr[triangle_index],
        "transparency": transparency_arr[triangle_index],
        "ior": ior_arr[triangle_index],
    }


def hit_record_normal_components(hit_record, triangle_data):
    if hit_record["type"] == "triangle":
        return triangle_normal_components(triangle_data, hit_record["triangle_index"])
    else:
        return None
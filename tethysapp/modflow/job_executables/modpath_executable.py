#!/opt/tethys-python
import flopy
import os
import sys
import shapefile
from json import dumps
import pyproj
import math


def find_hdry(ml):
    if ml.get_package('LPF'):
        hdry = ml.get_package('LPF').hdry
    else:
        hdry = -888
    return hdry


def set_pyproj_env():
    if 'PROJ_LIB' not in os.environ:
        # Set PROJ_LIB environ variable
        os.environ['PROJ_LIB'] = str(os.path.join(pyproj.__file__.split('lib')[0], 'share', 'proj'))
        return 'Set PROJ_LIB Environment Variable'


def create_point_geo(x, y):
    geo = {'type': 'Point', 'coordinates': (float(x), float(y))}
    return geo


def transform(x, y, inprj, outprj):
    if "+" in inprj:
        inprj = pyproj.Proj(str(inprj), preserve_units=True)
    else:
        inprj = pyproj.Proj(init='epsg:' + str(inprj), preserve_units=True)

    if "+" in outprj:
        outprj = pyproj.Proj(str(outprj), preserve_units=True)
    else:
        outprj = pyproj.Proj(init='epsg:' + str(outprj), preserve_units=True)
    x, y = pyproj.transform(inprj, outprj, x, y)
    return x, y


def transform_geom(geom, inprj, outprj):
    coordinates = list(geom['coordinates'])
    index = 0
    for coordinate in coordinates:
        x, y = transform(coordinate[0], coordinate[1], inprj, outprj)
        coordinates[index] = tuple([x, y])
        index += 1
    geom['coordinates'] = tuple(coordinates)
    return geom


def degree_to_radian(x):
    return x * (math.pi / 180)


def coordinate_transformation(xo, yo, x, y, rotation):
    x = x - xo
    y = y - yo
    xt = x * math.cos(rotation) - y * math.sin(rotation)
    yt = x * math.sin(rotation) + y * math.cos(rotation)
    return xt, yt


def modpath_cell_prop(ml, head, xll, yll, x, y, rotation, depth):
    """
    ml: MODFLOW loaded model
    head: head data to find out water surface elevation
    x, y coordinates
    depth: Depth from water surface

    This function returns an array [intersected row, intersected col, local x, local y, local z]
    local x, y , z is the offset in x, y ,z direction

    """  # noqa: E501

    # if x and y are outside model grid, it will select the first cell
    # Get intersected row and col
    if rotation == 0:
        rc = ml.sr.get_rc(x=x, y=y)
        row = rc[0]
        col = rc[1]
    else:
        xa = abs(ml.sr.xul - x)
        ya = abs(ml.sr.yul - y)
        rr = degree_to_radian(rotation)
        y_length = ya / math.cos(rr) + (xa - ya * math.tan(rr)) * math.sin(rr)
        x_length = (xa - ya * math.tan(rr)) * math.cos(rr)

        x_grid_length = 0
        y_grid_length = 0
        scol = 0
        srow = 0
        for del_x in ml.dis.delr:
            x_grid_length += del_x
            if x_grid_length >= x_length:
                break
            else:
                scol += 1
        for del_y in ml.dis.delc:
            y_grid_length += del_y
            if y_grid_length >= y_length:
                break
            else:
                srow += 1
        col = scol
        row = srow

    # Get the vertices of the instersected node to find the offset
    vertices = ml.sr.get_vertices(i=row, j=col)
    distance_list = []
    for vertice in vertices:
        distance = math.sqrt((vertice[0] - xll) ** 2 + (vertice[1] - yll) ** 2)
        distance_list.append(distance)
    max_distance = max(distance_list)
    max_index = distance_list.index(max_distance)
    min_distance = min(distance_list)
    min_index = distance_list.index(min_distance)
    vertice_x_min = vertices[min_index][0]
    vertice_y_min = vertices[min_index][1]
    vertice_x_max = vertices[max_index][0]
    vertice_y_max = vertices[max_index][1]

    # Calculate roff and coff
    # Perform coodinate transform
    rotation_rad = degree_to_radian(-rotation)
    x1, y1 = coordinate_transformation(vertice_x_min, vertice_y_min, x, y, rotation_rad)
    vertice_x1_min, vertice_y1_min = coordinate_transformation(vertice_x_min, vertice_y_min, vertice_x_min,
                                                               vertice_y_min, rotation_rad)
    vertice_x1_max, vertice_y1_max = coordinate_transformation(vertice_x_min, vertice_y_min, vertice_x_max,
                                                               vertice_y_max, rotation_rad)

    loc_x = float((x1 - vertice_x1_min) / (vertice_x1_max - vertice_x1_min))
    loc_y = float((y1 - vertice_y1_min) / (vertice_y1_max - vertice_y1_min))

    if abs(loc_x) > 1 or abs(loc_y) > 1:
        raise Exception('The point is outside the model boundary')
    hdry = find_hdry(ml)
    # Get water level
    for i in range(ml.nlay):
        top_sat = head.get_data(mflay=(ml.nlay - i - 1))[row][col]
        if top_sat != hdry:
            break

    # Get partical elevation
    particle_elev = top_sat - depth

    # Get layer_number from particle_elev (zero-based)
    layer_number = ml.dis.get_layer(row, col, particle_elev)

    # Get top_elev from the cell intersected with particle
    if layer_number == 0:
        top_elev = ml.dis.gettop()[row][col]
    else:
        top_elev = ml.dis.getbotm()[layer_number - 1][row][col]

    bot_elev = ml.dis.getbotm()[layer_number][row][col]

    thickness = top_elev - bot_elev
    sat_thickness = top_sat - bot_elev
    if depth > sat_thickness:
        depth = sat_thickness

    if layer_number == 0:
        loc_z = (sat_thickness - depth) / thickness
    else:
        loc_z = (particle_elev - bot_elev) / (top_elev - bot_elev)
    if loc_z > 1:
        loc_z = 1
    return [layer_number, row, col, loc_x, loc_y, loc_z]


def find_out_fnames(ml, ext):
    modflow_out_file = ""
    output_fnames = ml.output_fnames
    for output_fname in output_fnames:
        if output_fname.split(".")[-1] == ext:
            modflow_out_file = output_fname
    return modflow_out_file


def run(session_id, workflow_id, user_ws, modflow_exe, modpath_exe, modpath_version, data_path, modflow_nam,
        model_epsg, xll, yll, rotation, lon, lat, depth, geo_prj, depth_field):
    """
    Run MODPATH model

    Args:
        modflow_exe: path to MODFLOW executable file.
        modpath_exe: path to MODPATH executable file.
        modpath_version: for version 7 use 'modpath7'.
        data_path: path to data model files.
        modflow_nam: MODFLOW name file with extension.
        model_epsg: prj string (ESPG).
        xll: x-coordinate at lower left corner for spacial reference.
        yll: y-coordinate at lower left corner for spacial reference.
        rotation: model rotation
        lon: lon of point
        lat: lat of point
        depth: Depth of the modpath point
        geo_prj: projection of geojson file
        depth_field: depth field name in the geojson file

    """  # noqa: E501

    set_pyproj_env()

    exe_name = modflow_exe
    mp_exe_name = modpath_exe
    base_name = os.path.splitext(modflow_nam)[0]
    ws = data_path

    # Load Existing MODFLOW model
    ml = flopy.modflow.Modflow.load(modflow_nam, model_ws=ws, check=False, exe_name=exe_name)

    prj = flopy.utils.reference.getproj4(model_epsg)

    # Spatial Reference
    sr = flopy.utils.reference.SpatialReference(delr=ml.dis.delr, delc=ml.dis.delc, xll=float(xll),
                                                yll=float(yll), rotation=rotation, proj4_str=prj)
    ml.sr = sr

    ml.write_input()

    # Simulated Head
    modflow_hds = find_out_fnames(ml, "hds")
    head_file = os.path.join(data_path, modflow_hds)

    # Simulated CBB
    budget_base = find_out_fnames(ml, "cbb")
    if budget_base == "":
        budget_base = find_out_fnames(ml, "cbc")
    cbb_file = os.path.join(data_path, budget_base)

    if not (os.path.exists(head_file) and os.path.exists(cbb_file)):
        ml.run_model(silent=True)

    head = flopy.utils.HeadFile(head_file)

    # Blank buffer to export to geojson
    buffer = []

    # MODPATH
    plocs = []

    particlegroups = list()

    x = lon
    y = lat
    # Append point to buffer
    buffer.append(
        dict(type="Feature", geometry=create_point_geo(x, y), properties={'attribute': 'starting_point'}))

    x, y = transform(x, y, geo_prj, model_epsg)
    try:
        depth = depth
    except KeyError:
        depth = 0

    # Need to find out the k for multilayer model in the future
    cell_prop = modpath_cell_prop(ml, head, float(xll), float(yll), float(x), float(y), float(rotation), float(depth))
    plocs.append((cell_prop[0], cell_prop[1], cell_prop[2]))
    s1_part = flopy.modpath.ParticleData(plocs, drape=0, structured=True,
                                         localx=cell_prop[3], localy=cell_prop[4], localz=cell_prop[5])

    # Create particle group, data will be write in the .sloc file
    particle_name = 'flow_path'
    particle_file = particle_name + ".sloc"
    particlegroups.append(flopy.modpath.ParticleGroup(particlegroupname=particle_name, particledata=s1_part,
                                                      filename=particle_file))

    # Create and Run MODPATH 7
    mp = flopy.modpath.mp7.Modpath7(modelname=base_name, flowmodel=ml, version=modpath_version, exe_name=mp_exe_name,
                                    model_ws=ws)

    # Define MODPATH basic package
    flopy.modpath.Modpath7Bas(mp, porosity=float(0.3))

    direction_list = ['forward', 'backward']
    for direction in direction_list:
        flopy.modpath.Modpath7Sim(mp, trackingdirection=direction, particlegroups=particlegroups)

        # Write the input and run model
        mp.write_input()
        mp.run_model()

        # Make a copy of mppth file
        mppth = os.path.join(data_path, base_name + '.mppth')

        # Read in the modpath pathline and export to shapefile.
        pthobj = flopy.utils.PathlineFile(mppth)
        shpname = os.path.join(data_path, particle_name + "_" + direction + ".shp")
        pthobj.write_shapefile(shpname=shpname, one_per_particle=False, sr=sr, proj4_str=prj)

        reader = shapefile.Reader(shpname)
        fields = reader.fields[1:]
        fields_name = [field[0] for field in fields]

        for shaperecord in reader.shapeRecords():
            atr = dict(zip(fields_name, shaperecord.record))
            atr['direction'] = direction
            geom = shaperecord.shape.__geo_interface__
            geom = transform_geom(geom, prj, geo_prj)
            buffer.append(dict(type="Feature", geometry=geom, properties=atr))

    geojson = open(os.path.join(particle_name + ".json"), "w")
    geojson.write(dumps({"type": "FeatureCollection", "features": buffer}, indent=2) + "\n")
    geojson.close()


if __name__ == "__main__":
    args = sys.argv
    args.pop(0)
    run(*args)

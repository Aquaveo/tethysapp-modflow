#!/opt/tethys-python
import flopy
import sys
import os
import numpy as np
import pyproj
from shapely.geometry import Polygon
from geojson import Feature, FeatureCollection, dump
import json
import flopy.utils.binaryfile as bf
import shapefile
import math


def set_pyproj_env():
    if not hasattr(os.environ, 'PROJ_LIB'):
        print('attempt so set PROJ_LIB env')
        os.environ['PROJ_LIB'] = str(os.path.join(pyproj.__file__.split('lib')[0], 'share', 'proj'))
        print('successfully set set PROJ_LIB env')
        return 'Set PROJ_LIB Environment Variable'


def sp_start_end_time_extractor(sp, ml):
    """
    :param sp: Stress Period we want to extract - based 0
    :param ml: flopy modflow model
    :return: list [start_time, end_time]
    """
    start_time = 0
    end_time = 0
    for number_sp in range(sp):
        if number_sp == 0:
            start_time = 0
            end_time = ml.dis.perlen[sp]
        else:
            start_time = end_time
            end_time = start_time + ml.dis.perlen[sp]

    return start_time, end_time


def pumping_rate_extractor(flowrate_string, sp,  ml):
    """
    :param flowrate_string: Flow rate String
    :param sp: Stress Period which flow rate need to be extracted - based 0
    :param ml: flopy modflow model
    :return: Pumping rate value for a given stress period
    """
    flowrate_list = flowrate_string.split(";")
    start_time_stress_period, end_time_stress_period = sp_start_end_time_extractor(sp, ml)
    flowrate = 0
    if start_time_stress_period == end_time_stress_period:
        return flowrate
    else:
        for i in range(len(flowrate_list)):
            if i + 1 < len(flowrate_list):
                flowrate_data = flowrate_list[i].split(',')
                flowrate_data_next = flowrate_list[i+1].split(',')
                start_time_flow = float(flowrate_data[0])
                start_time_flow_next = float(flowrate_data_next[0])
                end_time_flow = float(flowrate_data_next[0])
                if start_time_stress_period <= start_time_flow < end_time_stress_period:
                    if end_time_flow < end_time_stress_period:
                        flowrate += float(flowrate_data[1])*(end_time_flow - start_time_flow) /\
                                    (end_time_stress_period - start_time_stress_period)
                    else:
                        flowrate += float(flowrate_data[1])*(end_time_stress_period - start_time_flow)\
                                    / (end_time_stress_period - start_time_stress_period)
                elif start_time_flow <= start_time_stress_period:
                    if start_time_stress_period <= start_time_flow_next < end_time_stress_period:
                        flowrate += float(flowrate_data[1])*(start_time_flow_next - start_time_stress_period)\
                                        / (end_time_stress_period - start_time_stress_period)
                    elif start_time_flow_next >= end_time_stress_period and start_time_flow <= start_time_stress_period:
                        flowrate = float(flowrate_data[1])
            else:
                flowrate += 0
    return flowrate


def associate_stress_period(time, ml):
    """
    :param time: tim
    :param ml:
    :return: the stress period the time belongs to
    """

    sp_time_length = 0
    for sp in range(ml.nper):
        sp_time_length += ml.dis.perlen[sp]
        if time <= sp_time_length:
            return sp
    return sp


def degree_to_radian(x):
    return x*(math.pi/180)


def rcl(ml, x, y, rotation, z, z_type):
    """
    ml: MODFLOW loaded model
    x, y coordinates
    z: elevation or depth if z_type is 'depth'
    depth: Depth from top surface

    This function returns an array [intersected row, intersected col]
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
        y_length = ya/math.cos(rr) + (xa - ya*math.tan(rr))*math.sin(rr)
        x_length = (xa - ya*math.tan(rr))*math.cos(rr)
        # Assume square grid
        grid_length = ml.dis.delc[0]

        col = math.floor(x_length/grid_length)
        row = math.floor(y_length/grid_length)

    if z_type.lower() == 'depth':
        top_elev = float(ml.dis.gettop()[row][col])
        z = top_elev - z
    lay = flopy.modflow.mfdis.get_layer(ml.dis, row, col, z)

    return [row, col, lay]


def cal_pumping_data(ml, polygon, layer, total_pump):
    # Get boundary
    boundary = polygon.bounds
    rc_upper_left = ml.sr.get_rc(x=boundary[0], y=boundary[3])
    rc_bottom_right = ml.sr.get_rc(x=boundary[2], y=boundary[1])

    row_min = rc_upper_left[0]
    col_min = rc_upper_left[1]

    row_max = rc_bottom_right[0]
    col_max = rc_bottom_right[1]

    stress_period_data = []
    for row in range(row_min, row_max + 1):
        for col in range(col_min, col_max + 1):
            vertices = ml.sr.get_vertices(row, col)
            check_poly = Polygon(vertices)
            if check_poly.intersects(polygon):
                intersected_percentage = check_poly.intersection(polygon).area / polygon.area
                pumping_value = float(total_pump) * intersected_percentage
                stress_period_data.append([layer, row, col, pumping_value])

    return stress_period_data


def transform(x, y, inprj, outprj):
    if "+" in inprj:
        inprj = pyproj.Proj(str(inprj), preserve_units=True)
    else:
        inprj = pyproj.Proj('epsg:' + str(inprj), preserve_units=True)

    if "+" in outprj:
        outprj = pyproj.Proj(str(outprj), preserve_units=True)
    else:
        outprj = pyproj.Proj('epsg:' + str(outprj), preserve_units=True)
    x, y = pyproj.transform(inprj, outprj, x, y, always_xy=True)
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


def polygon_area(xlist, ylist, n):
    # python3 program to evaluate
    # area of a polygon using
    # shoelace formula
    # (xlist[i], ylist[i]) are coordinates of i'th point.
    # Initialze area
    area = 0.0

    # Calculate value of shoelace formula
    j = n - 1
    for i in range(0, n):
        area += (xlist[j] + xlist[i]) * (ylist[j] - ylist[i])
        j = i  # j is previous vertex to i

    # Return absolute value
    return int(abs(area / 2.0))


def line_to_polygon(geom):
    geo_polygon = {}
    geo_polygon['type'] = 'Polygon'
    geo_polygon['coordinates'] = [[]]
    for coordinate in geom['coordinates']:
        geo_polygon['coordinates'][0].append([coordinate[0], coordinate[1]])
    # geo_polygon['coordinates'][0].append([geom['coordinates'][0][0], geom['coordinates'][0][1]])
    return geo_polygon


def find_out_fnames(ml, ext):
    modflow_out_file = ""
    output_fnames = ml.output_fnames
    for output_fname in output_fnames:
        if output_fname.split(".")[-1] == ext:
            modflow_out_file = output_fname
    return modflow_out_file


def extract_modflow_data(modflow_data, package, nper, nlay):
    modflow_data_list = list()
    for lay in range(nlay):
        modflow_data_list.append(list())
        for per in range(nper):
            # kstpkper(time step, stress period)
            if package:
                modflow_data_list[lay].append(np.array(modflow_data.get_data(text=package, kstpkper=(0, per))[0][lay]))
            else:
                modflow_data_list[lay].append(np.array(modflow_data.get_data(kstpkper=(0, per), mflay=int(lay))))
    return modflow_data_list


def calculate_data_diff(data_base, data_new, nper, nlay, data_type='float'):
    data_diff = list()
    for layer in range(nlay):
        data_diff.append(list())
        for per in range(nper):
            if data_type == 'float':
                data_diff[layer].append((data_base[layer][per] - data_new[layer][per]).astype(float))
            else:
                data_diff[layer].append((data_base[layer][per] - data_new[layer][per]).astype(int))
    return data_diff


def run(modflow_exe, data_path, modflow_nam, modflow_hds, modflow_wel, model_prj, xll, yll, rotation, geo_prj,
        contour_levels="0.1", export_layer_string="", export_sp_string=""):
    """
    Run MODFLOW model

    Args:
        modflow_exe: path to MODFLOW executable file
        data_path: path to MODFLOW model files
        modflow_nam: MODFLOW name file with extension
        modflow_wel: Name of the well file
        model_prj: projection of the model
        xll: x-coordinate of the lower left conner
        yll: y-coordinate of the lower left conner
        rotation: grid rotation in degrees (counter clockwise).
        geo_prj: output projection
        contour_levels: Drawdown Contour Levels - Comma separated list of drawdown contour levels. Up to 5 levels
         (ex: 1, 5, 10, 15)
        shape_type(Point or Polygon): Type of geometry shape in the output. Point is at center of the cell. Polygon is
        for the cell itself. Default is Point
        details: "All" is to print before and after data. If nothing is specified, it will only print the
        differences (before - after). Default is only to write out the differences.
        stream_transformation_name: name of the stream_transformation_file.
        std_minimum_change: Threshold for changes in streamflow in percentage.
        package: package in cell to cell budget file
        export_layer_string: layer to export
        export_sp_string: stress period to export
         Wont' write out data if less than this value.
    """  # noqa: E501

    set_pyproj_env()
    exe_name = modflow_exe
    ws = data_path

    # Load Existing MODFLOW model
    ml = flopy.modflow.Modflow.load(modflow_nam, model_ws=ws, check=False, exe_name=exe_name)

    # Spatial Reference
    sr = flopy.utils.reference.SpatialReference(delr=ml.dis.delr, delc=ml.dis.delc, xll=float(xll),
                                                yll=float(yll), rotation=float(rotation), epsg=int(model_prj))
    ml.sr = sr
    # Don't use compact
    ml.oc.compact = False

    if not export_sp_string:
        export_sp_string = str(ml.dis.nper)
    # Write New Input Files
    if ml.upw:
        upw_file = os.path.join(data_path, ml.upw.file_name[0])
        flopy.modflow.ModflowUpw.load(upw_file, ml)
    ml.write_input()

    ml.run_model(silent=False)
    # Load head and budget files from existing model
    modflow_hds = find_out_fnames(ml, "hds")

    path_to_head_file = os.path.join(data_path, modflow_hds)

    # Get the base head from timestep 1 of the last stress period in top layer
    head_base_data = extract_modflow_data(bf.HeadFile(os.path.join(data_path, modflow_hds)),
                                          '', ml.dis.nper, ml.dis.nlay)
    # Load GeoJson Data
    geojson_file = os.path.join(ws, 'well_impact.json')
    with open(geojson_file) as f:
        data = json.load(f)

    sp_data = list()
    for feature in data['features']:
        flowrate = feature['properties'].get('Flowrate', 0)
        flow_factor = float(feature['properties'].get('Pumpfactor', 0))

        if feature['geometry']['type'] == 'Point':
            x = float(feature['geometry']['coordinates'][0])
            y = float(feature['geometry']['coordinates'][1])
            z = float(feature['geometry']['coordinates'][2])
            x, y = transform(x, y, geo_prj, model_prj)

            row, col, lay = rcl(ml, x, y, float(rotation), z, 'depth')
            sp_data.append([lay, row, col, flowrate])

        elif feature['geometry']['type'] == 'Polygon':
            # Reproject and build shapely polygon
            polygon_point_list = []
            for point in feature['geometry']['coordinates'][0]:
                x = float(point[0])
                y = float(point[1])
                x, y = transform(x, y, geo_prj, model_prj)
                polygon_point_list.append([x, y])
            polygon = Polygon(polygon_point_list)
            polygon_wells = cal_pumping_data(ml, polygon, 0, flowrate)
            for polygon_well in polygon_wells:
                sp_data.append(polygon_well)

    # Check if we need to append data to existing well, otherwise, we'll create a new well file.
    if modflow_wel != '_':
        wel_file = os.path.join(data_path, modflow_wel)
        if os.path.isfile(wel_file):
            # Well File with existing data
            wel_o = flopy.modflow.ModflowWel.load(wel_file, ml)
        if ml.nper > 1:
            # append constant rate to the all stress period
            stress_period_data_new = dict()
            ipakcb = ml.wel.ipakcb if ml.wel.ipakcb else 0
            for sp in range(ml.nper):
                # Create data for given stress period
                # Add existing data to well_data list in this sp
                well_data = list()
                flow_rate = 0
                if os.path.isfile(wel_file):
                    for well_number in range(len(wel_o.stress_period_data[sp])):
                        well_data.append([wel_o.stress_period_data[sp][well_number][0],
                                          wel_o.stress_period_data[sp][well_number][1],
                                          wel_o.stress_period_data[sp][well_number][2],
                                          wel_o.stress_period_data[sp][well_number][3]])
                # Append new data into well_data list in this stress period.
                for well_number in range(len(sp_data)):
                    flow_string = sp_data[well_number][3]

                    # Check to see if we should append data in this stress period based on start time and duration.
                    if not flow_string.isnumeric():
                        flow_rate = pumping_rate_extractor(flow_string, sp, ml)
                    # Apply to stress period if no start_time and duration is specified
                    else:
                        flow_rate = float(sp_data[well_number][3])
                    flow_rate = flow_factor * flow_rate
                    # Handle polygon case, we need to multiply with the intersected polygon
                    if len(sp_data[well_number]) == 5:
                        flow_rate = flow_rate * sp_data[well_number][4]
                    well_data.append([sp_data[well_number][0], sp_data[well_number][1],
                                      sp_data[well_number][2], flow_rate])
                stress_period_data_new[sp] = well_data
            flopy.modflow.ModflowWel(ml, stress_period_data=stress_period_data_new, ipakcb=ipakcb)
        else:
            constant_sp_data = list()
            for constant_flow_data in sp_data:
                constant_sp_data.append([constant_flow_data[0], constant_flow_data[1], constant_flow_data[2],
                                         flow_factor * float(constant_flow_data[3])])
            if os.path.isfile(wel_file):
                flopy.modflow.ModflowWel(ml, stress_period_data=wel_o.stress_period_data
                                         .append(constant_sp_data))
            else:
                flopy.modflow.ModflowWel(ml, stress_period_data=constant_sp_data)
    else:
        # Create new well file
        if ml.nper > 1:
            stress_period_data_new = dict()
            for sp in range(ml.nper):
                well_data = list()
                for well_number in range(len(sp_data)):
                    flow_string = sp_data[well_number][3]

                    # Check to see if we should append data in this stress period based on start time and duration.
                    if not flow_string.isnumeric():
                        flow_rate = pumping_rate_extractor(flow_string, sp, ml)
                    # Apply to stress period if no start_time and duration is specified
                    else:
                        flow_rate = float(sp_data[well_number][3])
                    flow_rate = flow_factor * flow_rate
                    # Handle polygon case, we need to multiply with the intersected polygon
                    if len(sp_data[well_number]) == 5:
                        flow_rate = flow_rate * sp_data[well_number][4]
                    well_data.append([sp_data[well_number][0], sp_data[well_number][1],
                                      sp_data[well_number][2], flow_rate])
                stress_period_data_new[sp] = well_data
            flopy.modflow.ModflowWel(ml, stress_period_data=stress_period_data_new)
        else:
            constant_sp_data = list()
            for constant_flow_data in sp_data:
                constant_sp_data.append([constant_flow_data[0], constant_flow_data[1], constant_flow_data[2],
                                         flow_factor * float(constant_flow_data[3])])
            flopy.modflow.ModflowWel(ml, stress_period_data=constant_sp_data)
    # Write New Input Files
    if ml.upw:
        upw_file = os.path.join(data_path, ml.upw.file_name[0])
        flopy.modflow.ModflowUpw.load(upw_file, ml)
    ml.write_input()

    ml.run_model(silent=False)

    if not export_layer_string:
        # export all layers
        for x in range(ml.dis.nlay):
            export_layer_string += str(x + 1) + ","
        if export_layer_string[-1] == ",":
            export_layer_string = export_layer_string[:-1]

    if not export_sp_string:
        export_sp_string = str(ml.dis.nper)

    export_layer = [(abs(int(x) - 1)) for x in export_layer_string.split("_")]
    export_sp = [(abs(int(x) - 1)) for x in export_sp_string.split("_")]

    # Drawdown
    # Get the new head from timestep 1 of the last stress period in top layer
    head_new_data = extract_modflow_data(bf.HeadFile(path_to_head_file), '', ml.dis.nper, ml.dis.nlay)

    head_diff = calculate_data_diff(head_base_data, head_new_data, ml.dis.nper, ml.dis.nlay)

    # sr.export_array_contours("drawdown_contour.shp", head_diff)
    import matplotlib.pyplot as plt

    # Obtain contour levels
    contour_levels = contour_levels.split("/")
    contour_levels_float = [float(i) for i in contour_levels]
    ax = plt.subplot()
    feature_collection_list = list()
    for layer in range(ml.dis.nlay):
        if layer in export_layer:
            for sp in range(ml.dis.nper):
                features = []
                if sp in export_sp:
                    sr = flopy.utils.reference.SpatialReference(delr=ml.dis.delr, delc=ml.dis.delc, xll=float(xll),
                                                                yll=float(yll), rotation=float(rotation),
                                                                epsg=int(model_prj))
                    ctr = sr.contour_array(ax, head_diff[layer][sp], levels=contour_levels_float)
                    try:
                        sr.export_contours("drawdown_contour.shp", ctr, epsg=sr.epsg)

                        # read the shapefile
                        reader = shapefile.Reader("drawdown_contour.shp")
                        fields = reader.fields[1:]
                        field_names = [field[0] for field in fields]
                        for sr in reader.shapeRecords():
                            atr = dict(zip(field_names, sr.record))
                            if atr['level'] != 0:
                                geom = sr.shape.__geo_interface__
                                geom = transform_geom(geom, model_prj, geo_prj)
                                geom = line_to_polygon(geom)
                                features.append(Feature(geometry=geom, properties=atr))

                        feature_collection_list.append(FeatureCollection(features))
                        drawdown_feature_collection = FeatureCollection(features)
                        # write the GeoJSON file
                        with open("well_impact_" + str(layer) + "_" + str(sp) + ".json", 'w') as f:
                            dump(drawdown_feature_collection, f)
                    except Exception as e:
                        print(str(e))
                        pass

    with open("tethys_job_done.chk", 'w') as f:
        f.close()


if __name__ == "__main__":
    args = sys.argv
    args.pop(0)
    run(*args)

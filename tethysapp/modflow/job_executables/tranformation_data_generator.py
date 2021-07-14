#!/opt/tethys-python
import flopy
import sys
import pyproj
import json


def list_unique(item_list):
    return list(dict.fromkeys(item_list))


def rcl(ml, x, y, z, z_type):
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
    rc = ml.sr.get_rc(x=x, y=y)
    row = rc[0]
    col = rc[1]
    if z_type.lower() == 'depth':
        top_elev = float(ml.dis.gettop()[row][col])
        z = top_elev - z
    lay = flopy.modflow.mfdis.get_layer(ml.dis, row, col, z)

    return [row, col, lay]


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


def run(modflow_exe, data_path, modflow_nam, model_prj, xll, yll, rotation, geo_prj):
    """
    Run MODFLOW model
    Args:
        modflow_exe: path to MODFLOW executable file
        data_path: path to MODFLOW model files
        modflow_nam: MODFLOW name file with extension
        model_prj: projection of the model
        xll: x-coordinate of the lower left conner
        yll: y-coordinate of the lower left conner
        rotation: model grid rotation in counter clockwise direction
        budget_base: cell-to-cell file of the base model.
        geo_prj: output projection
        shape_type(Point or Polygon): Type of geometry shape in the output. Point is at center of the cell. Polygon is
         for the cell itself. Default is Point
        details: "All" is to print before and after data. If nothing is specified, it will only print the
         differences (before - after). Default is only to write out the differences.
    """  # noqa: E501

    """
        Run MODFLOW model

        Args:
            modflow_exe: path to MODFLOW executable file
            data_path: path to MODFLOW model files
            modflow_nam: MODFLOW name file with extension
            modflow_hds: MODFLOW hds file with extension
            modflow_wel: Name of the well file
            model_prj: model projection - prj string (ESPG or PROJ4).
            xll: x-coordinate at lower left corner for spacial reference.
            yll: y-coordinate at lower left corner for spacial reference.
            geo_prj: projection of pumps
        """  # noqa: E501

    exe_name = modflow_exe
    ws = data_path

    # Load Existing MODFLOW model
    ml = flopy.modflow.Modflow.load(modflow_nam, model_ws=ws, check=False, exe_name=exe_name)

    prj = flopy.utils.reference.getproj4(model_prj)

    # Spatial Reference
    sr = flopy.utils.reference.SpatialReference(delr=ml.dis.delr, delc=ml.dis.delc, xll=float(xll),
                                                yll=float(yll), rotation=float(rotation), proj4_str=prj,
                                                epsg=int(model_prj))
    ml.sr = sr
    transformation_lookup = {}
    if ml.has_package('DRN'):
        drn_cell2d_list = list()
        for sp in range(ml.nper):
            for eachdrain in range(len(ml.drn.stress_period_data[sp])):
                drn_cell2d_list.append(str(ml.drn.stress_period_data[sp][eachdrain][1]) + "_" +
                                       str(ml.drn.stress_period_data[sp][eachdrain][2]))
        drn_cell_2d_unique = list_unique(drn_cell2d_list)
        for cell in drn_cell_2d_unique:
            cell = cell.split("_")
            row = int(cell[0])
            if not transformation_lookup.get(row):
                transformation_lookup[row] = {}
        for cell in drn_cell_2d_unique:
            cell = cell.split("_")
            row = int(cell[0])
            col = int(cell[1])
            vertices = ml.sr.get_vertices(row, col)
            if not transformation_lookup[row].get(col):
                transformation_lookup[row][col] = [transform(vertices[3][0], vertices[3][1], model_prj, geo_prj),
                                                   transform(vertices[2][0], vertices[2][1], model_prj, geo_prj),
                                                   transform(vertices[1][0], vertices[1][1], model_prj, geo_prj),
                                                   transform(vertices[0][0], vertices[0][1], model_prj, geo_prj)]

    if ml.has_package('STR'):
        for reach in ml.sfr.reach_data:
            row = int(reach[2])
            if not transformation_lookup.get(row):
                transformation_lookup[row] = {}
        for reach in ml.sfr.reach_data:
            row = int(reach[2])
            col = int(reach[3])
            vertices = ml.sr.get_vertices(row, col)
            if not transformation_lookup[row].get(col):
                transformation_lookup[row][col] = [transform(vertices[3][0], vertices[3][1], model_prj, geo_prj),
                                                   transform(vertices[2][0], vertices[2][1], model_prj, geo_prj),
                                                   transform(vertices[1][0], vertices[1][1], model_prj, geo_prj),
                                                   transform(vertices[0][0], vertices[0][1], model_prj, geo_prj)]

    if ml.has_package('RIV'):
        riv_cell2d_list = list()
        for sp in range(ml.nper):
            for eachriv in range(len(ml.riv.stress_period_data[sp])):
                riv_cell2d_list.append(str(ml.riv.stress_period_data[sp][eachriv][1]) + "_" +
                                       str(ml.riv.stress_period_data[sp][eachriv][2]))
        riv_cell_2d_unique = list_unique(riv_cell2d_list)
        for cell in riv_cell_2d_unique:
            cell = cell.split("_")
            row = int(cell[0])
            if not transformation_lookup.get(row):
                transformation_lookup[row] = {}
        for cell in riv_cell_2d_unique:
            cell = cell.split("_")
            row = int(cell[0])
            col = int(cell[1])
            vertices = ml.sr.get_vertices(row, col)
            if not transformation_lookup[row].get(col):
                transformation_lookup[row][col] = [transform(vertices[3][0], vertices[3][1], model_prj, geo_prj),
                                                   transform(vertices[2][0], vertices[2][1], model_prj, geo_prj),
                                                   transform(vertices[1][0], vertices[1][1], model_prj, geo_prj),
                                                   transform(vertices[0][0], vertices[0][1], model_prj, geo_prj)]

    if transformation_lookup:
        json_data = json.dumps(transformation_lookup)
        f = open("transformation_lookup.json", "w")
        f.write(json_data)
        f.close


if __name__ == "__main__":
    args = sys.argv
    args.pop(0)
    run(*args)

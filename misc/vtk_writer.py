from vtk import vtkXMLUnstructuredGridWriter, vtkUnstructuredGrid, vtkPoints, vtkDoubleArray


def write_vtu(input, x, y, z, disX, disY, disZ):
    # Write the vtk file
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName("out_" + input)

    # Generate the grid
    grid = vtkUnstructuredGrid()

    # Add points and fields
    points = vtkPoints()
    points.SetNumberOfPoints(len(x))
    points.SetDataTypeToDouble()

    # Add the points
    for i in range(len(x)):
        points.InsertPoint(i, x[i], y[i], z[i])
    # Add the points to the grid
    grid.SetPoints(points)

    # Displacement field
    disArray = vtkDoubleArray()
    disArray.SetName("Displacement")
    disArray.SetNumberOfComponents(3)
    disArray.SetNumberOfTuples(len(x))

    # Write the displacement
    for i in range(len(x)):
        disArray.SetTuple3(i, disX[i], disY[i], disZ[i])

    # Add the displacement field to the grid
    dataOut = grid.GetPointData()
    dataOut.AddArray(disArray)
    writer.SetInput(grid)

    # Add compression
    writer.GetCompressor().SetCompressionLevel(0)
    writer.SetDataModeToAscii()

    # Write the grid
    writer.Write()

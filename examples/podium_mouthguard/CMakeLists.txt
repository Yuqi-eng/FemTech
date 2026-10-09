SET(podium_mouthguard_src podium_mouthguard.cpp)

ADD_EXECUTABLE(podium_mouthguard ${podium_mouthguard_src})
ADD_DEPENDENCIES(podium_mouthguard JsonCpp)

if(ENABLE_MPI)
  LINK_DIRECTORIES(${CMAKE_BINARY_DIR}/lib ${CMAKE_BINARY_DIR}/third-party/parmetis-4.0.3/libparmetis)
  TARGET_LINK_LIBRARIES(podium_mouthguard FemTech parmetis  ${lapackblas_libraries} jsoncpp)
else()
  LINK_DIRECTORIES(${CMAKE_BINARY_DIR}/lib)
  TARGET_LINK_LIBRARIES(podium_mouthguard FemTech)
endif(ENABLE_MPI)

file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/analysis)
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/runtime_files)
file(INSTALL runtime_files/coarse_brain.inp DESTINATION runtime_files/.)
file(INSTALL runtime_files/materials.dat DESTINATION runtime_files/.)
file(INSTALL runtime_files/input.json DESTINATION runtime_files/.)
file(INSTALL analysis/gnuplot.script DESTINATION analysis/.)
file(INSTALL analysis/gnuplotEnergy.script DESTINATION analysis/.)
file(INSTALL README.md DESTINATION .)
file(INSTALL analysis/simulationMovie.py DESTINATION analysis/.)
file(INSTALL analysis/mps95Movie.py DESTINATION analysis/.)
file(INSTALL analysis/addGraph.py DESTINATION analysis/.)
file(INSTALL runtime_files/run_mg.sh DESTINATION runtime_files/.)
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/results)
file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/results/vtu)

# Define debugger options when working with windows & visual studio generator
# We set them here but could be passed as options if required
# We use a template for the same, replacing the options we need
if(WIN32 AND MSVC)
	set( DEBUG_COMMAND "C:\\Program Files\\Microsoft MPI\\Bin\\mpiexec.exe" )
	set( DEBUG_COMMAND_ARGUMENTS "-n 2 \"$(TargetPath)\" brain.inp" )
	configure_file( template.vcxproj.user.in ${CMAKE_BINARY_DIR}/examples/podium_mouthguard/podium_mouthguard.vcxproj.user @ONLY )
endif()

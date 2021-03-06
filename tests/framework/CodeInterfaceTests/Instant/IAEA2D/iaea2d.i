[Mesh]
 type = SplitSidesetMesh
 file = iaea2d.e
 uniform_refine = 0
 second_order = true
[]

[MeshModifiers]
  [./normals]
    type = SplitSideSetsAndAddNormals
  [../]
[]

[Debug]
 show_actions = true
# show_material_props = true
[]

[TransportSystems]
 particle = neutron
 equation_type = eigenvalue

 G = 2

 VacuumBoundary = '2'
 ReflectingBoundary = '1'
 [./diff]
    scheme = CFEM-Diffusion
    family = LAGRANGE
    order = FIRST
 [../]
[]

[Materials]
  [./fuel1]
    type = ConstantNeutronicsMaterial
    block = 2
    fromFile = true
    fileName = xs.xml
    material_id = 1
  [../]

  [./fuel2]
    type = ConstantNeutronicsMaterial
    block = 3
    fromFile = true
    fileName = xs.xml
    material_id = 2
  [../]

  [./fuel1withrod]
    type = ConstantNeutronicsMaterial
    block = 1
    fromFile = true
    fileName = xs.xml
    material_id = 3
  [../]

  [./reflector]
    type = ConstantNeutronicsMaterial
    block = 4
    fromFile = true
    fileName = xs.xml
    material_id = 4
  [../]
[]

[Executioner]
  type = NonlinearEigen

  #Preconditioned JFNK (default)
  solve_type = 'PJFNK'
  petsc_options_iname = '-pc_type -pc_hypre_type -ksp_gmres_restart '
  petsc_options_value = 'hypre boomeramg 300'

  free_power_iterations = 4
  source_abs_tol = 1e-12
  output_after_power_iterations = false
[]

[Outputs]
  exodus = true
[]

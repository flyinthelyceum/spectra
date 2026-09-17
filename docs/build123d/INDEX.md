# Vendored build123d reference

Cut from tag **v0.11.1**, the same version pinned in `requirements.txt`. See
`SOURCE_COMMIT.txt` for the exact commit. Bump both together or neither.

This exists so CAD in this repo is authored against the real API rather than
against a model's memory of it. Read the file that covers what you are about to
write, before you write it.

## Where to look

| Doing this | Read |
| --- | --- |
| Getting oriented at all | `introduction.rst`, `key_concepts.rst` |
| Choosing builder vs algebra mode | `key_concepts_builder.rst`, `key_concepts_algebra.rst` |
| Looking up a call you half remember | `cheat_sheet.rst` |
| Building a solid | `build_part.rst`, `objects.rst`, `operations.rst` |
| Building a 2D profile to extrude | `build_sketch.rst` |
| Paths, profiles, sweeps | `build_line.rst` |
| Picking faces, edges, vertices | `selectors.rst`, `topology_selection.rst` |
| Placing things without guessing coordinates | `moving_objects.rst`, `location_arithmetic.rst`, `center.rst` |
| Fitting parts together, mating | `joints.rst`, `tutorial_joints.rst` |
| Multi-part assemblies | `assemblies.rst` |
| STEP out, DXF out, mesh out | `import_export.rst` |
| Full signatures for anything | `direct_api_reference.rst`, `builder_api_reference.rst` |
| Drawings for the shop | `tech_drawing_tutorial.rst` |
| It runs but the geometry is wrong | `debugging_logging.rst`, `tips.rst` |
| Worked examples to copy the shape of | `introductory_examples.rst`, `examples_1.rst`, `tttt.rst` |

## House rules on top of the library

- Parameters live in one block per part. No literals buried in geometry.
- STEP is the interchange format out to Fusion, DXF is the format out to the
  laser. Both come from the same model.
- Joinery, kerf, and fastener spacing derive from material thickness. Changing
  18mm to 15mm regenerates every joint rather than breaking them.
- Fitted trays are generated from a tool list, not drawn one pocket at a time.

from analytics import Project

file = "data/Example_Project_POS.zip"

# load project
project = Project.from_zipped_xmi(file)

# print all annotator names
for annotator in project.annotators:
    print(annotator)

# create a view 
pos_type = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"

view = project.select(
        annotation=project.feature_path(pos_type, "coarseValue"),
        annotators=project.annotators, 
        source_files=project.source_file_names
)

print('# pos annotations in view:', len(view.annotations))

print('IAA Krippendorff: ', view.iaa())

for cf in view.confusion_matrices():
    print(cf)

from voc_eval_py3 import voc_eval

#/Users/liqinghua/projects/medical-rib/data/voc2007/ImageSets/test.txt
rec,prec,ap = voc_eval('/Users/liqinghua/projects/medical-rib/models/darknet/results/{}.txt', '/Users/liqinghua/voc2007.xoy/Annotations/{}.xml',
                       '/Users/liqinghua/voc2007.xoy/ImageSets/2007_test.txt', 'hurt', '.')

print('rec',rec)
print('prec',prec)
print('ap',ap)
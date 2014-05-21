from cohort import *
from validated_cohort import *
from fixed_cohort import *
from wiki_cohort import *

# ignore flake8 because of F403 violation
# flake8: noqa

from inspect import getmembers, isclass
from sys import modules
cohort_classes = {
    c[0]: c[1]
    for c in getmembers(modules[__name__], isclass)
    if issubclass(c[1], Cohort)
}

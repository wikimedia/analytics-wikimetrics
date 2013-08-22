from dummy import *
from metric import *
from namespace_edits import *
from revert_rate import *
from bytes_added import *
from pages_created import *

# ignore flake8 because of F403 violation
# flake8: noqa

from inspect import getmembers, isclass
from sys import modules
metric_classes = {m[0]: m[1] for m in getmembers(modules[__name__], isclass)}


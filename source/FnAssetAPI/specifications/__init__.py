from .SpecificationBase import SpecificationBase
from .SpecificationFactory import SpecificationFactory
from .Specification import Specification

# Import derived classes
from ._command import *
from ._entity import *
from ._locale import *
from ._parameter import *
from ._relationship import *

# Foundry Core Specifications
from ._foundry import *

##
# @namespace python.specifications
# Spefications are vital to defining the 'type' of Entities, as well as better
# informing a Manager as to specifics of a Host's actions. They are broken down
# into several sub-classes:
#
#  \li EntitySpecifications - for typing an Entity.
#  \li LocaleSpecifications - for defining which area of a Host is performing
#  an action. 
#  \li ParameterSpecifications - for defining stronger Parameter types to
#  Manager UI Delegates.
#  \li RelationshipSpecifications - for defining the relationships between
#  Entities.
#  \li CommandSpecificaionts - for defining custom commands that may be
#  supported by a Host or Manager.
#
#  Specifications are simply represented by a string - the 'schema' and a
#  series of arbitrary key-value pairs. String keys, plain-old-data values.
#
#  \see python.specifications._entity.EntitySpecification
#  \see python.specifications._locale.LocaleSpecification
#  \see python.specifications._parameter.ParameterSpecification
#  \see python.specifications._relationship.RelationshipSpecification
#  \see python.specifications._command.CommandSpecification
#




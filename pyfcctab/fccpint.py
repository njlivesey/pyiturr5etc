"""A simple module for establishing a common unit registry"""

import pint

ureg = pint.UnitRegistry()
pint.set_application_registry(ureg)
ureg.setup_matplotlib()

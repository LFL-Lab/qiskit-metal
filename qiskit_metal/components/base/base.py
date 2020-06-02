# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2019.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
This is the main module that defines what a component is in Qiskit Metal.
See the docstring of QComponent
    >> ?QComponent

@author: Zlatko Minev, Thomas McConekey, ... (IBM)
@date: 2019
"""
import pandas as pd
import logging
import pprint
import inspect
import os
import numpy as np
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Iterable, List, Optional, TypeVar, Union, Dict as Dict_
from ... import draw
from ... import is_design, logger
from ...draw import BaseGeometry
from ...toolbox_python.attr_dict import Dict
from ._parsed_dynamic_attrs import ParsedDynamicAttributes_Component

from ... import is_design, logger
from ...draw import BaseGeometry
from ...toolbox_python.attr_dict import Dict
from ._parsed_dynamic_attrs import ParsedDynamicAttributes_Component

__all__ = ['QComponent']

if TYPE_CHECKING:
    # For linting typechecking, import modules that can't be loaded here under normal conditions.
    # For example, I can't import QDesign, because it requires QComponent first. We have the
    # chicken and egg issue.
    from ...designs import QDesign
    # from ...elements import ElementTypes
    import matplotlib


class QComponent():
    """
    `QComponent` is the base class for all Metal components and is the
    central construct from which all components in Metal are derived.

    The class defines the user interface for working with components.

    For front-end user:
        * Manipulates the dictionary of options (stored as string-string key-value
         pairs) to change the geometry and properties of the component.
        * The options of the class are stored in an options dicitonary. These
          include the geometric sizes, such as width='10um' or height='5mm', etc.
        * The `make` function parses these strings and implements the logic required
          to transform the dictionary of options (stored as strings) into shapes
          with associated properties.

    For creator user:
        * The creator user implements the `make` function (see above)
        * The class define the internal representation of a componetns
        * The class provides the interfaces for the component (creator user)
    """

    ''' QComponent.gather_all_children_options collects the options
        starting with the basecomponent, and stepping through the children.
        Each child adds it's options to the base options.  If the
        key is the same, the option of the youngest child is used.
    '''

    # Dummy private attribute used to check if an instanciated object is
    # indeed a QComponent class. The problem is that the `isinstance`
    # built-in method fails when this module is reloaded.
    # Used by `is_component` to check.
    __i_am_component__ = True

    def __init__(self, design: 'QDesign', name: str, options: Dict = None,
                 make=True, component_template: Dict = None):
        """Create a new Metal component and adds it's default_options to the design.

        Arguments:
            name {str} -- Name of the component.
            design {QDesign} -- The parent design.

        Keyword Arguments:
            options {[type]} -- User options that will override the defaults. (default: {None})
            make {bool} -- Should the make function be called at the end of the init.
                    Options be used in the make funciton to create the geometry. (default: {True})
            component_template {[type]} -- User can overwrite the template options for the component
                                           that will be stored in the design, in design.template, and used
                                           every time a new component is instantiated.
        """

        assert is_design(design), "Error you did not pass in a valid \
        Metal Design object as a parent of this component."

        # TODO: handle, if the component name already exits and we want to overwrite,
        # then we need to delete its old elements at the end of the init before the make

        self._name = name
        self._design = design  # pointer to parent

        self._id = 0

        self._class_name = self._get_unique_class_name()

        self.options = self.get_template_options(
            design=design, component_template=component_template)
        if options:
            self.options.update(options)

        # In case someone wants to store extra information or
        # analysis results
        self.metadata = Dict()

        # Status: usedd to handle building of a compoentn and checking if it succeedded or failed.
        self.status = 'not built'

        # Names of connectors associated with this components.
        # Used to rename, etc.  CHANGE TO PINS?
        self._connector_names = set()

        # has the component already been made
        self._made = False

        # Parser for options
        self.p = ParsedDynamicAttributes_Component(self)
        
        #Generate empty dict for pins
        self.pins = dict()

        # Add the component to the parent design
        self._add_to_design()

        # Make the component geometry
        if make:
            self.do_make()

    @classmethod
    def _gather_all_children_options(cls):
        '''
        From the base class of QComponent, traverse the child classes
        to gather the .default options for each child class.
        Note: if keys are the same for child and grandchild, grandchild will overwrite child
        Init method.
        '''

        options_from_children = {}
        parents = inspect.getmro(cls)

        # Base.py is not expected to have default_options dict to add to design class.
        for child in parents[len(parents)-2::-1]:
            # There is a developer agreement so the defaults will be in dict named default_options.
            if hasattr(child, 'default_options'):
                options_from_children = {
                    **options_from_children, **child.default_options}

        return options_from_children

    @classmethod
    def _get_unique_class_name(cls) -> str:
        """Returns unique class name based on the module:

        Returns:
            str -- Example: 'qiskit_metal.components.qubits.transmon_pocket.TransmonPocket'
        """
        return f'{cls.__module__}.{cls.__name__}'

    @classmethod
    def _register_class_with_design(cls,
                                    design: 'QDesign',
                                    template_key: str,
                                    component_template: Dict):
        """Init funciton to register a component class with the design when first instantiated.
            Registers the design template options.
        """
        # do not overwrite
        if template_key not in design.template_options:
            if not component_template:
                component_template = cls._gather_all_children_options()
            design.template_options[template_key] = deepcopy(
                component_template)

    @property
    def name(self) -> str:
        '''Name of the component'''
        return self._name

    @name.setter
    def name(self, new_name: str):
        '''Rename the component. Change the design dictioanries as well.
        handle components. Delete and remake.'''
        return self.design.rename_component(self.name, new_name)

    @property
    def design(self) -> 'QDesign':
        '''Return a reference to the parent design object'''
        return self._design

    @property
    def class_name(self) -> str:
        '''Return the full name of the class: the full module name with the class name.
        e.g., qiskit_metal.components.qubits.QubitClass
        '''
        return self._class_name

    @property
    def logger(self) -> logging.Logger:
        return self._design.logger

    @property
    def connectors(self) -> set:
        '''The names of the connectors'''
        return self._connector_names

    @property
    def id(self) -> int:
        '''The unique id of component within a design.'''
        return self._id

    def _add_to_design(self):
        ''' Add self to design objects dictionary.
            Method will obtain an unique id for the component within a design, THEN add itself to design.
        '''
        self._id = self.design._get_new_qcomponent_id()
        self.design.components[self.id] = self

    @classmethod
    def get_template_options(cls,
                             design: 'QDesign',
                             component_template: Dict = None,
                             logger_: logging.Logger = None,
                             template_key: str = None) -> Dict:
        """
        Creates template options for the Metal Componnet class required for the class
        to function, based on teh design template; i.e., be created, made, and rendered. Provides the blank option
        structure required.

        The options can be extended by plugins, such as renderers.

        Arguments:
            design {QDesign} -- Design class. Should be the class, not the instance.

        Keyword Arguments:
            logger_ {logging.Logger} -- A logger for errors. (default: {None})
            component_template {Dict} -- Tempalte options to overwrite the class ones.
            template_key {str} --  The template key identifier. If None, then uses
                                    cls._get_unique_class_name() (default: {None})

        Returns:
            Dict -- dictionary of default options based on design template.
        """
        # get key for tepmlates
        if template_key is None:
            template_key = cls._get_unique_class_name()

        if template_key not in design.template_options:
            cls._register_class_with_design(
                design, template_key, component_template)

        if template_key not in design.template_options:
            logger_ = logger_ or design.logger
            if logger_:
                logger_.error(f'ERROR in the creating component {cls.__name__}!\n'
                              f'The default options for the component class {cls.__name__} are missing')

        # Specific object template options
        options = deepcopy(Dict(design.template_options[template_key]))

        return options

    def make(self):
        '''
        Overwrite in inheritnace to define user logic to convert options dictionary into
        elements.
        Here, one creates the shapely objects, assigns them as elements.
        This method should be overwritten by the childs make function.

        This function only contains the logic, the actual call to make the element is in
        do_make() and remake()
        '''
        raise NotImplementedError()

    # TODO: Maybe call this function build
    # TODO: Capture error here and save to log as the latest error
    def do_make(self):
        """Actually make or remake the component"""
        self.status = 'failed'
        if self._made:  # already made, just remaking
            # TODO: this is probably very inefficient, design more efficient way
            self.design.elements.delete_component(self.id)
            self.make()
        else:  # first time making
            self.make()
            self._made = True  # what if make throws an error part way?
        self.status = 'good'

    rebuild = do_make

    def delete(self):
        """
        Delete the element and remove from the design.
        Removes also all of its connectors.
        """
        raise NotImplementedError()

    def parse_value(self, value: Union[Any, List, Dict, Iterable]):
        # Maybe still should be fine as any values will be in component options still?
        # Though the data table approach and rendering directly via shapely could lead to problem
        # with variable use
        """
        Parse a string, mappable (dict, Dict), iterrable (list, tuple) to account for
        units conversion, some basic arithmetic, and design variables.
        This is the main parsing function of Qiskit Metal.

        Handled Inputs:

            Strings:
                Strings of numbers, numbers with units; e.g., '1', '1nm', '1 um'
                    Converts to int or float.
                    Some basic arithmatic is possible, see below.
                Strings of variables 'variable1'.
                    Variable interpertation will use string method
                    isidentifier `'variable1'.isidentifier()
                Strings of

            Dictionaries:
                Returns ordered `Dict` with same key-value mappings, where the values have
                been subjected to parse_value.

            Itterables(list, tuple, ...):
                Returns same kind and calls itself `parse_value` on each elemnt.

            Numbers:
                Returns the number as is. Int to int, etc.


        Arithemetic:
            Some basic arithemetic can be handled as well, such as `'-2 * 1e5 nm'`
            will yield float(-0.2) when the default units are set to `mm`.

        Default units:
            User units can be set in the design. The design will set config.DEFAULT.units

        Examples:
            See the docstring for this module.
                >> ?qiskit_metal.toolbox_metal.parsing

        Arguments:
            value {[str]} -- string to parse
            variable_dict {[dict]} -- dict pointer of variables

        Return:
            Parse value: str, float, list, tuple, or ast eval
        """
        return self.design.parse_value(value)

    def parse_options(self, options: Dict = None) -> Dict:
        """
        Parse the options, converting string into interpreted values.
        Parses units, variables, strings, lists, and dicitonaries.
        Explained by example below.

        Options Arguments:
            options (dict) : default is None. If left None,
                             then self.options is used

        Calls `self.design.parse_options`.

        See `self.parse_value` for more infomation.
        """

        return self.design.parse_options(options if options else self.options)


####################################################################################
### Functions for handling of pins
# 
# TODO: Decide how to handle this.
#   Should this be a class?
#   Should we keep function here or just move into design?
# MAKE it so it has reference to who made it
    #This doesn't really need to be here, could shift to toolbox
    def make_pin(self, points: list, parent_name: str, flip=False, chip='main'):
        """
        Works in user units.

        Arguments:
            points {[list of coordinates]} -- Two points that define the connector

        Keyword Arguments:
            flip {bool} -- Flip the normal or not  (default: {False})
            chip {str} -- Name of the chip the connector sits on (default: {'main'})

        Returns:
            [type] -- [description]
        """
        assert len(points) == 2

        # Get the direction vector, the unit direction vec, and the normal vector
        vec_dist, vec_dist_unit, vec_normal = draw.Vector.two_points_described(
            points)

        if flip:
            vec_normal = -vec_normal

        return Dict(
            points=points,
            middle=np.sum(points, axis=0)/2.,
            normal=vec_normal,
            tangent=vec_dist_unit,
            width=np.linalg.norm(vec_dist),
            chip=chip,
            parent_name=parent_name,
            net_id = 0
        )

    def get_pin(self, name: str):
        """Interface for components to get connector data

        Args:
            name (str): Name of the desired connector.

        Returns:
            (dict): Returns the data of the connector, see design_base.make_connector() for
                what those values are.
        """

        # For after switching to pandas, something like this?
        # return self.connectors.get(name).to_dict()

        return self.pins[name]

    def add_pin(self,
                      name: str,
                      points: list,
                      parent: Union[str, 'QComponent'],
                      flip: bool = False,
                      chip: str = 'main'):
        """Add named connector to the design by creating a connector dicitoanry.

        Arguments:
            name {str} -- Name of connector
            points {list} -- List of two (x,y) points that define the connector
            parent {Union[str,} -- component or string or None. Will be converted to a
                                 string, which will the name of the component.

        Keyword Arguments:
            flip {bool} -- [description] (default: {False})
            chip {str} --  Optionally add options (default: {'main'})
        """
        ##THIS SEEMS REDUNDANT IF THE function is part of the component class?
        # if is_component(parent):
        #     parent = parent.id
        # elif parent is None:
        #     parent = 'none'
        # name = str(parent)+'_'+name

        # assert isinstance(parent, str) # could enfornce
        self.pins[name] = self.make_pin(
            points, parent, flip=flip, chip=chip)

        # TODO: Add net?

#BEING MOVED TO DIFFERENT CLASS?
    # def add_connector(self, id, points: list, flip=False, chip=None):
    #     """Register a connector with the design.

    #     Arguments:
    #         two_points {list} -- List of the two point coordinates that deifne the start
    #                              and end of the connector
    #         ops {None / dict} -- Options

    #     Keyword Arguments:
    #         name {string or None} -- By default is just the object name  (default: {None})
    #         chip {string or None} -- chip name or defaults to DEFAULT.chip
    #     """
    #     if id is None:
    #         id = self.id

    #     self._connector_names.add(name)

    #     self.design.add_connector(name=name,
    #                               points=points,
    #                               parent=self,
    #                               chip=chip,
    #                               flip=flip)

    def add_dependency(self, parent: str, child: str):
        """Add a dependency between one component and another.
        Calls parent design.

        Arguments:
            parent {str} -- The component on which the child depends
            child {str} -- The child cannot live without the parent.
        """
        self.design.add_dependency(parent, child)

##########################################
# Elements
    def add_elements(self,
                     kind: str,
                     elements: dict,
                     subtract: bool = False,
                     helper: bool = False,
                     layer: Union[int, str] = 1,  # chip will be here
                     chip: str = 'main',
                     **kwargs
                     ):
                    #  subtract: Optional[bool] = False,
                    #  layer: Optional[Union[int, str]] = 0,
                    #  type: Optional[ElementTypes] = ElementTypes.positive,
                    #  chip: Optional[str] = 'main',
                    #  **kwargs):
        r"""Add elements.

        Takes any additional options in options.

        Assumptions:
            * Assumes all elements in the elements are homogeneous in kind;
             i.e., all lines or polys etc.


        Arguments:
            kind {str} -- The kind of elements, such as 'path', 'poly', etc.
                          All elements in the dicitonary should have the same kind
            elements {Dict[BaseGeometry]} -- Key-value pairs

        Keyword Arguments:
            subtract {bool} -- Subtract from the layer (default: {False})
            helper {bool} -- Is this a helper object. If true, subtract must be false
            layer {int, str} -- The layer to which the set of elements will belong
                        (default: {0})
            chip {str} -- Chip name (dafult: 'main')
        """
        #assert (subtract and helper) == False, "The object can't be a subtracted helper. Please"\
        #    " choose it to either be a helper or a a subtracted layer, but not both. Thank you."

        self.design.elements.add_elements(kind, self.id, elements, subtract=subtract,
                                          helper=helper, layer=layer, chip=chip, **kwargs)

    def __repr__(self, *args):
        b = '\033[94m\033[1m'
        e = '\033[0m'
        return f"""Component {b}{self.name}{e}:
 class  : {b}{self.__class__.__name__:<22s}{e}     at {hex(id(self))}
 module : {b}{self.__class__.__module__}{e}
 options: \n{pprint.pformat(self.options)}"""

    ############################################################################
    # Geometry handling of created elements

    @property
    def elements_types(self) -> List[str]:
        """Get a list of the names of the element tables.
        Returns:
            List[str] -- Name of element table or type; e.g., 'poly' and 'path'
        """
        return self.design.elements.get_element_types()

    def elements_dict(self, element_type: str) -> Dict_[str, BaseGeometry]:
        """
        Returns a dict of element geoemetry (shapely geometry) of the component
        as a python dict, where the dict keys are the names of the elements
        and the corresponding values are the shapely geometries.

        Arguments:
            element_type {str} -- Name of element table or type; e.g., 'poly' and 'path'

        Returns:
            List[BaseGeometry] or None -- Returns None if an error in the name of the element type (ie. table)
        """
        if self.design.elements.check_element_type(element_type):
            return self.design.elements.get_component_geometry_dict(self.id, element_type)

    def elements_list(self, element_type: str = 'all') -> List[BaseGeometry]:
        """
        Returns a list of element geoemetry (shapely geometry) of the component
        as a python list of shapely geometries.

        Arguments:
            element_type {str} -- Name of element table or type; e.g., 'poly' and 'path'.
                                 Can also specify all

        Returns:
            List[BaseGeometry] or None -- Returns None if an error in the name of the element type (ie. table)
        """
        if element_type == 'all' or self.design.elements.check_element_type(element_type):
            return self.design.elements.get_component_geometry_list(self.id, element_type)

    def elements_table(self,  element_type: str) -> pd.DataFrame:
        """
        Returns the entire element table for the component.

        Arguments:
            element_type {str} -- Name of element table or type; e.g., 'poly' and 'path'

        Returns:
            pd.DataFrame or None -- Element table for the component. Returns None if an error in the name of the element type (ie. table)
        """
        if self.design.elements.check_element_type(element_type):
            return self.design.elements.get_component(self.id, element_type)

    def geometry_bounds(self):
        """
        Return the bounds of the geometry.
        """
        bounds = self.design.elements.get_component_bounds(self.id)
        return bounds

    def elements_plot(self, ax: 'matplotlib.axes.Axes' = None, plot_kw: dict = None) -> List:
        """    Draw all the elements of the component (polys and path etc.)

        Keyword Arguments:
            ax {[type]} --  Matplotlib axis to draw on (default: {None} -- gets the current axis)
            plot_kw {dict} -- [description] (default: {None})

        Returns:
            List -- The list of elements draw

        Example use:
            Suppose you had a component called q1:

                fig, ax = draw.mpl.figure_spawn()
                q1.elements_plot(ax)
        """
        elements = self.elements_list()
        plot_kw = {}
        draw.mpl.render(elements, ax=ax, kw=plot_kw)
        return elements

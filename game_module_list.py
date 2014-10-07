# Game Modules List
# -----------------
# This script looks to all blender files in the current directory
# and list all the python module used by the controllers.
#
# Dalai Felinto
# www.dalaifelinto.com
#
# Rio de Janeiro, Brazil
# February 10th, 2012

# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "List Game Modules",
    "author": "Dalai Felinto",
    "version": (1, 0),
    "blender": (2, 6, 2),
    "location": "Logic Editor > View > List Module Controllers",
    "description": "List all Python Module controllers in this file and its folder recursively",
    "warning": "waiting for bug fix: [#30155] segfault with bpy.app.handlers",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Game Engine"}


import bpy
import os
import collections
from xml.etree.ElementTree import Element, SubElement, Comment, tostring

from bpy.app.handlers import persistent

class NestedDict(collections.OrderedDict):
    def __init__(self, *args, **kw):
        super(NestedDict, self).__init__(*args, **kw)
        self.itemlist = super(NestedDict,self).keys()

    def __getitem__( self, name ):
        try:
            return super(NestedDict,self).__getitem__(name)

        except KeyError:
            # when key is not found automatically creates
            self.__setitem__(name, NestedDict())
            return super(NestedDict,self).__getitem__(name)

    def add_user(self, *args):
        """recursive function to add nested elements"""

        if len(args) > 1:
            # it auto-adds elements if key doesn't exist
            self.__getitem__(args[0]).add_user(*args[1:])

        else:
            self.__setitem__(args[0], None)

    def __setitem__(self, key, value):
        """add a new item in the right order"""
        keys = list(self.keys())

        sorted_keys = keys[:]
        sorted_keys.append(key)
        sorted_keys.sort()
        
        index = sorted_keys.index(key)
        super(NestedDict, self).__setitem__(key, value)

        # they all could run the else formula
        # but the if/elif help some performance
        # in big dictionaries

        # add to the end
        if index == len(keys): pass

        # add to the begin
        elif index == 0:
            self.move_to_end(key, last=False)

        # add to the middle
        else:
            for _key in sorted_keys[index+1:]:
                self.move_to_end(_key)

class Modules:
    def __init__(self, basedir, filepath, xml):
        """"""
        self.basedir = basedir
        self.filepath = filepath
        self.modules = NestedDict()
        self.xml = xml

    def add_user(self, module, function, filename, object, controller):
        """"""
        print("add_user(self, %s, %s, %s, %s, %s)" % (module, function, filename, object, controller))
        self.modules[module].add_user(function, filename, object, controller)

    def finished(self):
        """runs after everything else"""
        del bpy.files

        bpy.app.handlers.load_post.remove(inspect_file)
        bpy.app.handlers.load_post.append(print_report)

        if self.filepath == bpy.context.blend_data.filepath:
            self.report()
        else:
            bpy.ops.wm.open_mainfile(filepath=self.filepath)

    def report(self):
        """clean up everything and report"""
        bpy.app.handlers.load_post.remove(print_report)

        if self.xml == True:
            xmlreport = Element("report")
            xmlreport.set('version', "1.0")
            comment = Comment("Blender files report, bge module list")
            xmlreport.append(comment)

            for key,value in self.modules.items():
                module = SubElement(xmlreport, "module")
                module.attrib = {'name':key}

               # function
                for key,value in value.items():
                    function = SubElement(module, "function")
                    function.attrib = {'name':key}

                    # file
                    for key,value in value.items():
                        file = SubElement(function, "file")
                        file.attrib = {'name':key}
    
                        # object
                        for key,value in value.items():
                            object = SubElement(file, "object")
                            object.attrib = {'name':key}

                            # controller
                            for key,value in value.items():
                                controller = SubElement(object, "controller")
                                controller.text = key
    
            text = bpy.data.texts.new(name="report.xml")
            message = tostring(xmlreport, encoding='utf-8', method='xml').decode()
            text.write(message)

        else:
            # report composing
            text = bpy.data.texts.new(name="Report.txt")
            message = "Blender Game Engine . Module Python Listing:"
            text.write("%s\n%s\n" % (message, "^"*len(message)))
    
            # module
            for key,value in self.modules.items():
                message = "module: {0}".format(key)
                text.write("\n{0}\n{1}\n{0}\n".format("="*len(message), message))
                # function
                for key,value in value.items():
                    message = "function: {0}".format(key)
                    text.write("\n{0}\n{1}\n{0}\n".format("="*len(message), message))
                    # file
                    for key,value in value.items():
                        message = "file: {0}".format(key)
                        text.write("\n{0}\n{1}\n{0}\n".format("="*len(message), message))
                        # object
                        for key,value in value.items():
                            text.write("object: {0}\n".format(key))
                            # controller
                            for key,value in value.items():
                                text.write("controller: {0}\n".format(key))

        # we don't need to print it, but right now there is a bug right after we are done
        print(text.as_string())
    
class LOGIC_OT_list_controllers(bpy.types.Operator):
    """List all module controllers"""
    bl_idname = "logic.list_modules"
    bl_label = "List Game Modules"
    bl_description = "List all Python Module controllers in this file and its folder recursively"
    bl_options = {'REGISTER', 'UNDO'}

    autosave = bpy.props.BoolProperty(  name = "Autosave",
                                        description = "Automatically save the current file before " \
                                        " opening the linked library",
                                        default = True)


    xml = bpy.props.BoolProperty(  name = "XML",
                                        description = "Export the file as XML",
                                        default = True)

    def execute(self, context):
        # initialize bpy.modules
        curdir = bpy.path.abspath('//')
        filepath = bpy.context.blend_data.filepath
        bpy.modules = Modules(curdir, filepath, self.properties.xml)
    
        # get all files available
        files = list()
        basedir = bpy.path.abspath('//')
        get_files(files, basedir)
    
        # store to use later
        bpy.files = files
    
        # make sure this runs for the new files    
        bpy.app.handlers.load_post.append(inspect_file)

        # we will open other files, may as well save the current
        if self.properties.autosave == True:
            bpy.ops.wm.save_mainfile()

        # start the inspection with the current file
        inspect_file(context)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager     
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        layout.label(text="Do you want to save the current file?")
        layout.prop(self, "autosave")

        layout.label(text="Do you want to use the XML format?")
        layout.prop(self, "xml")

@persistent
def print_report(context):
    """"""
    bpy.modules.report()

@persistent
def inspect_file(context):
    """runs for every file"""
    curdir = bpy.path.abspath('//')
    filepath = bpy.context.blend_data.filepath

    # relative to basedir
    filename = bpy.path.relpath(filepath, bpy.modules.basedir)
    basedir,file = os.path.split(filename)

    # convert '//folder/subfolder' to 'folder.subfolder'
    pythondir = '.'.join(basedir[3:].split(os.path.sep)[2:])

    # when in the top level folder shouldn't show .
    if pythondir == ".": pythondir = ""
    
    for object in bpy.data.objects:
        for controller in object.game.controllers:
            if controller.type == 'PYTHON' and controller.mode == 'MODULE':

             module,function = "{0}{1}".format(pythondir, controller.module).rsplit('.', 1)
             module = "{0}.py".format(module)
             bpy.modules.add_user(module, function, filename, object.name, controller.name)

    # go to next file
    load_next_file()

def load_next_file():
    """"""
    if len(bpy.files):
        filepath = bpy.files.pop()
     
    else:
        bpy.modules.finished()
        return

    if filepath == bpy.modules.filepath:
        load_next_file()
    else:
        bpy.ops.wm.open_mainfile(filepath=filepath)

def get_files(files, directory):
    """creates a list with all .blend files from this folder on"""

    for file in os.listdir(directory):
        if file == '.svn':
            continue

        filepath = os.path.abspath(os.path.join(directory, file))

        if os.path.isdir(filepath):
            get_files(files, filepath)

        elif file.endswith('.blend'):
            files.append(filepath)


def list_controllers_button(self, context):
    self.layout.operator(
        LOGIC_OT_list_controllers.bl_idname,
        text="List Controllers",
        icon="GAME")

def register():
    bpy.utils.register_class(LOGIC_OT_list_controllers)
    bpy.types.LOGIC_MT_view.append(list_controllers_button)


def unregister():
    bpy.utils.unregister_class(LOGIC_OT_list_controllers)
    bpy.types.LOGIC_MT_view.remove(list_controllers_button)


if __name__ == '__main__':
    register()

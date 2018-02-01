# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 10:55:49 2018

@author: peter
"""
import sys
import pycparser
import pycparser.c_generator
from pycparser.c_ast import *
def main(argv):
    if len(argv) < 2:
        print("Error: C source code filename required as the argument 1")
        return
    filename = argv[1]
    ast = pycparser.parse_file(filename, use_cpp=False)

    packet_size_lookup = {}
    print('import struct')
    print()

    for (index, child) in enumerate(ast.children()):
        node_type = child[1].type
        # print(node_type)
        #node_name= child[1].type.name
        #print('{0} {1}'.format(node_type, node_name))
        if type(node_type) == Enum:
            print('# enum {}:'.format(node_type.name))
            for member in node_type.values.enumerators:
                member_name = member.name
                # print('  {} = ??'.format(member_name))
                member_value = int(member.value.value)
                print('{} = {}'.format(member_name, member_value))
            print()
        elif type(node_type) == Struct:
            packet_size = 0
            pack_sizes = []
            member_inits = []
            member_unpacks = []
            member_packs = []
            pack_index = 0
            type_formats = []
            new_subformat = True
            type_format_index = -1

            for (index, (member_id, member)) in enumerate(node_type.children()):
                member_name = member.name
                # print('  {} = ??'.format(enum_member_name))
                member_type = member.type
                if type(member_type) == TypeDecl:
                    if type(member_type.type) == IdentifierType:
                        member_type_name = member_type.type.names[0]
                        if new_subformat:
                            pack_sizes += [int(0)]
                            type_formats += ["('"]
                            new_subformat = False
                            type_format_index += 1
                            member_unpacks += ['    packet_elements = struct.Struct(self.__formats[{0}]).unpack(packet[:self._size[{0}]])'.format(type_format_index)]
                            member_packs += ['    packet_elements = ()']
                            pack_index = 0
                        if member_type_name == 'int':
                            packet_size += 4
                            pack_sizes[-1] += 4
                            member_inits += ['    self.{} = {}(0)'.format(member_name, member_type_name)]
                            type_formats[-1] += "i "
                        elif member_type_name == 'long':
                            packet_size += 8
                            pack_sizes[-1] += 8
                            member_inits += ['    self.{} = {}(0)'.format(member_name, 'int')]
                            type_formats[-1] += "L "
                        elif member_type_name == 'double':
                            packet_size += 8
                            pack_sizes[-1] += 8
                            member_inits += ['    self.{} = {}(0)'.format(member_name, 'float')]
                            type_formats[-1] += "d "
                        member_unpacks += ['    self.{} = packet_elements[{}]'.format(member_name, pack_index)]
                        member_packs += ['    packet_elements += (self.{},)'.format(member_name)]
                        pack_index += 1
                    elif type(member_type.type) == Enum:
                        if new_subformat:
                            pack_sizes += [int(0)]
                            type_formats += ["('"]
                            new_subformat = False
                            type_format_index += 1
                            member_unpacks += ['    packet_elements = struct.Struct(self.__formats[{0}]).unpack(packet[:self._size[{0}]])'.format(type_format_index)]
                            member_packs += ['    packet_elements = ()']
                            pack_index = 0
                        packet_size += 8
                        pack_sizes[-1] += 4
                        member_inits += ['    self.{} = int(0)  # {}'.format(member_name, member_type.type.name)]
                        member_unpacks += ['    self.{} = packet_elements[{}]'.format(member_name, pack_index)]
                        member_packs += ['    packet_elements += (self.{},)'.format(member_name)]
                        pack_index += 1
                        type_formats[-1] += "I "
                    elif type(member_type.type) == Struct:
                        if not new_subformat:
                            type_formats[-1] += "')"
                            new_subformat = True
                            member_packs += ['    packet += struct.Struct(self.__formats[{}]).pack(packet_elements)'.format(type_format_index)]
                        packet_size += packet_size_lookup[member_type.type.name]
                        member_inits += ['    self.{} = {}()'.format(member_name, member_type.type.name)]
                        if member_name == 'packetInfo':
                            member_inits += ['    self.packetInfo.packetHeader.lPacketSize = self.__packet_size']
                            if node_type.name == 'SingleMeasResultT':
                                packet_type = 'ES_DT_SingleMeasResult'
                            elif node_type.name == 'NivelResultT':
                                packet_type = 'ES_DT_NivelResult'
                            elif node_type.name == 'ReflectorPosResultT':
                                packet_type = 'ES_DT_ReflectorPosResult'
                            elif node_type.name == 'SingleMeasResult2T':
                                packet_type = 'ES_DT_SingleMeasResult2'
                            else:
                                packet_type = 'ES_DT_Command'
                            member_inits += ['    self.packetInfo.packetHeader.type = {}'.format(packet_type)]
                            if packet_type == 'ES_DT_Command':
                                if 'LongSystemParam' in node_type.name or 'DoubleSystemParam' in node_type.name:
                                    member_inits += ['    self.packetInfo.command = ES_C_{}eter'.format(node_type.name[:-2])]
                                else:
                                    member_inits += ['    self.packetInfo.command = ES_C_{}'.format(node_type.name[:-2])]
                        elif member_name == 'packetHeader':
                            if node_type.name == 'ErrorResponseT':
                                packet_type = 'ES_DT_Error'
                            elif node_type.name == 'SystemStatusChangeT':
                                packet_type = 'ES_DT_SystemStatusChange'
                            if node_type.name == 'ErrorResponseT' or node_type.name == 'SystemStatusChangeT':
                                member_inits += ['    self.packetHeader.lPacketSize = self.__packet_size']
                                member_inits += ['    self.packetHeader.type = {}'.format(packet_type)]
                        member_unpacks += ['    packet = self.{}.unpack(packet)'.format(member_name)]
                        member_packs += ['    packet += self.{}.pack()'.format(member_name)]
                    else:
                        print('    # Skipped {} {} {}'.format(type(member_type.type), member_type.type.name, member_name))
                elif type(member_type) == ArrayDecl:
                    array_dim = int(member_type.dim.value)
                    if new_subformat:
                        pack_sizes += [int(0)]
                        type_formats += ["('"]
                        new_subformat = False
                        type_format_index += 1
                        member_unpacks += ['    packet_elements = struct.Struct(self.__formats[{0}]).unpack(packet[:self._size[{0}]])'.format(type_format_index)]
                        member_packs += ['    packet_elements = ()']
                        pack_index = 0
                    packet_size += array_dim
                    pack_sizes[-1] += array_dim
                    member_inits += ['    self.{} = str()  # {} bytes max'.format(member_name, array_dim)]
                    type_formats[-1] += "{}s ".format(array_dim)
                    member_unpacks += ['    self.{} = packet_elements[{}]'.format(member_name, pack_index)]
                    member_packs += ['    packet_elements += (self.{},)'.format(member_name)]
                    pack_index += 1
            packet_size_lookup[node_type.name] = packet_size
            if not new_subformat:
                type_formats[-1] += "')"
                member_packs += ['    packet += struct.Struct(self.__formats[{}]).pack(packet_elements)'.format(type_format_index)]

            print('class {}(object):'.format(node_type.name))
            print('  def __init__(self):')
            print('    self.__packet_size = {}'.format(packet_size_lookup[node_type.name]))
            print('    self.__sizes = [{}]'.format(','.join(map(str, pack_sizes))))
            print('    self.__formats = [{}]'.format(','.join(type_formats)))
            for member_init in member_inits:
                print(member_init)
            print()

            print('  def unpack(self, packet):')
            for member_unpack in member_unpacks:
                print(member_unpack)
            if len(pack_sizes) > 0:
                print('    return packet[self.__sizes[{}]:]'.format(pack_sizes[-1]))
            else:
                print('    return packet')
            print()

            print('  def pack(self):')
            print("    packet = b''")
            for member_pack in member_packs:
                print(member_pack)
            print('    return packet')
            print()
        else:
            print('# Skipped object {}'.format(type(node_type)))

if __name__ == "__main__":
    main(sys.argv)
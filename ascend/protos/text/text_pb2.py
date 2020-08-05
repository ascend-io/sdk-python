# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ascend/protos/text/text.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='ascend/protos/text/text.proto',
  package='text',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x1d\x61scend/protos/text/text.proto\x12\x04text\"\x98\x03\n\nLineEnding\x12!\n\x02\x63r\x18\x01 \x01(\x0b\x32\x13.text.LineEnding.CrH\x00\x12&\n\x05\x63r_lf\x18\x02 \x01(\x0b\x32\x15.text.LineEnding.CrLfH\x00\x12!\n\x02lf\x18\x03 \x01(\x0b\x32\x13.text.LineEnding.LfH\x00\x12&\n\x05lf_cr\x18\x04 \x01(\x0b\x32\x15.text.LineEnding.LfCrH\x00\x12!\n\x02\x66\x66\x18\x05 \x01(\x0b\x32\x13.text.LineEnding.FfH\x00\x12!\n\x02ls\x18\x06 \x01(\x0b\x32\x13.text.LineEnding.LsH\x00\x12#\n\x03nel\x18\x07 \x01(\x0b\x32\x14.text.LineEnding.NelH\x00\x12!\n\x02ps\x18\x08 \x01(\x0b\x32\x13.text.LineEnding.PsH\x00\x12!\n\x02vt\x18\t \x01(\x0b\x32\x13.text.LineEnding.VtH\x00\x1a\x04\n\x02\x43r\x1a\x06\n\x04\x43rLf\x1a\x04\n\x02Lf\x1a\x06\n\x04LfCr\x1a\x04\n\x02\x46\x66\x1a\x04\n\x02Ls\x1a\x05\n\x03Nel\x1a\x04\n\x02Ps\x1a\x04\n\x02VtB\x08\n\x06\x64\x65tailb\x06proto3'
)




_LINEENDING_CR = _descriptor.Descriptor(
  name='Cr',
  full_name='text.LineEnding.Cr',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=381,
  serialized_end=385,
)

_LINEENDING_CRLF = _descriptor.Descriptor(
  name='CrLf',
  full_name='text.LineEnding.CrLf',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=387,
  serialized_end=393,
)

_LINEENDING_LF = _descriptor.Descriptor(
  name='Lf',
  full_name='text.LineEnding.Lf',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=395,
  serialized_end=399,
)

_LINEENDING_LFCR = _descriptor.Descriptor(
  name='LfCr',
  full_name='text.LineEnding.LfCr',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=401,
  serialized_end=407,
)

_LINEENDING_FF = _descriptor.Descriptor(
  name='Ff',
  full_name='text.LineEnding.Ff',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=409,
  serialized_end=413,
)

_LINEENDING_LS = _descriptor.Descriptor(
  name='Ls',
  full_name='text.LineEnding.Ls',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=415,
  serialized_end=419,
)

_LINEENDING_NEL = _descriptor.Descriptor(
  name='Nel',
  full_name='text.LineEnding.Nel',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=421,
  serialized_end=426,
)

_LINEENDING_PS = _descriptor.Descriptor(
  name='Ps',
  full_name='text.LineEnding.Ps',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=428,
  serialized_end=432,
)

_LINEENDING_VT = _descriptor.Descriptor(
  name='Vt',
  full_name='text.LineEnding.Vt',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=434,
  serialized_end=438,
)

_LINEENDING = _descriptor.Descriptor(
  name='LineEnding',
  full_name='text.LineEnding',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='cr', full_name='text.LineEnding.cr', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='cr_lf', full_name='text.LineEnding.cr_lf', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='lf', full_name='text.LineEnding.lf', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='lf_cr', full_name='text.LineEnding.lf_cr', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ff', full_name='text.LineEnding.ff', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ls', full_name='text.LineEnding.ls', index=5,
      number=6, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='nel', full_name='text.LineEnding.nel', index=6,
      number=7, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ps', full_name='text.LineEnding.ps', index=7,
      number=8, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='vt', full_name='text.LineEnding.vt', index=8,
      number=9, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_LINEENDING_CR, _LINEENDING_CRLF, _LINEENDING_LF, _LINEENDING_LFCR, _LINEENDING_FF, _LINEENDING_LS, _LINEENDING_NEL, _LINEENDING_PS, _LINEENDING_VT, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='detail', full_name='text.LineEnding.detail',
      index=0, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
  ],
  serialized_start=40,
  serialized_end=448,
)

_LINEENDING_CR.containing_type = _LINEENDING
_LINEENDING_CRLF.containing_type = _LINEENDING
_LINEENDING_LF.containing_type = _LINEENDING
_LINEENDING_LFCR.containing_type = _LINEENDING
_LINEENDING_FF.containing_type = _LINEENDING
_LINEENDING_LS.containing_type = _LINEENDING
_LINEENDING_NEL.containing_type = _LINEENDING
_LINEENDING_PS.containing_type = _LINEENDING
_LINEENDING_VT.containing_type = _LINEENDING
_LINEENDING.fields_by_name['cr'].message_type = _LINEENDING_CR
_LINEENDING.fields_by_name['cr_lf'].message_type = _LINEENDING_CRLF
_LINEENDING.fields_by_name['lf'].message_type = _LINEENDING_LF
_LINEENDING.fields_by_name['lf_cr'].message_type = _LINEENDING_LFCR
_LINEENDING.fields_by_name['ff'].message_type = _LINEENDING_FF
_LINEENDING.fields_by_name['ls'].message_type = _LINEENDING_LS
_LINEENDING.fields_by_name['nel'].message_type = _LINEENDING_NEL
_LINEENDING.fields_by_name['ps'].message_type = _LINEENDING_PS
_LINEENDING.fields_by_name['vt'].message_type = _LINEENDING_VT
_LINEENDING.oneofs_by_name['detail'].fields.append(
  _LINEENDING.fields_by_name['cr'])
_LINEENDING.fields_by_name['cr'].containing_oneof = _LINEENDING.oneofs_by_name['detail']
_LINEENDING.oneofs_by_name['detail'].fields.append(
  _LINEENDING.fields_by_name['cr_lf'])
_LINEENDING.fields_by_name['cr_lf'].containing_oneof = _LINEENDING.oneofs_by_name['detail']
_LINEENDING.oneofs_by_name['detail'].fields.append(
  _LINEENDING.fields_by_name['lf'])
_LINEENDING.fields_by_name['lf'].containing_oneof = _LINEENDING.oneofs_by_name['detail']
_LINEENDING.oneofs_by_name['detail'].fields.append(
  _LINEENDING.fields_by_name['lf_cr'])
_LINEENDING.fields_by_name['lf_cr'].containing_oneof = _LINEENDING.oneofs_by_name['detail']
_LINEENDING.oneofs_by_name['detail'].fields.append(
  _LINEENDING.fields_by_name['ff'])
_LINEENDING.fields_by_name['ff'].containing_oneof = _LINEENDING.oneofs_by_name['detail']
_LINEENDING.oneofs_by_name['detail'].fields.append(
  _LINEENDING.fields_by_name['ls'])
_LINEENDING.fields_by_name['ls'].containing_oneof = _LINEENDING.oneofs_by_name['detail']
_LINEENDING.oneofs_by_name['detail'].fields.append(
  _LINEENDING.fields_by_name['nel'])
_LINEENDING.fields_by_name['nel'].containing_oneof = _LINEENDING.oneofs_by_name['detail']
_LINEENDING.oneofs_by_name['detail'].fields.append(
  _LINEENDING.fields_by_name['ps'])
_LINEENDING.fields_by_name['ps'].containing_oneof = _LINEENDING.oneofs_by_name['detail']
_LINEENDING.oneofs_by_name['detail'].fields.append(
  _LINEENDING.fields_by_name['vt'])
_LINEENDING.fields_by_name['vt'].containing_oneof = _LINEENDING.oneofs_by_name['detail']
DESCRIPTOR.message_types_by_name['LineEnding'] = _LINEENDING
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

LineEnding = _reflection.GeneratedProtocolMessageType('LineEnding', (_message.Message,), {

  'Cr' : _reflection.GeneratedProtocolMessageType('Cr', (_message.Message,), {
    'DESCRIPTOR' : _LINEENDING_CR,
    '__module__' : 'ascend.protos.text.text_pb2'
    # @@protoc_insertion_point(class_scope:text.LineEnding.Cr)
    })
  ,

  'CrLf' : _reflection.GeneratedProtocolMessageType('CrLf', (_message.Message,), {
    'DESCRIPTOR' : _LINEENDING_CRLF,
    '__module__' : 'ascend.protos.text.text_pb2'
    # @@protoc_insertion_point(class_scope:text.LineEnding.CrLf)
    })
  ,

  'Lf' : _reflection.GeneratedProtocolMessageType('Lf', (_message.Message,), {
    'DESCRIPTOR' : _LINEENDING_LF,
    '__module__' : 'ascend.protos.text.text_pb2'
    # @@protoc_insertion_point(class_scope:text.LineEnding.Lf)
    })
  ,

  'LfCr' : _reflection.GeneratedProtocolMessageType('LfCr', (_message.Message,), {
    'DESCRIPTOR' : _LINEENDING_LFCR,
    '__module__' : 'ascend.protos.text.text_pb2'
    # @@protoc_insertion_point(class_scope:text.LineEnding.LfCr)
    })
  ,

  'Ff' : _reflection.GeneratedProtocolMessageType('Ff', (_message.Message,), {
    'DESCRIPTOR' : _LINEENDING_FF,
    '__module__' : 'ascend.protos.text.text_pb2'
    # @@protoc_insertion_point(class_scope:text.LineEnding.Ff)
    })
  ,

  'Ls' : _reflection.GeneratedProtocolMessageType('Ls', (_message.Message,), {
    'DESCRIPTOR' : _LINEENDING_LS,
    '__module__' : 'ascend.protos.text.text_pb2'
    # @@protoc_insertion_point(class_scope:text.LineEnding.Ls)
    })
  ,

  'Nel' : _reflection.GeneratedProtocolMessageType('Nel', (_message.Message,), {
    'DESCRIPTOR' : _LINEENDING_NEL,
    '__module__' : 'ascend.protos.text.text_pb2'
    # @@protoc_insertion_point(class_scope:text.LineEnding.Nel)
    })
  ,

  'Ps' : _reflection.GeneratedProtocolMessageType('Ps', (_message.Message,), {
    'DESCRIPTOR' : _LINEENDING_PS,
    '__module__' : 'ascend.protos.text.text_pb2'
    # @@protoc_insertion_point(class_scope:text.LineEnding.Ps)
    })
  ,

  'Vt' : _reflection.GeneratedProtocolMessageType('Vt', (_message.Message,), {
    'DESCRIPTOR' : _LINEENDING_VT,
    '__module__' : 'ascend.protos.text.text_pb2'
    # @@protoc_insertion_point(class_scope:text.LineEnding.Vt)
    })
  ,
  'DESCRIPTOR' : _LINEENDING,
  '__module__' : 'ascend.protos.text.text_pb2'
  # @@protoc_insertion_point(class_scope:text.LineEnding)
  })
_sym_db.RegisterMessage(LineEnding)
_sym_db.RegisterMessage(LineEnding.Cr)
_sym_db.RegisterMessage(LineEnding.CrLf)
_sym_db.RegisterMessage(LineEnding.Lf)
_sym_db.RegisterMessage(LineEnding.LfCr)
_sym_db.RegisterMessage(LineEnding.Ff)
_sym_db.RegisterMessage(LineEnding.Ls)
_sym_db.RegisterMessage(LineEnding.Nel)
_sym_db.RegisterMessage(LineEnding.Ps)
_sym_db.RegisterMessage(LineEnding.Vt)


# @@protoc_insertion_point(module_scope)

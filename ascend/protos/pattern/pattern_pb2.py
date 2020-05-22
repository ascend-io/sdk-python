# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ascend/protos/pattern/pattern.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='ascend/protos/pattern/pattern.proto',
  package='pattern',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n#ascend/protos/pattern/pattern.proto\x12\x07pattern\"L\n\x07Pattern\x12\x0e\n\x04glob\x18\x01 \x01(\tH\x00\x12\x0f\n\x05regex\x18\x02 \x01(\tH\x00\x12\x15\n\x0b\x65xact_match\x18\x03 \x01(\tH\x00\x42\t\n\x07patternb\x06proto3')
)




_PATTERN = _descriptor.Descriptor(
  name='Pattern',
  full_name='pattern.Pattern',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='glob', full_name='pattern.Pattern.glob', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='regex', full_name='pattern.Pattern.regex', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='exact_match', full_name='pattern.Pattern.exact_match', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
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
    _descriptor.OneofDescriptor(
      name='pattern', full_name='pattern.Pattern.pattern',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=48,
  serialized_end=124,
)

_PATTERN.oneofs_by_name['pattern'].fields.append(
  _PATTERN.fields_by_name['glob'])
_PATTERN.fields_by_name['glob'].containing_oneof = _PATTERN.oneofs_by_name['pattern']
_PATTERN.oneofs_by_name['pattern'].fields.append(
  _PATTERN.fields_by_name['regex'])
_PATTERN.fields_by_name['regex'].containing_oneof = _PATTERN.oneofs_by_name['pattern']
_PATTERN.oneofs_by_name['pattern'].fields.append(
  _PATTERN.fields_by_name['exact_match'])
_PATTERN.fields_by_name['exact_match'].containing_oneof = _PATTERN.oneofs_by_name['pattern']
DESCRIPTOR.message_types_by_name['Pattern'] = _PATTERN
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Pattern = _reflection.GeneratedProtocolMessageType('Pattern', (_message.Message,), {
  'DESCRIPTOR' : _PATTERN,
  '__module__' : 'ascend.protos.pattern.pattern_pb2'
  # @@protoc_insertion_point(class_scope:pattern.Pattern)
  })
_sym_db.RegisterMessage(Pattern)


# @@protoc_insertion_point(module_scope)

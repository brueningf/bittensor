""" Create and init Axon, whcih services Forward and Backward requests from other neurons.
"""
# The MIT License (MIT)
# Copyright © 2021 Yuma Rao
# Copyright © 2022 Opentensor Foundation

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import pydantic
import bittensor
from fastapi.responses import Response
from fastapi import Request
from typing import Dict, Optional, Tuple, Union, List, Callable

def cast_int(raw: str) -> int:
    return int( raw ) if raw != None else raw
def cast_float( raw: str ) -> float:
    return float( raw ) if raw != None else raw

class TerminalInfo( pydantic.BaseModel ):

    class Config:
        validate_assignment = True

    # The HTTP status code from: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
    status_code: Optional[int] = pydantic.Field(
        title = 'status_code',
        description = 'The HTTP status code from: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status',
        examples = 200,
        default = None,
        allow_mutation = True
    )
    _extract_status_code = pydantic.validator('status_code', pre=True, allow_reuse=True)(cast_int)

    # The HTTP status code from: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
    status_message: Optional[str] = pydantic.Field(
        title = 'status_message',
        description = 'The status_message associated with the status_code',
        examples = 'Success',
        default = None,
        allow_mutation = True
    )
        
    # Process time on this terminal side of call
    process_time: Optional[float] = pydantic.Field(
        title = 'process_time',
        description = 'Process time on this terminal side of call',
        examples = 0.1,
        default = None,
        allow_mutation = True
    )
    _extract_process_time = pydantic.validator('process_time', pre=True, allow_reuse=True)(cast_float)

    # The terminal ip.
    ip: Optional[ str ] = pydantic.Field(
        title = 'ip',
        description = 'The ip of the axon recieving the request.',
        examples = '198.123.23.1',
        default = None,
        allow_mutation = True
    )

    # The host port of the terminal.
    port: Optional[ int ] = pydantic.Field(
        title = 'port',
        description = 'The port of the terminal.',
        examples = '9282',
        default = None,
        allow_mutation = True
    )
    _extract_port = pydantic.validator('port', pre=True, allow_reuse=True)(cast_int)

    # The bittensor version on the terminal as an int.
    version: Optional[ int ] = pydantic.Field(
        title = 'version',
        description = 'The bittensor version on the axon as str(int)',
        examples = 111,
        default = None,
        allow_mutation = True
    )
    _extract_version = pydantic.validator('version', pre=True, allow_reuse=True)(cast_int)

    # A unique monotonically increasing integer nonce associate with the terminal
    nonce: Optional[ int ] = pydantic.Field(
        title = 'nonce',
        description = 'A unique monotonically increasing integer nonce associate with the terminal generated from time.monotonic_ns()',
        examples = 111111,
        default = None,
        allow_mutation = True
    )
    _extract_nonce = pydantic.validator('nonce', pre=True, allow_reuse=True)(cast_int)

    # A unique identifier associated with the terminal, set on the axon side.
    uuid: Optional[ str ] = pydantic.Field(
        title = 'uuid',
        description = 'A unique identifier associated with the terminal',
        examples = "5ecbd69c-1cec-11ee-b0dc-e29ce36fec1a",
        default = None,
        allow_mutation = True
    )

    # The bittensor version on the terminal as an int.
    hotkey: Optional[ str ] = pydantic.Field(
        title = 'hotkey',
        description = 'The ss58 encoded hotkey string of the terminal wallet.',
        examples = "5EnjDGNqqWnuL2HCAdxeEtN2oqtXZw6BMBe936Kfy2PFz1J1",
        default = None,
        allow_mutation = True
    )

    # A signature verifying the tuple (axon_nonce, axon_hotkey, dendrite_hotkey, axon_uuid)
    signature: Optional[ str ] = pydantic.Field(
        title = 'signature',
        description = 'A signature verifying the tuple (nonce, axon_hotkey, dendrite_hotkey, uuid)',
        examples = "0x0813029319030129u4120u10841824y0182u091u230912u",
        default = None,
        allow_mutation = True
    )

class Synapse( pydantic.BaseModel ):

    class Config:
        validate_assignment = True

    @pydantic.root_validator(pre=True)
    def set_name_type(cls, values):
        values['name'] = cls.__name__
        return values

    # Defines the http route name which is set on axon.attach( callable( request: RequestName ))
    name: Optional[ str ] = pydantic.Field(
        title = 'name',
        description = 'Defines the http route name which is set on axon.attach( callable( request: RequestName ))',
        examples = 'Forward',
        allow_mutation = True,
        default = None,
        repr = False
    )

    # The call timeout, set by the dendrite terminal.
    timeout: Optional[ float ] = pydantic.Field(
        title = 'timeout',
        description = 'Defines the total query length.',
        examples = 12.0,
        default = 12.0,
        allow_mutation = True,
        repr = False
    )

    # The dendrite Terminal Information.
    dendrite: Optional[ TerminalInfo ] = pydantic.Field(
        title = 'dendrite',
        description = 'Dendrite Terminal Information',
        examples = "bt.TerminalInfo",
        default = TerminalInfo(),
        allow_mutation = True,
        repr = False
    )

    # A axon terminal information
    axon: Optional[ TerminalInfo ] = pydantic.Field(
        title = 'axon',
        description = 'Axon Terminal Information',
        examples = "bt.TerminalInfo",
        default = TerminalInfo(),
        allow_mutation = True,
        repr = False
    )

    def to_headers(self) -> dict:
        base_class = Synapse(**self.dict())
        headers = {
            'name': base_class.name,
            'timeout': str(base_class.timeout),
        }
        headers.update( { str('axon_'+k):str(v) for k, v in base_class.axon.dict().items() if v != None} )
        headers.update( { str('dendrite_'+k):str(v) for k, v in base_class.dendrite.dict().items() if v != None})
        return headers

    def from_headers( headers: dict ) -> 'Synapse':
        synapse = bittensor.Synapse()
        synapse.timeout = float(headers.get('timeout', None))
        synapse.name = headers.get('name', None)
        for k, v in headers.items():
            try:
                k = k.split('axon_')[1]
                setattr( synapse.axon, k, v )
            except: pass
            try:
                k = k.split('dendrite_')[1]
                setattr( synapse.dendrite, k, v )
            except: pass
        return synapse



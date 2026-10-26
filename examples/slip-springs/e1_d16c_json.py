"""Bounded strict streaming JSON inspection, without materializing skipped values."""
import json
import math
import re

from e1_d1_pilot import require

DELIMITER=re.compile(r'[\s,\]}:]')


class Reader:
    def __init__(self,stream,limit,paths):
        self.stream=stream;self.limit=limit;self.total=0;self.buffer='';self.pos=0;self.eof=False
        self.paths=set(paths);self.found={};self.decoder=json.JSONDecoder()

    def fill(self):
        chunk=self.stream.read(65536)
        self.total+=len(chunk)
        require(self.total<=self.limit,'decompressed JSON limit exceeded; no data discarded')
        self.buffer=self.buffer[self.pos:]+chunk;self.pos=0;self.eof=not chunk
        return bool(chunk)

    def peek(self):
        while True:
            while self.pos<len(self.buffer) and self.buffer[self.pos].isspace():self.pos+=1
            if self.pos<len(self.buffer):return self.buffer[self.pos]
            if self.eof or not self.fill():return ''

    def expect(self,char):
        require(self.peek()==char,'invalid JSON: expected '+char)
        self.pos+=1

    def string(self):
        require(self.peek()=='"','JSON string required')
        while True:
            try:
                value,end=json.decoder.scanstring(self.buffer,self.pos+1,True)
                self.pos=end;return value
            except (ValueError,json.JSONDecodeError):
                require(not self.eof and len(self.buffer)-self.pos<=1024**2,'invalid/oversize JSON string')
                self.fill()

    def scalar(self):
        if self.peek()=='"':return self.string()
        while True:
            match=DELIMITER.search(self.buffer,self.pos)
            if match or self.eof:
                end=match.start() if match else len(self.buffer)
                token=self.buffer[self.pos:end];require(token and len(token)<=128,'invalid JSON scalar')
                value=json.loads(token)
                require(value is None or type(value) in (bool,int,float),'invalid scalar')
                require(type(value) is not float or math.isfinite(value),'nonfinite JSON number')
                self.pos=end;return value
            require(len(self.buffer)-self.pos<=128,'oversize JSON scalar');self.fill()

    def value(self,path=(),capture=False,depth=0):
        require(depth<=64,'JSON nesting limit exceeded')
        selected=path in self.paths;capture=capture or selected
        char=self.peek();require(bool(char),'truncated JSON')
        if char=='{':
            self.pos+=1;seen=set();result={} if capture else None
            if self.peek()!='}':
                while True:
                    key=self.string();require(key not in seen,'duplicate JSON key: '+key);seen.add(key)
                    require(len(seen)<=100000,'JSON object member cap exceeded')
                    self.expect(':');value=self.value(path+(key,),capture,depth+1)
                    if capture:result[key]=value
                    if self.peek()!=',':break
                    self.pos+=1
            self.expect('}')
        elif char=='[':
            self.pos+=1;result=[] if capture else None;index=0
            if self.peek()!=']':
                while True:
                    value=self.value(path+(index,),capture,depth+1)
                    if capture:result.append(value)
                    index+=1
                    if self.peek()!=',':break
                    self.pos+=1
            self.expect(']')
        else:
            value=self.scalar();result=value if capture else None
        if selected:self.found[path]=result
        return result


def extract(stream,paths,limit):
    reader=Reader(stream,limit,paths);reader.value()
    require(reader.peek()=='','trailing JSON data')
    return reader.found

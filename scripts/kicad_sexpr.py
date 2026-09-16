"""Small lossless-atom S-expression reader/writer for the KiCad conversion."""
import re,json
class Atom(str): pass
def parse(text):
    tokens=iter(re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',text))
    def node(token):
        if token=='(':
            out=[]
            for t in tokens:
                if t==')':return out
                out.append(node(t))
            raise ValueError('Unclosed expression')
        return json.loads(token) if token.startswith('"') else Atom(token)
    return node(next(tokens))
def dump(x):
    if isinstance(x,list):return '('+' '.join(dump(v) for v in x)+')'
    if isinstance(x,Atom):return str(x)
    if isinstance(x,(int,float)):return str(round(x,6))
    return json.dumps(x,ensure_ascii=False)
def children(x,key):return [v for v in x if isinstance(v,list) and v and v[0]==key]
def child(x,key):return next((v for v in children(x,key)),None)
def walk(x,key):
    if isinstance(x,list):
        if x and x[0]==key:yield x
        for v in x:yield from walk(v,key)

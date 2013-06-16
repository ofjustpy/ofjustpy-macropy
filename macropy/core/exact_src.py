from macropy.core import unparse
from ast import *
from walkers import Walker


def linear_index(line_lengths, lineno, col_offset):
    prev_length = sum(line_lengths[:lineno-1]) + lineno-2
    out = prev_length + col_offset + 1
    return out

@Walker
def indexer(tree, collect, **kw):
    try:
        unparse(tree)
        collect((tree.lineno, tree.col_offset))
    except Exception, e:
        pass

_transforms = {
    GeneratorExp: "(%s)",
    ListComp: "[%s]",
    SetComp: "{%s}",
    DictComp: "{%s}"
}



def exact_src(tree, src, indexes, line_lengths):
    all_child_pos = sorted(indexer.collect(tree))
    start_index = linear_index(line_lengths(), *all_child_pos[0])

    last_child_index = linear_index(line_lengths(), *all_child_pos[-1])

    first_successor_index = indexes()[min(indexes().index(last_child_index)+1, len(indexes())-1)]

    for end_index in range(last_child_index, first_successor_index+1):

        prelim = src[start_index:end_index]
        prelim = _transforms.get(type(tree), "%s") % prelim


        if isinstance(tree, stmt):
            prelim = prelim.replace("\n" + " " * tree.col_offset, "\n")

        if isinstance(tree, list):
            prelim = prelim.replace("\n" + " " * tree[0].col_offset, "\n")

        try:
            if isinstance(tree, expr):
                x = "(" + prelim + ")"
            else:
                x = prelim
            import ast
            parsed = ast.parse(x)
            if unparse(parsed).strip() == unparse(tree).strip():
                return prelim

        except SyntaxError as e:
            pass
    raise ExactSrcException()
class ExactSrcException(Exception):
    pass
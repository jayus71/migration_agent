"""MSAdapter's documented import conversion, without operator or optimizer patches."""

import ast


class NativeImports(ast.NodeTransformer):
    def visit_Import(self, node):
        imports = []
        for alias in node.names:
            if alias.name == 'torch' or alias.name.startswith('torch.'):
                name = 'msadapter' + alias.name[len('torch'):]
                if alias.asname:
                    imports.append(ast.Import(names=[ast.alias(name=name, asname=alias.asname)]))
                else:
                    imports.append(ast.Import(names=[ast.alias(name='msadapter', asname='torch')]))
                    if alias.name != 'torch':
                        imports.append(ast.Import(names=[ast.alias(name=name)]))
            else:
                imports.append(ast.Import(names=[alias]))
        return imports

    def visit_ImportFrom(self, node):
        if node.module == 'torch' or (node.module or '').startswith('torch.'):
            node.module = 'msadapter' + node.module[len('torch'):]
        return node


def convert(source):
    return ast.unparse(ast.fix_missing_locations(NativeImports().visit(ast.parse(source)))) + '\n'

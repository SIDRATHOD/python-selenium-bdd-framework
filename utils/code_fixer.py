import ast

class CodeFixer(ast.NodeTransformer):
    """
    Uses AST to safely rewrite a locator variable assignment in a Python file.
    """
    def __init__(self, target_variable, new_value_tuple):
        self.target_variable = target_variable
        self.new_value_tuple = new_value_tuple
        self.fix_applied = False

    def visit_Assign(self, node):
        # Visit an assignment statement (e.g., VAR = ...)
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == self.target_variable:
                # Found the variable we want to change.
                # Now, ensure it's a Locator call.
                if isinstance(node.value, ast.Call) and getattr(node.value.func, 'id', '') == 'Locator':
                    # It is. Let's change the first argument (the locator tuple).
                    new_tuple_node = ast.Constant(value=self.new_value_tuple)
                    node.value.args[0] = new_tuple_node
                    self.fix_applied = True
        return node

def rewrite_locator_file(file_path, variable_name, new_locator):
    """
    Reads a Python file, uses the AST transformer to rewrite a locator,
    and writes the changes back to the file.
    """
    with open(file_path, 'r') as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    transformer = CodeFixer(variable_name, new_locator)
    new_tree = transformer.visit(tree)

    if transformer.fix_applied:
        # Add necessary imports if they are missing
        imports = {node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)}
        if 'ast' not in imports:
            # This is a simple way; a more robust solution would check all imports.
            pass # For now, we assume imports are correct.

        # Unparse the modified tree back to source code
        new_source = ast.unparse(new_tree)
        with open(file_path, 'w') as f:
            f.write(new_source)
        return True
    return False
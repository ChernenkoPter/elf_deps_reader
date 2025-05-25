#!/usr/bin/env python3
import subprocess
import sys

class DependencyNode:
    def __init__(self, basename, absolute_path):
        self.basename = basename
        self.absolute_path = absolute_path
        self.children = []

    def find(self, name):
        return name == self.basename or name == self.absolute_path or any(child.find(name) for child in self.children)

    def add_child(self, child_node):
        self.children.append(child_node)


def parse(output):
    """Convert lddtree output into dependency tree"""
    lines = output.splitlines()
    elf_name = lines[0].split()[0]
    elf_absolute_path = lines[0].split()[2]
    root_node = DependencyNode(elf_name, elf_absolute_path)
    interpreter = lines[0].split()[-1].rstrip(')')
    stack = [(0, root_node)]

    for line in lines[1:]:
        line = line.rstrip()
        if not line:
            continue

        indent = len(line) - len(line.lstrip())
        dep_name = line.lstrip().split(' => ')[0]
        absolute_dep_path = line.lstrip().split(' => ')[1]
        node = DependencyNode(dep_name, absolute_dep_path)

        while stack[-1][0] >= indent:
            stack.pop()
        if not root_node.find(dep_name):
            stack[-1][1].add_child(node)
        stack.append((indent, node))

    return interpreter, root_node


def get_dependencies(elf_file):
    """Get dependencies using lddtree"""
    try:
        result = subprocess.run(['lddtree', '-a', elf_file],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                check=True)
        return parse(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running lddtree on {elf_file}: {e.stderr}", file=sys.stderr)
        return None, None


def dependency_list(root):
    """Convert dependency tree to dependency list"""
    dependencies = root.children
    i = 0
    while i < len(dependencies):
        dep = dependencies[i]
        for child in dep.children:
            dependencies.append(child)
        i += 1

    return dependencies


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <elf_file>", file=sys.stderr)
        sys.exit(1)

    elf_file = sys.argv[1]
    interpreter, root = get_dependencies(elf_file)

    for dep in dependency_list(root):
        print(dep.basename, end=" ")
    print()


if __name__ == "__main__":
    main()
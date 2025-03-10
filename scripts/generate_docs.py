#!/usr/bin/env python3
"""
Documentation generator for MedConnect.

This script generates API documentation from the codebase.
"""

import os
import sys
import json
import argparse
import logging
import inspect
import importlib
import pkgutil
from typing import Dict, Any, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def get_module_docstring(module):
    """Get module docstring."""
    return module.__doc__ or ""


def get_class_docstring(cls):
    """Get class docstring."""
    return cls.__doc__ or ""


def get_function_docstring(func):
    """Get function docstring."""
    return func.__doc__ or ""


def get_function_signature(func):
    """Get function signature."""
    try:
        return str(inspect.signature(func))
    except ValueError:
        return "()"


def get_module_functions(module):
    """Get all functions in a module."""
    functions = []
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if obj.__module__ == module.__name__:
            functions.append((name, obj))
    return functions


def get_module_classes(module):
    """Get all classes in a module."""
    classes = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__:
            classes.append((name, obj))
    return classes


def get_class_methods(cls):
    """Get all methods in a class."""
    methods = []
    for name, obj in inspect.getmembers(cls, inspect.isfunction):
        if name.startswith("_") and name != "__init__":
            continue
        methods.append((name, obj))
    return methods


def generate_module_docs(module_name: str) -> Dict[str, Any]:
    """Generate documentation for a module."""
    try:
        module = importlib.import_module(module_name)
        
        module_doc = {
            "name": module_name,
            "docstring": get_module_docstring(module),
            "functions": [],
            "classes": []
        }
        
        # Document functions
        for name, func in get_module_functions(module):
            function_doc = {
                "name": name,
                "signature": get_function_signature(func),
                "docstring": get_function_docstring(func)
            }
            module_doc["functions"].append(function_doc)
        
        # Document classes
        for name, cls in get_module_classes(module):
            class_doc = {
                "name": name,
                "docstring": get_class_docstring(cls),
                "methods": []
            }
            
            # Document methods
            for method_name, method in get_class_methods(cls):
                method_doc = {
                    "name": method_name,
                    "signature": get_function_signature(method),
                    "docstring": get_function_docstring(method)
                }
                class_doc["methods"].append(method_doc)
            
            module_doc["classes"].append(class_doc)
        
        return module_doc
    
    except ImportError as e:
        logger.warning(f"Could not import module {module_name}: {e}")
        return {
            "name": module_name,
            "error": str(e)
        }


def discover_modules(package_name: str) -> List[str]:
    """Discover all modules in a package."""
    try:
        package = importlib.import_module(package_name)
        modules = []
        
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            if is_pkg:
                modules.extend(discover_modules(name))
            else:
                modules.append(name)
        
        return modules
    
    except ImportError as e:
        logger.warning(f"Could not import package {package_name}: {e}")
        return []


def generate_markdown_docs(docs: Dict[str, Any], output_dir: str) -> None:
    """Generate Markdown documentation."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate index file
    with open(os.path.join(output_dir, "index.md"), "w") as f:
        f.write("# MedConnect API Documentation\n\n")
        f.write("## Modules\n\n")
        
        for module in docs["modules"]:
            module_name = module["name"]
            module_file = module_name.replace(".", "_") + ".md"
            f.write(f"- [{module_name}]({module_file})\n")
    
    # Generate module files
    for module in docs["modules"]:
        module_name = module["name"]
        module_file = os.path.join(output_dir, module_name.replace(".", "_") + ".md")
        
        with open(module_file, "w") as f:
            f.write(f"# {module_name}\n\n")
            
            if module.get("docstring"):
                f.write(f"{module['docstring']}\n\n")
            
            if module.get("error"):
                f.write(f"**Error:** {module['error']}\n\n")
                continue
            
            if module.get("functions"):
                f.write("## Functions\n\n")
                
                for func in module["functions"]:
                    f.write(f"### `{func['name']}{func['signature']}`\n\n")
                    
                    if func.get("docstring"):
                        f.write(f"{func['docstring']}\n\n")
            
            if module.get("classes"):
                f.write("## Classes\n\n")
                
                for cls in module["classes"]:
                    f.write(f"### `{cls['name']}`\n\n")
                    
                    if cls.get("docstring"):
                        f.write(f"{cls['docstring']}\n\n")
                    
                    if cls.get("methods"):
                        f.write("#### Methods\n\n")
                        
                        for method in cls["methods"]:
                            f.write(f"##### `{method['name']}{method['signature']}`\n\n")
                            
                            if method.get("docstring"):
                                f.write(f"{method['docstring']}\n\n")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate API documentation for MedConnect")
    parser.add_argument("--output", default="./docs", help="Output directory for documentation")
    args = parser.parse_args()
    
    logger.info("Generating API documentation")
    
    # Discover modules
    packages = ["api", "core", "data"]
    modules = []
    
    for package in packages:
        modules.extend(discover_modules(package))
    
    # Generate documentation
    docs = {
        "modules": []
    }
    
    for module_name in modules:
        logger.info(f"Documenting module: {module_name}")
        module_doc = generate_module_docs(module_name)
        docs["modules"].append(module_doc)
    
    # Generate Markdown documentation
    generate_markdown_docs(docs, args.output)
    
    logger.info(f"Documentation generated in {args.output}")


if __name__ == "__main__":
    main() 
import os
from pathlib import Path
from typing import Dict, List, Optional
import ast
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class CodeAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.context_cache: Dict[str, Dict] = {}
        self.observer = Observer()
        self.setup_file_watcher()

    def analyze_file(self, file_path: str) -> Dict:
        """Analyze a single file and extract its context."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract basic information
            file_info = {
                'path': str(file_path),
                'imports': [],
                'classes': [],
                'functions': [],
                'dependencies': set()
            }
            
            # Analyze AST
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        file_info['imports'].append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    file_info['imports'].append(f"{node.module}.{node.names[0].name}")
                elif isinstance(node, ast.ClassDef):
                    file_info['classes'].append({
                        'name': node.name,
                        'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    })
                elif isinstance(node, ast.FunctionDef):
                    file_info['functions'].append({
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args]
                    })
            
            return file_info
        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")
            return {}

    def analyze_project(self) -> Dict:
        """Analyze the entire project and generate context."""
        project_context = {
            'files': {},
            'dependencies': set(),
            'structure': {}
        }
        
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.project_root)
                    file_context = self.analyze_file(file_path)
                    project_context['files'][relative_path] = file_context
                    project_context['dependencies'].update(file_context.get('dependencies', set()))
        
        return project_context

    def setup_file_watcher(self):
        """Set up file system watcher to detect changes."""
        class CodeChangeHandler(FileSystemEventHandler):
            def __init__(self, analyzer):
                self.analyzer = analyzer

            def on_modified(self, event):
                if not event.is_directory and event.src_path.endswith('.py'):
                    self.analyzer.update_context(event.src_path)

        handler = CodeChangeHandler(self)
        self.observer.schedule(handler, self.project_root, recursive=True)
        self.observer.start()

    def update_context(self, file_path: str):
        """Update context when a file changes."""
        relative_path = os.path.relpath(file_path, self.project_root)
        self.context_cache[relative_path] = self.analyze_file(file_path)

    def get_context(self, file_path: Optional[str] = None) -> Dict:
        """Get context for a specific file or the entire project."""
        if file_path:
            return self.context_cache.get(file_path, {})
        return self.analyze_project()

    def stop(self):
        """Stop the file watcher."""
        self.observer.stop()
        self.observer.join() 
import sys
import pytest
from pathlib import Path

def run_tests():
    tests_dir = Path(__file__).resolve().parent
    args = [str(tests_dir), "-v", "--color=yes"]
    args.extend(sys.argv[1:])
    
    return pytest.main(args)

if __name__ == "__main__":
    backend_dir = Path(__file__).resolve().parent.parent
    sys.path.append(str(backend_dir))
    
    exit_code = run_tests()
    
    sys.exit(exit_code)
# pystock


import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



import sys
import os
import argparse
print(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
import os
import argparse

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
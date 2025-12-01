import subprocess
import time
import sys
import os
from typing import List, Dict, Any


class ScriptScheduler:
    def __init__(self):
        self.scripts = []

    def add_script(self, script_path: str, args: List[str] = None, wait: bool = True,
                   timeout: int = None, working_dir: str = None):
        """添加脚本到调度队列

        Args:
            script_path: 脚本路径
            args: 命令行参数列表
            wait: 是否等待脚本执行完成
            timeout: 执行超时时间（秒）
            working_dir: 工作目录
        """
        script_info = {
            'path': script_path,
            'args': args or [],
            'wait': wait,
            'timeout': timeout,
            'working_dir': working_dir
        }
        self.scripts.append(script_info)

    def run_scripts(self):
        """按顺序执行所有脚本"""
        for i, script in enumerate(self.scripts, 1):
            print(f"\n{'=' * 50}")
            print(f"执行脚本 {i}/{len(self.scripts)}: {script['path']}")
            print(f"{'=' * 50}")

            try:
                # 构建命令
                cmd = ['python', script['path']] + script['args']

                # 设置工作目录
                cwd = script.get('working_dir') or os.path.dirname(script['path'])

                # 执行脚本
                if script['wait']:
                    # 等待执行完成
                    result = subprocess.run(
                        cmd,
                        cwd=cwd,
                        timeout=script.get('timeout'),
                        capture_output=True,
                        text=True
                    )

                    # 输出结果
                    if result.stdout:
                        print("输出:", result.stdout)
                    if result.stderr:
                        print("错误:", result.stderr)

                    # 检查返回码
                    if result.returncode != 0:
                        print(f"警告: 脚本 {script['path']} 返回非零状态码: {result.returncode}")

                else:
                    # 异步执行
                    subprocess.Popen(cmd, cwd=cwd)
                    print(f"脚本 {script['path']} 已启动（异步执行）")

                print(f"✓ 脚本 {script['path']} 执行完成")

            except subprocess.TimeoutExpired:
                print(f"✗ 脚本 {script['path']} 执行超时")
            except FileNotFoundError:
                print(f"✗ 脚本文件未找到: {script['path']}")
            except Exception as e:
                print(f"✗ 执行脚本 {script['path']} 时发生错误: {e}")

            # 脚本间延时
            if i < len(self.scripts):
                time.sleep(1)


def main():
    """使用示例"""
    scheduler = ScriptScheduler()

    # 添加要执行的脚本
    scheduler.add_script(r'G:\chane_git\pystock\demo\tmp\a.py')
    scheduler.add_script(r'G:\chane_git\pystock\demo\tmp\b.py')
    # scheduler.add_script('b.py', args=['--a', 'a'])
    # scheduler.add_script('c.py', args=['--input', 'data.txt', '--output', 'result.csv'])

    # 异步执行的脚本（不等待完成）
    # scheduler.add_script('background_task.py', wait=False)

    # 带超时的脚本
    # scheduler.add_script('long_running.py', timeout=300)  # 5分钟超时

    # 执行所有脚本
    scheduler.run_scripts()


if __name__ == "__main__":
    main()
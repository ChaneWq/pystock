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
# 添加项目路径
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mysql_tools.file_to_db_importer import FileToMySQL

# python upload_db.py --file "new_全部Ａ股20251127.txt" --table "tmp_sku8"
def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='将文件数据导入MySQL数据库')
    parser.add_argument('--file', required=True, help='要导入的文件路径（必需）')
    parser.add_argument('--table', required=True, help='目标MySQL表名（必需）')

    # 解析参数
    args = parser.parse_args()

    # 数据库配置（固定）
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'root',
        'database': 'stock'
    }

    # 固定参数
    csv_file_path = args.file
    mysql_table_name = args.table

    # 创建导入器实例
    importer = FileToMySQL(db_config)

    # 先预览文件结构
    importer.preview_file_structure(csv_file_path, sep='\t', nrows=5)

    # CSV参数（固定）
    csv_params = {
        'file_type': 'auto',
        'sep': '\t',
        'encoding': None,
        'batch_size': 1000
    }

    # 执行导入
    importer.file_to_mysql(
        file_path=csv_file_path,
        table_name=mysql_table_name,
        mode='create_and_insert',
        **csv_params
    )


if __name__ == "__main__":
    main()
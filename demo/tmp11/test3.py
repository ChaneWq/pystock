import argparse
import sys


def process_file(input_file, dict_file, output_file=None):
    """
    读取文件的第一行并替换内容

    Args:
        input_file: 输入文件名
        dict_file: 字典文件名
        output_file: 输出文件名（可选，默认为'new_'+输入文件名）
    """
    try:
        # 读取输入文件
        with open(input_file, 'r', encoding='gbk') as file:
            lines = file.readlines()

        # 读取字典文件
        column_dict = {}
        with open(dict_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if len(parts) >= 2:
                        eng, chn = parts[0], parts[1]
                        column_dict[chn] = eng

        # 处理第一行
        l1 = lines[0].strip().split('\t')

        # 调试信息：显示每个字段的索引和内容
        for i in range(len(l1)):
            print(f"{i}: '{l1[i]}'")
            if l1[i] in column_dict:
                l1[i] = column_dict[l1[i]]
                print(f"  -> 替换为: '{l1[i]}'")

        # 生成新的第一行
        newline = '\t'.join(l1) + '\n'
        lines[0] = newline

        # 确定输出文件名
        if output_file is None:
            import os
            output_file = 'new_' + os.path.basename(input_file)

        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines(lines)

        print(f"文件第一行已成功修改！输出文件: {output_file}")

    except FileNotFoundError as e:
        print(f"错误：文件未找到 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"处理文件时发生错误：{e}")
        sys.exit(1)

# python script.py 全部Ａ股20251127.txt column_dict.txt
def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='处理文件第一行，根据字典替换内容')
    parser.add_argument('input_file', help='输入文件名（如：全部Ａ股20251127.txt）')
    parser.add_argument('dict_file', help='字典文件名（如：column_dict.txt）')
    parser.add_argument('-output', '--output_file', help='输出文件名（可选）')

    # 解析参数
    args = parser.parse_args()

    # 调用处理函数
    process_file(args.input_file, args.dict_file, args.output_file)


if __name__ == "__main__":
    main()
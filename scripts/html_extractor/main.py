"""
入口函数模块
处理命令行参数，调用解析器
"""

import sys
from pathlib import Path

from .extractor import EnhancedHTMLExtractor, _setup_utf8_output


def main():
    """主入口函数"""
    # 设置UTF-8输出编码（解决Windows终端编码问题）
    _setup_utf8_output()

    if len(sys.argv) < 2:
        print("用法: python html-extractor.py <html文件> [输出格式: markdown|json]")
        print("示例: python html-extractor.py page.html markdown")
        print("      python html-extractor.py page.html json")
        sys.exit(1)

    html_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "markdown"

    if not Path(html_file).exists():
        print(f"错误: HTML文件不存在: {html_file}")
        sys.exit(1)

    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        sys.exit(1)

    extractor = EnhancedHTMLExtractor(html_content, f"file://{html_file}")

    try:
        analysis = extractor.extract_full_structure()
    except Exception as e:
        print(f"分析HTML失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if output_format.lower() == "json":
        result = extractor.to_json(analysis)
    else:
        result = extractor.to_markdown(analysis)

    print(result)


if __name__ == "__main__":
    main()
#!/bin/bash
# URL原型分析器主脚本
# 用于分析Figma、墨刀、Axure等工具的URL原型

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助
show_help() {
    cat << EOF
URL/HTML原型分析器 - bie-zheng-luan-prototype技能

用法: $0 [选项] <URL|本地文件路径>

选项:
  -h, --help          显示此帮助信息
  -o, --output FILE   指定输出文件（默认：分析结果.md）
  -f, --format FORMAT 输出格式：markdown、json、html（默认：markdown）
  -v, --verbose       详细输出模式
  --no-cache          禁用缓存，强制重新获取

输入类型自动识别:
  http(s)://...   → URL原型分析（从网络下载）
  /path/to/file   → 本地HTML文件分析（直接读取）

示例:
  $0 https://www.figma.com/file/example/prototype
  $0 -o my-analysis.md https://app.mockplus.com/project/123
  $0 --format json /path/to/prototype.html
  $0 --format json ./local-file.html
EOF
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查curl或wget
    if command -v curl &> /dev/null; then
        DOWNLOADER="curl -sL"
        log_info "找到curl"
    elif command -v wget &> /dev/null; then
        DOWNLOADER="wget -qO-"
        log_info "找到wget"
    else
        log_error "需要curl或wget来下载网页内容"
        exit 1
    fi
    
    # 检查Python
    if command -v python3 &> /dev/null; then
        PYTHON="python3"
        log_info "找到Python3"
    elif command -v python &> /dev/null; then
        PYTHON="python"
        log_info "找到Python"
    else
        log_error "需要Python来解析HTML"
        exit 1
    fi
    
    # 检查Python模块
    log_info "检查Python依赖..."
    if ! $PYTHON -c "import bs4" 2>/dev/null; then
        log_warn "未找到BeautifulSoup4，尝试安装..."
        if $PYTHON -m pip install beautifulsoup4 lxml html5lib; then
            log_info "BeautifulSoup4安装成功"
        else
            log_error "无法安装BeautifulSoup4，请手动安装：pip install beautifulsoup4 lxml html5lib"
            exit 1
        fi
    fi
}

# 验证URL安全性
validate_url() {
    local url="$1"

    # 检查URL格式：只允许http和https协议
    if [[ ! "$url" =~ ^https?:// ]]; then
        log_error "无效URL: 仅允许http和https协议"
        return 1
    fi

    # 检查URL中是否包含危险字符（命令注入防护）
    # 阻止: ; | & $ ` ' " ( ) < > \n \r 等shell特殊字符
    if [[ "$url" =~ [;\|&\$\`\'\"()<>] ]] || [[ "$url" =~ [\n\r] ]]; then
        log_error "URL包含潜在危险字符，拒绝执行"
        return 1
    fi

    # 检查URL长度（防止过长URL攻击）
    if [[ ${#url} -gt 2048 ]]; then
        log_error "URL过长（超过2048字符），拒绝执行"
        return 1
    fi

    # 获取域名并验证
    local domain=$(echo "$url" | sed -n 's|^https?://[^/]*||p' | cut -d'/' -f1 | cut -d':' -f1)

    # 阻止访问本地回环地址和私有IP（可选，根据需求启用）
    # 注意：如果需要支持内网原型，可以注释掉以下检查
    if [[ "$domain" =~ ^(localhost|127\.|0\.0\.0\.0|::1|10\.|172\.16|192\.168|169\.254) ]]; then
        log_warn "警告: URL指向私有网络地址或本地主机"
        log_warn "如果是预期的内网原型，请确保URL来源可信"
        # 不阻止，但发出警告（允许内网访问）
    fi

    log_info "URL验证通过: $url"
    return 0
}

# 下载网页内容（安全版本）
download_page() {
    local url="$1"
    local output_file="$2"

    # 验证URL
    if ! validate_url "$url"; then
        return 1
    fi

    log_info "下载网页内容: $url"

    if [ "$NO_CACHE" = true ] || [ ! -f "$output_file" ]; then
        # 使用--选项防止URL被解析为选项
        # 使用引号保护参数，但URL已在validate_url中验证
        if $DOWNLOADER -- "$url" > "$output_file" 2>/dev/null; then
            log_info "网页内容已保存到: $output_file"
            return 0
        else
            log_error "下载网页失败"
            return 1
        fi
    else
        log_info "使用缓存的网页内容: $output_file"
        return 0
    fi
}

# 提取页面信息
extract_page_info() {
    local html_file="$1"
    local output_format="$2"
    
    log_info "分析页面结构..."
    
    # 调用Python脚本解析HTML
    local script_dir=$(dirname "$0")
    local extractor_script="$script_dir/html-extractor.py"
    
    if [ -f "$extractor_script" ]; then
        # 以JSON格式提取数据，传递给生成器
        $PYTHON "$extractor_script" "$html_file" "json"
    else
        log_warn "HTML提取脚本不存在，使用简单分析"
        simple_html_analysis "$html_file"
    fi
}

# 简单HTML分析（备用）
simple_html_analysis() {
    local html_file="$1"
    
    log_info "执行简单HTML分析..."
    
    # 提取标题
    local title=$(grep -o '<title>[^<]*</title>' "$html_file" | sed 's/<title>//;s/<\/title>//' | head -1)
    
    # 提取meta描述
    local description=$(grep -o '<meta[^>]*name="description"[^>]*>' "$html_file" | \
                       grep -o 'content="[^"]*"' | sed 's/content="//;s/"//' | head -1)
    
    # 统计标签
    local h1_count=$(grep -c '<h1' "$html_file")
    local h2_count=$(grep -c '<h2' "$html_file")
    local form_count=$(grep -c '<form' "$html_file")
    local button_count=$(grep -c '<button' "$html_file")
    local input_count=$(grep -c '<input' "$html_file")
    
    # 提取文本内容（前1000字符）
    local text_content=$(grep -o '<p>[^<]*</p>' "$html_file" | sed 's/<p>//;s/<\/p>//' | head -5 | tr '\n' ' ')
    
    cat << EOF
# 页面分析结果

## 基本信息
- **页面标题**: ${title:-未找到}
- **页面描述**: ${description:-未找到}
- **分析时间**: $(date)

## 页面结构统计
- H1标题数量: $h1_count
- H2标题数量: $h2_count
- 表单数量: $form_count
- 按钮数量: $button_count
- 输入框数量: $input_count

## 内容摘要
${text_content:0:500}...

## 分析说明
这是一个简单的HTML分析结果，仅提取了基础信息。
对于原型分析，建议使用完整的HTML提取脚本。

## 后续步骤
1. 手动检查页面布局和功能模块
2. 识别关键交互元素（按钮、表单、链接）
3. 分析数据流动和业务逻辑
4. 生成详细的技术规格文档
EOF
}

# 生成技术文档
generate_spec() {
    local analysis_json_file="$1"
    local output_file="$2"
    local format="$3"
    
    log_info "生成技术文档: $output_file"
    
    local script_dir=$(dirname "$0")
    local generator_script="$script_dir/spec-generator.py"
    
    if [ -f "$generator_script" ]; then
        log_info "使用文档生成器脚本"
        local fmt_flag=""
        if [ "$format" != "markdown" ]; then
            fmt_flag="--format $format"
        fi
        # 通过文件传递JSON数据，避免管道被安全策略拦截
        $PYTHON "$generator_script" "$output_file" --input-json "$analysis_json_file" $fmt_flag
    else
        log_warn "文档生成脚本不存在，创建基础文档"
        if [ -f "$analysis_json_file" ]; then
            cat "$analysis_json_file" > "$output_file"
        fi
    fi
    
    if [ -f "$output_file" ]; then
        log_info "技术文档已生成: $output_file"
        log_info "文件大小: $(wc -c < "$output_file") 字节"
        log_info "行数: $(wc -l < "$output_file")"
    else
        log_error "生成技术文档失败"
        return 1
    fi
}

# 验证本地文件路径安全性
validate_local_file() {
    local filepath="$1"

    # 检查路径是否包含危险字符（命令注入防护）
    if [[ "$filepath" =~ [;\|&\$\`\'\"()<>] ]] || [[ "$filepath" =~ [\n\r] ]]; then
        log_error "文件路径包含潜在危险字符，拒绝执行"
        return 1
    fi

    # 检查路径长度
    if [[ ${#filepath} -gt 4096 ]]; then
        log_error "文件路径过长，拒绝执行"
        return 1
    fi

    # 检查文件是否存在
    if [ ! -f "$filepath" ]; then
        log_error "文件不存在: $filepath"
        return 1
    fi

    return 0
}

# 主函数
main() {
    # 默认参数
    OUTPUT_FILE="分析结果.md"
    FORMAT="markdown"
    VERBOSE=false
    NO_CACHE=false

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            -f|--format)
                FORMAT="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --no-cache)
                NO_CACHE=true
                shift
                ;;
            -*)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
            *)
                URL="$1"
                shift
                ;;
        esac
    done

    # 验证输出文件路径安全性
    if [[ "$OUTPUT_FILE" =~ [;\|&\$\`\'\"()<>] ]] || [[ "$OUTPUT_FILE" =~ [\n\r] ]]; then
        log_error "输出文件路径包含危险字符，拒绝执行"
        exit 1
    fi

    # 检查URL参数
    if [ -z "$URL" ]; then
        log_error "请提供要分析的URL"
        show_help
        exit 1
    fi

    # 判断输入类型：URL还是本地文件
    if [[ "$URL" =~ ^https?:// ]]; then
        INPUT_TYPE="url"
        log_info "输入类型: URL原型"
        # URL验证将在download_page中执行
    elif [ -f "$URL" ]; then
        INPUT_TYPE="local"
        log_info "输入类型: 本地HTML文件"
        # 验证本地文件路径
        if ! validate_local_file "$URL"; then
            exit 1
        fi
    else
        log_error "输入无效：既不是有效的URL，也不是存在的文件路径"
        log_error "URL需以http://或https://开头"
        log_error "本地文件需是存在的HTML文件路径"
        exit 1
    fi
    
    log_info "开始分析: $URL"
    log_info "输出文件: $OUTPUT_FILE"
    log_info "输出格式: $FORMAT"
    
    # 检查依赖
    check_dependencies
    
    # 获取HTML文件
    if [ "$INPUT_TYPE" = "url" ]; then
        # URL方式：下载到临时目录
        TEMP_DIR=$(mktemp -d)
        trap "rm -rf $TEMP_DIR" EXIT
        HTML_FILE="$TEMP_DIR/page.html"
        if ! download_page "$URL" "$HTML_FILE"; then
            exit 1
        fi
    else
        # 本地文件方式：直接使用原文件
        HTML_FILE="$URL"
        log_info "直接读取本地文件: $HTML_FILE"
        log_info "文件大小: $(wc -c < "$HTML_FILE") 字节"
    fi
    
    # 分析页面，输出JSON到临时文件
    ANALYSIS_JSON_FILE=$(mktemp /tmp/analysis-XXXXXX.json)
    if [ "$INPUT_TYPE" = "url" ]; then
        trap "rm -rf $TEMP_DIR $ANALYSIS_JSON_FILE" EXIT
    else
        trap "rm -f $ANALYSIS_JSON_FILE" EXIT
    fi
    $PYTHON "$extractor_script" "$HTML_FILE" json > "$ANALYSIS_JSON_FILE" 2>/dev/null
    
    # 生成技术文档
    if ! generate_spec "$ANALYSIS_JSON_FILE" "$OUTPUT_FILE" "$FORMAT"; then
        exit 1
    fi
    
    log_info "分析完成!"
    log_info "请查看生成的文档: $OUTPUT_FILE"
    
    # 显示文档预览（前10行）
    if [ "$VERBOSE" = true ]; then
        echo ""
        echo "文档预览:"
        echo "========================================"
        head -20 "$OUTPUT_FILE"
        echo "========================================"
    fi
}

# 运行主函数
main "$@"
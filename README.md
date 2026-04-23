# bie-zheng-luan-prototype (别整乱原型分析技能)

将产品原型转换为详细技术规范的技能，支持4种输入类型：URL原型、本地HTML文件、图片原型、XMind文件。

## 🎯 功能特性

### ✅ 支持的输入类型
1. **URL原型** - Figma、墨刀、Axure、蓝湖等设计工具的公开/内网链接
2. **本地HTML文件** - 导出的HTML原型文件、本地保存的网页原型
3. **图片原型** - 设计稿截图、高保真原型图（PNG/JPG/WebP等）
4. **XMind文件** - 产品功能脑图、信息架构图

### ✅ 核心能力
- **智能解析**：自动识别输入类型并选择相应解析方式
- **功能拆解**：将原型元素拆解为前端组件、后端接口、数据库设计
- **技术文档生成**：输出完整的技术规范文档
- **多格式支持**：HTML、图片、思维导图全面覆盖

## 📦 安装

### 通过OpenClaw安装
```bash
openclaw skills install https://clawhub.ai/skills/bie-zheng-luan-prototype
```

### 手动安装
```bash
# 克隆仓库
git clone https://github.com/[your-username]/bie-zheng-luan-prototype.git

# 复制到技能目录
cp -r bie-zheng-luan-prototype ~/.openclaw/workspace/skills/
```

## 🚀 使用方法

### 基本调用
当用户提供原型时，直接使用本技能：

```bash
# 分析URL原型
分析这个Figma原型：https://www.figma.com/file/xxx

# 分析本地HTML文件
分析这个HTML原型文件：/path/to/prototype.html

# 分析图片原型
分析这张设计稿截图：/path/to/design.png

# 分析XMind文件
分析这个产品脑图：/path/to/product.xmind
```

### 输入类型自动识别
技能会根据输入内容自动判断解析方式：

| 输入内容 | 识别方式 | 解析方式 |
|---------|---------|---------|
| `https://...` 或 `http://...` | 以http/https开头 | URL原型解析 |
| `/path/to/file.html` | 文件路径，以.html结尾 | 本地HTML文件解析 |
| `<!DOCTYPE html>...` | 以HTML标签开头 | 直接解析粘贴的HTML内容 |
| `/path/to/file.png/.jpg/.jpeg/.gif/.webp/.bmp` | 图片格式文件路径 | 图片原型解析 |
| `/path/to/file.xmind` | .xmind后缀文件路径 | XMind文件解析 |

## 📋 输出文档

技能会生成包含以下内容的技术规范文档：

### 1. 系统概览
- 原型来源和类型
- 分析时间和版本
- 总体功能描述
- 技术栈建议

### 2. 页面结构分析
- 布局分解（头部、侧边栏、主内容区、底部）
- 功能模块清单
- 交互元素识别

### 3. 前端实现方案
- 页面路由规划
- 组件清单（名称、props、状态、交互逻辑）
- 样式方案（CSS框架、设计系统）
- 交互细节

### 4. 后端实现方案
- API接口设计（路由、HTTP方法、参数、返回值）
- 业务逻辑伪代码
- 数据库表设计
- 第三方服务集成

### 5. 开发注意事项
- 技术栈建议
- 特殊依赖说明
- 性能和安全考虑
- 测试要点

## 🔧 内置工具

### 脚本文件
- `scripts/url-prototype-analyzer.sh` - URL原型解析主脚本
- `scripts/html-extractor.py` - HTML内容提取工具
- `scripts/spec-generator.py` - 技术文档生成工具
- `scripts/image-prototype-analyzer.py` - 图片原型分析工具
- `scripts/xmind-analyzer.py` - XMind文件分析工具
- `scripts/run_analysis.sh` - 综合分析入口脚本

### 参考模板
- `references/template-spec.md` - 技术规范文档模板
- `references/component-catalog.md` - 前端组件目录
- `references/api-design.md` - API设计规范

### 示例输出
- `assets/sample-output/sample-user-management.md` - 用户管理系统示例

## 📊 技术架构

### 解析流程
```
输入识别 → 内容解析 → 功能拆解 → 文档生成 → 输出保存
```

### 依赖要求
- **Python 3.8+**
- **Python包（核心）**：
  - `beautifulsoup4` (HTML解析)
  - `Pillow` (图片处理)
- **Python包（可选，用于增强功能）**：
  - `anthropic` (Claude Vision API，用于图片原型精确分析) — 需设置 `ANTHROPIC_API_KEY`
  - `opencv-python` (高级图像处理)

### 文件结构
```
bie-zheng-luan-prototype/
├── SKILL.md                    # 技能主文件
├── README.md                   # 说明文档
├── LICENSE                     # MIT许可证
├── skill.json                  # 技能元数据
├── scripts/                    # 分析脚本
│   ├── url-prototype-analyzer.sh
│   ├── html-extractor.py
│   ├── spec-generator.py
│   ├── image-prototype-analyzer.py
│   ├── xmind-analyzer.py
│   └── run_analysis.sh
├── references/                 # 参考模板
│   ├── template-spec.md
│   ├── component-catalog.md
│   └── api-design.md
├── assets/                     # 资源文件
│   └── sample-output/
│       └── sample-user-management.md
└── requirements.txt            # Python依赖
```

## 🎨 示例场景

### 示例1：用户管理系统原型
**输入**：Figma用户管理后台URL

**输出包含**：
- 前端：用户列表组件、用户表单组件、权限选择组件
- 后端：用户CRUD接口、权限验证接口、搜索接口
- 数据库：users表、roles表、user_roles关联表

### 示例2：电商商品页面原型  
**输入**：墨刀电商商品详情页URL

**输出包含**：
- 前端：商品展示组件、购物车组件、评价组件
- 后端：商品查询接口、购物车接口、下单接口
- 数据库：products表、categories表、orders表

## ⚠️ 安全注意事项

> 🔴 **使用前必读**：本技能涉及网络访问和可选的外部API调用，请理解以下风险：

### 网络访问与SSRF风险
- 支持**内网URL分析**，可访问内部原型链接
- ⚠️ 请勿提供不应被访问的内部系统URL，可能存在SSRF风险
- 建议：仅提供明确需要分析的原型链接

### 外部API数据传输
- 图片"视觉增强分析"需要 `ANTHROPIC_API_KEY`
- ⚠️ 启用此功能会将图片数据发送到Anthropic服务器
- 建议：敏感设计稿仅使用本地基础分析（不设置API密钥）

### 本地文件访问
- 技能会读取您指定的本地文件路径
- ⚠️ 确保路径指向预期文件，避免误读敏感内容

### 首次使用建议
- 检查 `scripts/` 目录下的脚本内容
- 在虚拟环境中安装依赖：`python -m venv .venv && source .venv/bin/activate`
- 在隔离环境中首次测试

## 🔄 版本历史

### v2.1.0 (2026-04-23)
- ✅ 增加安全警告声明（SSRF、数据泄露风险）
- ✅ 在skill.json中声明可选环境变量 `ANTHROPIC_API_KEY`
- ✅ 增加外部服务数据传输警告
- ✅ 提供首次使用安全建议

### v2.0.0 (2026-04-22)
- ✅ 新增本地HTML文件解析支持
- ✅ 新增图片原型分析功能
- ✅ 新增XMind文件解析功能
- ✅ 修复spec-generator.py中的bug
- ✅ 完善技能文档和示例

### v1.0.0 (2026-04-21)
- ✅ 初始版本：URL原型分析功能
- ✅ 基础HTML解析和文档生成

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

## 📞 支持

- 问题反馈：[GitHub Issues](https://github.com/[your-username]/bie-zheng-luan-prototype/issues)
- 功能建议：[GitHub Discussions](https://github.com/[your-username]/bie-zheng-luan-prototype/discussions)

---

*让产品原型不再"别整乱"，一键生成技术规范！*
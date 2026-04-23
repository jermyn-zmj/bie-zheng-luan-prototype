#!/usr/bin/env python3
"""
HTML页面结构提取器
用于分析原型工具的HTML页面，提取布局、组件、交互元素等信息
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import html

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("错误: 需要安装BeautifulSoup4")
    print("请运行: pip install beautifulsoup4 lxml html5lib")
    sys.exit(1)

@dataclass
class PageElement:
    """页面元素"""
    tag_name: str
    attributes: Dict[str, str]
    text: str
    xpath: str
    classes: List[str]
    children: List['PageElement']
    
    def to_dict(self):
        return {
            'tag': self.tag_name,
            'attributes': self.attributes,
            'text': self.text.strip() if self.text else '',
            'xpath': self.xpath,
            'classes': self.classes,
            'children_count': len(self.children)
        }

@dataclass
class PageStructure:
    """页面结构分析结果"""
    url: str
    title: str
    meta_description: str
    meta_keywords: str
    language: str
    viewport: str
    layout_elements: List[Dict[str, Any]]
    interactive_elements: List[Dict[str, Any]]
    forms: List[Dict[str, Any]]
    navigation: List[Dict[str, Any]]
    statistics: Dict[str, int]
    identified_components: List[Dict[str, Any]]

class HTMLExtractor:
    """HTML提取器"""
    
    def __init__(self, html_content: str, url: str = ""):
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.url = url
        self.xpath_counter = 0
        
    def extract_structure(self) -> PageStructure:
        """提取页面结构"""
        
        # 基础信息
        title = self.soup.title.string if self.soup.title else ""
        
        meta_description = ""
        meta_keywords = ""
        language = "zh-CN"
        viewport = "width=device-width, initial-scale=1.0"
        
        for meta in self.soup.find_all('meta'):
            if meta.get('name') == 'description':
                meta_description = meta.get('content', '')
            elif meta.get('name') == 'keywords':
                meta_keywords = meta.get('content', '')
            elif meta.get('name') == 'viewport':
                viewport = meta.get('content', '')
        
        html_tag = self.soup.find('html')
        if html_tag and html_tag.get('lang'):
            language = html_tag.get('lang')
        
        # 识别布局元素
        layout_elements = self._extract_layout_elements()
        
        # 识别交互元素
        interactive_elements = self._extract_interactive_elements()
        
        # 识别表单
        forms = self._extract_forms()
        
        # 识别导航
        navigation = self._extract_navigation()
        
        # 统计信息
        statistics = self._calculate_statistics()
        
        # 识别组件
        identified_components = self._identify_components()
        
        return PageStructure(
            url=self.url,
            title=title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            language=language,
            viewport=viewport,
            layout_elements=layout_elements,
            interactive_elements=interactive_elements,
            forms=forms,
            navigation=navigation,
            statistics=statistics,
            identified_components=identified_components
        )
    
    def _extract_layout_elements(self) -> List[Dict[str, Any]]:
        """提取布局元素"""
        layout_elements = []
        
        # 常见的布局容器
        layout_selectors = [
            'header', 'footer', 'nav', 'aside', 'main', 'section',
            'article', 'div.layout', 'div.container', 'div.wrapper',
            'div.header', 'div.footer', 'div.sidebar', 'div.content'
        ]
        
        for selector in layout_selectors:
            elements = self.soup.select(selector)
            for elem in elements[:10]:  # 限制数量
                classes = elem.get('class', [])
                if isinstance(classes, str):
                    classes = [classes]
                
                layout_elements.append({
                    'selector': selector,
                    'tag': elem.name,
                    'id': elem.get('id', ''),
                    'classes': classes,
                    'text_preview': elem.get_text(strip=True)[:100],
                    'child_count': len(elem.find_all())
                })
        
        return layout_elements
    
    def _extract_interactive_elements(self) -> List[Dict[str, Any]]:
        """提取交互元素"""
        interactive_elements = []
        
        # 按钮
        buttons = self.soup.find_all(['button', 'a.button', 'input[type="button"]', 
                                     'input[type="submit"]', 'div.button', 'span.button'])
        for btn in buttons[:50]:  # 限制数量
            btn_type = btn.get('type', 'button') if btn.name == 'input' else 'button'
            btn_text = btn.get_text(strip=True) or btn.get('value', '') or btn.get('aria-label', '')
            
            interactive_elements.append({
                'type': 'button',
                'element_type': btn.name,
                'text': btn_text,
                'id': btn.get('id', ''),
                'classes': btn.get('class', []),
                'onclick': btn.get('onclick', ''),
                'href': btn.get('href', '') if btn.name == 'a' else '',
                'role': btn.get('role', '')
            })
        
        # 链接
        links = self.soup.find_all('a')
        for link in links[:50]:  # 限制数量
            if link.get('href') and not link.get('href', '').startswith('#'):
                interactive_elements.append({
                    'type': 'link',
                    'text': link.get_text(strip=True),
                    'href': link.get('href', ''),
                    'title': link.get('title', ''),
                    'target': link.get('target', ''),
                    'id': link.get('id', ''),
                    'classes': link.get('class', [])
                })
        
        return interactive_elements
    
    def _extract_forms(self) -> List[Dict[str, Any]]:
        """提取表单"""
        forms = []
        
        for form in self.soup.find_all('form'):
            form_data = {
                'id': form.get('id', ''),
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'classes': form.get('class', []),
                'fields': []
            }
            
            # 提取表单字段
            inputs = form.find_all(['input', 'textarea', 'select'])
            for inp in inputs:
                field_type = inp.get('type', 'text') if inp.name == 'input' else inp.name
                
                field_data = {
                    'name': inp.get('name', ''),
                    'type': field_type,
                    'placeholder': inp.get('placeholder', ''),
                    'label': self._find_label_for_input(inp),
                    'required': inp.get('required') is not None,
                    'id': inp.get('id', ''),
                    'classes': inp.get('class', [])
                }
                
                form_data['fields'].append(field_data)
            
            forms.append(form_data)
        
        return forms
    
    def _find_label_for_input(self, input_element) -> str:
        """查找输入框对应的标签"""
        input_id = input_element.get('id')
        if input_id:
            label = self.soup.find('label', {'for': input_id})
            if label:
                return label.get_text(strip=True)
        
        # 查找父级中的label
        parent_label = input_element.find_parent('label')
        if parent_label:
            return parent_label.get_text(strip=True)
        
        return ""
    
    def _extract_navigation(self) -> List[Dict[str, Any]]:
        """提取导航菜单"""
        navigation = []
        
        # 查找导航元素
        nav_elements = self.soup.find_all(['nav', 'ul.nav', 'div.nav', 'div.menu'])
        
        for nav in nav_elements[:10]:  # 限制数量
            nav_data = {
                'type': nav.name,
                'id': nav.get('id', ''),
                'classes': nav.get('class', []),
                'items': []
            }
            
            # 提取导航项
            nav_items = nav.find_all(['a', 'li'])
            for item in nav_items[:20]:  # 限制数量
                if item.name == 'a':
                    nav_data['items'].append({
                        'type': 'link',
                        'text': item.get_text(strip=True),
                        'href': item.get('href', ''),
                        'target': item.get('target', '')
                    })
                elif item.name == 'li':
                    link = item.find('a')
                    if link:
                        nav_data['items'].append({
                            'type': 'link',
                            'text': link.get_text(strip=True),
                            'href': link.get('href', ''),
                            'target': link.get('target', '')
                        })
                    else:
                        nav_data['items'].append({
                            'type': 'text',
                            'text': item.get_text(strip=True)
                        })
            
            navigation.append(nav_data)
        
        return navigation
    
    def _calculate_statistics(self) -> Dict[str, int]:
        """计算页面统计信息"""
        stats = {
            'total_elements': len(self.soup.find_all()),
            'div_count': len(self.soup.find_all('div')),
            'span_count': len(self.soup.find_all('span')),
            'section_count': len(self.soup.find_all('section')),
            'header_count': len(self.soup.find_all('header')),
            'footer_count': len(self.soup.find_all('footer')),
            'nav_count': len(self.soup.find_all('nav')),
            'main_count': len(self.soup.find_all('main')),
            'aside_count': len(self.soup.find_all('aside')),
            'article_count': len(self.soup.find_all('article')),
            'h1_count': len(self.soup.find_all('h1')),
            'h2_count': len(self.soup.find_all('h2')),
            'h3_count': len(self.soup.find_all('h3')),
            'p_count': len(self.soup.find_all('p')),
            'a_count': len(self.soup.find_all('a')),
            'button_count': len(self.soup.find_all('button')),
            'input_count': len(self.soup.find_all('input')),
            'form_count': len(self.soup.find_all('form')),
            'img_count': len(self.soup.find_all('img')),
            'table_count': len(self.soup.find_all('table')),
            'ul_count': len(self.soup.find_all('ul')),
            'ol_count': len(self.soup.find_all('ol')),
            'li_count': len(self.soup.find_all('li')),
        }
        
        return stats
    
    def _identify_components(self) -> List[Dict[str, Any]]:
        """识别常见UI组件"""
        components = []
        
        # 基于类名识别组件
        component_patterns = {
            'card': ['card', 'panel', 'box'],
            'modal': ['modal', 'dialog', 'popup'],
            'dropdown': ['dropdown', 'select', 'menu'],
            'accordion': ['accordion', 'collapse'],
            'tab': ['tab', 'tabs'],
            'carousel': ['carousel', 'slider'],
            'breadcrumb': ['breadcrumb', 'breadcrumbs'],
            'pagination': ['pagination', 'pager'],
            'alert': ['alert', 'message', 'notification'],
            'badge': ['badge', 'tag', 'label'],
            'progress': ['progress', 'progress-bar'],
            'tooltip': ['tooltip'],
            'avatar': ['avatar'],
            'rating': ['rating', 'star'],
            'calendar': ['calendar', 'datepicker'],
            'chart': ['chart', 'graph'],
            'datatable': ['datatable', 'table'],
            'search': ['search', 'search-bar'],
            'sidebar': ['sidebar', 'side-nav'],
            'navbar': ['navbar', 'nav-bar'],
            'footer': ['footer'],
            'header': ['header'],
        }
        
        all_elements = self.soup.find_all(True)  # 所有元素
        
        for elem in all_elements[:200]:  # 限制数量
            classes = elem.get('class', [])
            if isinstance(classes, str):
                classes = [classes]
            
            for comp_type, patterns in component_patterns.items():
                for pattern in patterns:
                    # 检查类名是否包含组件模式
                    for cls in classes:
                        if pattern in cls.lower():
                            components.append({
                                'type': comp_type,
                                'element': elem.name,
                                'id': elem.get('id', ''),
                                'classes': classes,
                                'text_preview': elem.get_text(strip=True)[:50]
                            })
                            break
                    if components and components[-1]['type'] == comp_type:
                        break
        
        # 去重
        unique_components = []
        seen = set()
        for comp in components:
            comp_key = f"{comp['type']}:{comp['id']}:{','.join(comp['classes'])}"
            if comp_key not in seen:
                seen.add(comp_key)
                unique_components.append(comp)
        
        return unique_components
    
    def to_markdown(self, structure: PageStructure) -> str:
        """转换为Markdown格式"""
        md_lines = []
        
        md_lines.append(f"# 页面分析报告")
        md_lines.append(f"")
        md_lines.append(f"**URL**: {structure.url}")
        md_lines.append(f"**分析时间**: {self._get_current_time()}")
        md_lines.append(f"")
        
        md_lines.append(f"## 页面基本信息")
        md_lines.append(f"- **标题**: {structure.title}")
        md_lines.append(f"- **描述**: {structure.meta_description}")
        md_lines.append(f"- **语言**: {structure.language}")
        md_lines.append(f"- **视口**: {structure.viewport}")
        md_lines.append(f"")
        
        md_lines.append(f"## 页面统计")
        for key, value in structure.statistics.items():
            md_lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
        md_lines.append(f"")
        
        if structure.layout_elements:
            md_lines.append(f"## 布局元素")
            for layout in structure.layout_elements[:10]:  # 限制数量
                md_lines.append(f"### {layout['selector']}")
                md_lines.append(f"- 标签: {layout['tag']}")
                if layout['id']:
                    md_lines.append(f"- ID: {layout['id']}")
                if layout['classes']:
                    md_lines.append(f"- 类名: {', '.join(layout['classes'])}")
                if layout['text_preview']:
                    md_lines.append(f"- 文本预览: {layout['text_preview']}")
                md_lines.append(f"- 子元素数量: {layout['child_count']}")
                md_lines.append(f"")
        
        if structure.interactive_elements:
            md_lines.append(f"## 交互元素")
            
            # 按类型分组
            by_type = {}
            for elem in structure.interactive_elements:
                elem_type = elem['type']
                if elem_type not in by_type:
                    by_type[elem_type] = []
                by_type[elem_type].append(elem)
            
            for elem_type, elements in by_type.items():
                md_lines.append(f"### {elem_type.title()} ({len(elements)}个)")
                for elem in elements[:10]:  # 限制数量
                    if elem['text']:
                        md_lines.append(f"- {elem['text']}")
                        if elem.get('href'):
                            md_lines.append(f"  链接: {elem['href']}")
                    md_lines.append(f"")
        
        if structure.forms:
            md_lines.append(f"## 表单 ({len(structure.forms)}个)")
            for form in structure.forms[:5]:  # 限制数量
                md_lines.append(f"### 表单")
                if form['id']:
                    md_lines.append(f"- ID: {form['id']}")
                if form['action']:
                    md_lines.append(f"- 提交地址: {form['action']}")
                md_lines.append(f"- 提交方法: {form['method'].upper()}")
                
                if form['fields']:
                    md_lines.append(f"- 字段 ({len(form['fields'])}个):")
                    for field in form['fields']:
                        req = " (必填)" if field['required'] else ""
                        label = f"标签: {field['label']}, " if field['label'] else ""
                        md_lines.append(f"  - {field['type']}: {field['name']}{req}")
                        if field['placeholder']:
                            md_lines.append(f"    占位符: {field['placeholder']}")
                md_lines.append(f"")
        
        if structure.navigation:
            md_lines.append(f"## 导航菜单 ({len(structure.navigation)}个)")
            for nav in structure.navigation[:3]:  # 限制数量
                md_lines.append(f"### {nav['type'].title()}导航")
                for item in nav['items'][:10]:  # 限制数量
                    if item['type'] == 'link':
                        md_lines.append(f"- [{item['text']}]({item['href']})")
                    else:
                        md_lines.append(f"- {item['text']}")
                md_lines.append(f"")
        
        if structure.identified_components:
            md_lines.append(f"## 识别出的UI组件")
            by_type = {}
            for comp in structure.identified_components:
                comp_type = comp['type']
                if comp_type not in by_type:
                    by_type[comp_type] = []
                by_type[comp_type].append(comp)
            
            for comp_type, components in by_type.items():
                md_lines.append(f"### {comp_type.title()} ({len(components)}个)")
                for comp in components[:5]:  # 限制数量
                    md_lines.append(f"- {comp['element']}元素")
                    if comp['id']:
                        md_lines.append(f"  ID: {comp['id']}")
                    if comp['classes']:
                        md_lines.append(f"  类名: {', '.join(comp['classes'])}")
                    if comp['text_preview']:
                        md_lines.append(f"  文本: {comp['text_preview']}")
                md_lines.append(f"")
        
        md_lines.append(f"## 分析建议")
        md_lines.append(f"1. **布局分析**: 基于识别出的布局元素，规划页面结构")
        md_lines.append(f"2. **组件识别**: 根据UI组件类型，设计可复用组件")
        md_lines.append(f"3. **交互设计**: 基于按钮和表单，设计用户交互流程")
        md_lines.append(f"4. **导航设计**: 根据菜单结构，设计页面路由")
        md_lines.append(f"5. **数据流设计**: 基于表单字段，设计API接口和数据库")
        md_lines.append(f"")
        
        md_lines.append(f"---")
        md_lines.append(f"*生成工具: bie-zheng-luan-prototype技能*")
        md_lines.append(f"*注意: 此分析基于HTML结构，实际功能可能需进一步确认*")
        
        return "\n".join(md_lines)
    
    def to_json(self, structure: PageStructure) -> str:
        """转换为JSON格式"""
        return json.dumps(asdict(structure), ensure_ascii=False, indent=2)
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    if len(sys.argv) < 2:
        print("用法: python html-extractor.py <html文件> [输出格式: markdown|json]")
        print("示例: python html-extractor.py page.html markdown")
        sys.exit(1)
    
    html_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    
    if not Path(html_file).exists():
        print(f"错误: HTML文件不存在: {html_file}")
        sys.exit(1)
    
    # 读取HTML内容
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"读取文件失败: {e}")
        sys.exit(1)
    
    # 创建提取器
    extractor = HTMLExtractor(html_content, f"file://{html_file}")
    
    # 提取结构
    try:
        structure = extractor.extract_structure()
    except Exception as e:
        print(f"分析HTML失败: {e}")
        sys.exit(1)
    
    # 输出结果
    if output_format.lower() == "json":
        result = extractor.to_json(structure)
    else:
        result = extractor.to_markdown(structure)
    
    print(result)

if __name__ == "__main__":
    main()
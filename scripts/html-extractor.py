#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML页面结构提取器（通用版 v3.0.0）
用于分析各种原型工具的HTML页面，自动适配多种UI框架，深度提取菜单、筛选条件、表格列、按钮等信息
支持自动识别UI框架类型，动态调整解析策略
"""

import sys
import json
import re
import io
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

# 设置标准输出编码为UTF-8（解决Windows终端编码问题）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("错误: 需要安装BeautifulSoup4")
    print("请运行: pip install beautifulsoup4 lxml html5lib")
    sys.exit(1)


# ============ UI框架适配配置 ============
# 支持多种UI框架的类名映射，自动识别并适配

UI_FRAMEWORK_CONFIGS = {
    # 企业后台系统风格（通用配置）
    'enterprise_backend': {
        'sidebar': {
            'container': ['aside.sider', 'div.sidebar'],
            'nav': ['nav.sider__nav', 'nav'],
            'group': ['div.sider__group'],
            'group_label': ['div.sider__group-label'],
            'item': ['a.sider__item', 'div.nav-item'],
            'item_text': ['span.sider__item-text'],
            'item_icon': ['span.sider__item-icon'],
            'user_container': ['div.sider__user'],
            'avatar': ['div.sider__avatar'],
            'user_name': ['div.sider__user-name'],
            'user_role': ['div.sider__user-role'],
            'toggle_btn': ['button.sider__toggle-btn'],
            'page_id_attr': 'data-scm-page',
        },
        'filter': {
            'container': ['span.pr-filter-item', 'div.filter-item', 'div.search-field'],
            'label': ['span.pr-filter-item__label', 'label'],
            'select': ['select.pr-select', 'select'],
            'input': ['input'],
        },
        'stat_card': {
            'container': ['div.stat-card'],
            'title': ['div.stat-card__title'],
            'value': ['div.stat-card__num'],
            'subtitle': ['div.stat-card__sub'],
            'icon': ['div.stat-card__icon'],
            'color_classes': {
                'blue': ['stat-card--blue', 'blue'],
                'orange': ['stat-card--orange', 'orange'],
                'purple': ['stat-card--purple', 'purple'],
                'red': ['stat-card--red', 'red'],
                'yellow': ['stat-card--yellow', 'yellow'],
                'pink': ['stat-card--pink', 'pink'],
                'green': ['stat-card--green', 'green'],
            },
        },
        'page_view': {
            'container': ['div.view', 'div.page-view', 'div.main-wrap', 'div[data-view]', 'div[data-page]'],
        },
        'modal': {
            'container': ['div.drawer-panel', 'div.modal-overlay'],
            'header': ['div.drawer-panel__header', 'div.modal-header'],
            'title': ['span[id*="title"]', 'h2'],
            'anchor_bar': ['div.drawer-anchor-bar'],
            'anchor_link': ['a.drawer-anchor-link'],
            'body': ['div.drawer-panel__body', 'div.modal-body'],
            'footer': ['div.drawer-panel__footer', 'div.modal-footer'],
            'form_item': ['div.drawer-info-item'],
            'form_label': ['span.drawer-info-label'],
            'form_select': ['select.drawer-info-select'],
            'form_input': ['input.drawer-info-input'],
            'form_textarea': ['textarea.drawer-info-textarea'],
        },
        'status_tab': {
            'container': ['div.pr-status-group'],
            'chip': ['span.pr-status-chip'],
        },
    },

    # 通用后台系统风格（标准配置）
    'standard_backend': {
        'sidebar': {
            'container': ['aside.sidebar', 'div.sidebar'],
            'nav': ['nav'],
            'group': ['div.nav-section'],
            'group_label': ['div.nav-label'],
            'item': ['div.nav-item'],
            'item_text': ['span'],
            'item_badge': ['span.badge'],
            'toggle_btn': [],
            'user_container': [],
            'page_id_attr': 'data-view',
        },
        'filter': {
            'container': ['div.filters', 'div.plan-filter-bar', 'div.plan-filter-fields'],
            'item': ['label.plan-filter-field', 'span.plan-filter-field', 'div.warning-time-filter'],
            'label': ['span.plan-filter-label'],
            'select': ['select'],
            'input': ['input.plan-filter-inp', 'input[type="text"]', 'input[type="search"]', 'input[type="date"]'],
            'search_container': ['div.search-wrap'],
        },
        'stat_card': {
            'container': ['div.wb-overview', 'div.plan-stats', 'div.ship-stat-cards', 'div.stat-card'],
            'title': ['span', 'div.stat-title', 'div.stat-label'],
            'value': ['strong', 'span.stat-value', 'div.stat-num'],
            'subtitle': ['small', 'div.stat-sub'],
            'icon': [],
            'color_classes': {
                'blue': ['blue', 'primary'],
                'orange': ['orange', 'warning'],
                'red': ['red', 'danger'],
                'green': ['green', 'success'],
            },
        },
        'page_view': {
            'container': ['div.view', 'div[data-view]', 'div.plan-body', 'div.ship-body'],
            'id_prefix': 'view',
        },
        'modal': {
            'container': ['div.modal-overlay'],
            'header': ['div.modal-header'],
            'title': ['h2'],
            'body': ['div.modal-body'],
            'footer': ['div.modal-footer'],
            'close_btn': ['button.btn-close'],
        },
        'status_tab': {
            'container': ['div.plan-stats'],
            'chip': ['span'],
        },
    },

    # 通用移动端H5风格
    'mobile_h5': {
        'sidebar': {
            'container': [],
            'nav': ['nav.navbar', 'div.navbar'],
            'item': ['a.nav-item', 'button.nav-item'],
            'item_text': ['span'],
        },
        'filter': {
            'container': ['div.search-bar', 'div.filter-bar'],
            'label': ['span', 'label'],
            'select': ['select'],
            'input': ['input'],
        },
        'stat_card': {
            'container': ['div.card', 'div.stat-card'],
            'title': ['div.card-title', 'div.stat-title'],
            'value': ['div.card-value', 'span.stat-value'],
            'subtitle': ['div.card-subtitle'],
            'icon': [],
            'color_classes': {
                'blue': ['card-blue', 'primary'],
                'orange': ['card-orange', 'warning'],
                'red': ['card-red', 'danger'],
                'green': ['card-green', 'success'],
            },
        },
        'page_view': {
            'container': ['div.page-body', 'div.content', 'div[data-page]'],
        },
        'modal': {
            'container': ['div.modal', 'div.popup'],
            'header': ['div.modal-header', 'div.header'],
            'body': ['div.modal-body', 'div.body'],
            'footer': ['div.modal-footer', 'div.footer'],
        },
    },
}


class UIFrameworkDetector:
    """UI框架自动检测器"""

    def __init__(self, soup):
        self.soup = soup
        self.detected_framework = None

    def detect_framework(self) -> str:
        """自动检测HTML使用的UI框架类型"""
        html_str = str(self.soup)

        # 检测企业后台系统特征
        if 'sider__nav' in html_str or 'sider__item' in html_str or 'pr-filter-item' in html_str:
            return 'enterprise_backend'

        # 检测通用后台系统特征
        if 'nav-item' in html_str and 'data-view' in html_str:
            if 'plan-filter-field' in html_str or 'warning-toolbar' in html_str or 'wb-overview' in html_str:
                return 'standard_backend'

        # 检测移动端H5特征
        if 'navbar' in html_str and 'viewport' in html_str:
            return 'mobile_h5'

        # 默认使用企业后台配置
        return 'enterprise_backend'

    def get_config(self, framework: str = None) -> Dict:
        """获取指定框架的配置"""
        if framework is None:
            framework = self.detect_framework()
        return UI_FRAMEWORK_CONFIGS.get(framework, UI_FRAMEWORK_CONFIGS['enterprise_backend'])


def find_by_patterns(container, patterns: List[str], find_all: bool = False):
    """根据多个CSS选择器模式查找元素"""
    results = []
    for pattern in patterns:
        if not pattern:
            continue
        try:
            if find_all:
                found = container.select(pattern)
                results.extend(found)
            else:
                found = container.select_one(pattern)
                if found:
                    return found
        except:
            pass
    return results if find_all else None


# ============ 数据结构定义 ============

@dataclass
class MenuItem:
    """菜单项"""
    group: str               # 分组名（如"系统管理"）
    name: str                # 菜单名（如"用户列表"）
    icon: str                # SVG图标精确描述
    icon_svg: str            # SVG原始代码（用于前端还原）
    page_id: str             # 页面标识（data-scm-page）
    href: str                # 链接地址
    is_active: bool          # 是否当前激活


@dataclass
class UserInfo:
    """用户信息"""
    avatar_text: str         # 头像文字（如"文"）
    name: str                # 用户姓名（如"文俊"）
    role: str                # 用户角色（如"管理员"）


@dataclass
class SidebarInfo:
    """侧边栏信息"""
    has_toggle: bool         # 是否有折叠按钮
    toggle_button_id: str    # 折叠按钮ID
    user_info: UserInfo      # 用户信息


@dataclass
class PageTab:
    """页面标签"""
    name: str                # 标签名称
    is_active: bool          # 是否当前激活
    has_close: bool          # 是否有关闭按钮


@dataclass
class SubPill:
    """子标签（工作台切换）"""
    name: str                # 标签名称
    pill_id: str             # 标签ID
    is_active: bool          # 是否当前激活
    target_panel: str        # 目标面板ID


@dataclass
class FilterField:
    """筛选字段"""
    name: str                # 字段名（如"款式分类"）
    type: str                # 类型：select/input/text/date
    options: List[str]       # 下拉选项（如["全部", "裤袜", "运动"]）
    placeholder: str         # 占位符（input类型）
    filter_id: str           # 筛选器ID（如"pr-filter-1")
    default_value: str       # 默认值


@dataclass
class TableColumn:
    """表格列"""
    name: str                # 列名（如"单号"）
    data_type: str           # 数据类型推断：text/link/number/badge/progress/date/image/currency/percentage
    sortable: bool           # 是否可排序
    table_index: int         # 所属表格索引（用于区分多个表格）
    is_detail: bool          # 是否是明细子表列


@dataclass
class ActionButton:
    """操作按钮"""
    name: str                # 按钮名（如"搜索"/"智能拆单"）
    category: str            # 分类：search/action/export/edit/delete/create/confirm/view/reset/other
    style: str               # 样式：primary/default/danger/warning
    button_id: str           # 按钮ID
    icon: str                # 按钮图标描述（如果有）
    location: str            # 按钮位置：toolbar/filter/table/modal


@dataclass
class StatCard:
    """统计卡片"""
    title: str               # 卡片标题（如"待处理事项"）
    value: str               # 数值
    subtitle: str            # 子标题/说明
    color_type: str          # 颜色类型：blue/orange/purple/red/yellow/pink
    icon_svg: str            # SVG图标代码


@dataclass
class MessageCard:
    """消息通知卡片"""
    dot_visible: bool        # 是否有未读标记点
    headline: str            # 标题（如"【延期风险】链条斜挎 V02 第三版打样仍不通过"）
    content: str             # 正文内容
    time: str                # 时间（如"10:32"）
    participants: int        # 参与人数
    comments: int            # 评论数
    action_button: str       # 操作按钮（如"已阅读确认"）
    action_button_style: str # 按钮样式


@dataclass
class BuyerCard:
    """用户工作进度卡片"""
    avatar: str              # 头像（可能是图片或文字）
    name: str                # 姓名（如"梓鸣"）
    tag: str                 # 标签（如"能力偏弱"）
    tag_color: str           # 标签颜色
    stats: Dict[str, str]    # 统计数据（如{"待审核": "12个", "进行中": "12个"}）
    overdue_count: int       # 已逾期数量
    action_buttons: List[str] # 操作按钮列表


@dataclass
class StatusTab:
    """状态筛选Tab"""
    name: str                # 状态名称（如"未确认"）
    count: int               # 数量
    color_type: str          # 颜色类型：default/orange/green/red/pink
    is_active: bool          # 是否当前激活
    filter_key: str          # 筛选键（data-paa-status-filter等）


@dataclass
class ProgressItem:
    """进度条组件"""
    status_dot_color: str    # 状态点颜色（blue/orange/green/red）
    name: str                # 名称（如"回力双肩包提"）
    detail: str              # 详情（如"待下单 5000件 · 已到货0件"）
    status_label: str        # 状态标签（如"待下单"）
    status_label_color: str  # 状态标签颜色
    date: str                # 日期（如"预计 2026/04/02"）


@dataclass
class DrawerAnchorLink:
    """弹窗锚点导航链接"""
    name: str                # 锚点名称（如"基本信息"）
    anchor_key: str          # 锚点键（data-anchor）
    is_active: bool          # 是否当前激活


@dataclass
class DrawerFormField:
    """弹窗内表单字段"""
    name: str                # 字段名（如"默认仓库"）
    type: str                # 类型：select/input/textarea
    is_required: bool        # 是否必填
    options: List[str]       # 下拉选项（select类型）
    placeholder: str         # 占位符（input/textarea类型）
    field_id: str            # 字段ID
    is_full_width: bool      # 是否占整行


@dataclass
class DrawerStatistics:
    """弹窗内统计信息"""
    name: str                # 统计项名称（如"事项"）
    value: str               # 数值
    color_type: str          # 颜色类型


@dataclass
class DrawerPanel:
    """弹窗/抽屉面板"""
    panel_id: str            # 弹窗ID（如"drawer-por-detail"）
    title: str               # 弹窗标题（如"详情查看"）
    title_icon: str          # 标题图标描述
    status_badge_id: str     # 状态badge元素ID
    no_element_id: str       # 单号元素ID
    anchor_links: List[DrawerAnchorLink]  # 锚点导航
    form_fields: List[DrawerFormField]    # 表单字段
    statistics: List[DrawerStatistics]    # 统计信息
    inner_buttons: List[ActionButton]     # 弹窗内按钮
    has_search_box: bool     # 是否有搜索框
    search_placeholder: str  # 搜索框占位符
    has_timeline: bool       # 是否有操作日志时间线


@dataclass
class TableInfo:
    """表格信息"""
    table_index: int         # 表格索引
    table_class: str         # 表格class
    is_main_table: bool      # 是否主表
    columns: List[TableColumn]  # 列信息
    has_checkbox: bool       # 是否有勾选列


@dataclass
class PageView:
    """页面视图"""
    view_id: str             # 页面视图ID（如"view-user-list"）
    name: str                # 页面名称推断
    filters: List[FilterField] = field(default_factory=list)
    tables: List[TableInfo] = field(default_factory=list)
    buttons: List[ActionButton] = field(default_factory=list)
    stat_cards: List[StatCard] = field(default_factory=list)
    message_cards: List[MessageCard] = field(default_factory=list)
    buyer_cards: List[BuyerCard] = field(default_factory=list)
    sub_pills: List[SubPill] = field(default_factory=list)
    status_tabs: List[StatusTab] = field(default_factory=list)  # 新增：状态筛选Tab
    progress_items: List[ProgressItem] = field(default_factory=list)  # 新增：进度条组件
    drawer_panels: List[DrawerPanel] = field(default_factory=list)  # 新增：弹窗面板


@dataclass
class PrototypeAnalysis:
    """原型分析结果"""
    system_name: str         # 系统名称
    title: str               # 页面标题
    menus: List[MenuItem]    # 菜单结构
    sidebar: SidebarInfo     # 侧边栏信息（新增）
    page_tabs: List[PageTab] # 页面标签栏（新增）
    page_views: List[PageView]  # 页面视图列表
    total_filters: int       # 总筛选字段数
    total_columns: int       # 总表格列数
    total_buttons: int       # 总按钮数
    analysis_time: str       # 分析时间


# ============ 解析器类 ============

class EnhancedHTMLExtractor:
    """通用HTML提取器 v3.0.0 - 支持多种UI框架自动适配"""

    def __init__(self, html_content: str, url: str = ""):
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.url = url
        # 自动检测UI框架类型
        self.detector = UIFrameworkDetector(self.soup)
        self.framework = self.detector.detect_framework()
        self.config = self.detector.get_config(self.framework)

    def extract_full_structure(self) -> PrototypeAnalysis:

        # 1. 系统名称
        title = self.soup.title.string if self.soup.title else ""
        system_name = self._extract_system_name(title)

        # 2. 菜单结构
        menus = self._extract_sidebar_menu()

        # 3. 侧边栏信息（新增）
        sidebar = self._extract_sidebar_info()

        # 4. 页面标签栏（新增）
        page_tabs = self._extract_page_tabs()

        # 5. 页面视图
        page_views = self._extract_all_page_views()

        # 6. 统计
        total_filters = sum(len(pv.filters) for pv in page_views)
        total_columns = sum(sum(len(t.columns) for t in pv.tables) for pv in page_views)
        total_buttons = sum(len(pv.buttons) for pv in page_views)

        return PrototypeAnalysis(
            system_name=system_name,
            title=title,
            menus=menus,
            sidebar=sidebar,
            page_tabs=page_tabs,
            page_views=page_views,
            total_filters=total_filters,
            total_columns=total_columns,
            total_buttons=total_buttons,
            analysis_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def _extract_system_name(self, title: str) -> str:
        """从标题提取系统名称"""
        if ' - ' in title:
            return title.split(' - ')[0]
        return title

    def _extract_sidebar_menu(self) -> List[MenuItem]:
        """提取侧边栏菜单结构（通用版 - 支持多种UI框架）"""
        menus = []
        sidebar_config = self.config.get('sidebar', {})

        # 根据配置查找侧边栏容器
        container_patterns = sidebar_config.get('container', ['aside.sider', 'div.sidebar', 'aside.sidebar'])
        nav_patterns = sidebar_config.get('nav', ['nav.sider__nav', 'nav'])
        group_patterns = sidebar_config.get('group', ['div.sider__group', 'div.nav-section'])
        group_label_patterns = sidebar_config.get('group_label', ['div.sider__group-label', 'div.nav-label'])
        item_patterns = sidebar_config.get('item', ['a.sider__item', 'div.nav-item'])
        item_text_patterns = sidebar_config.get('item_text', ['span.sider__item-text', 'span'])
        item_icon_patterns = sidebar_config.get('item_icon', ['span.sider__item-icon'])
        page_id_attr = sidebar_config.get('page_id_attr', 'data-scm-page')

        # 查找侧边栏容器
        sidebar_container = find_by_patterns(self.soup, container_patterns)
        if not sidebar_container:
            return menus

        # 查找导航区域
        nav_area = find_by_patterns(sidebar_container, nav_patterns) if sidebar_container else None
        if not nav_area:
            nav_area = sidebar_container

        # 查找菜单分组
        groups = find_by_patterns(nav_area, group_patterns, find_all=True)
        if not groups:
            # 如果没有分组，直接查找菜单项
            items = find_by_patterns(nav_area, item_patterns, find_all=True)
            if items:
                for item in items:
                    self._add_menu_item(menus, item, "默认菜单", item_text_patterns, item_icon_patterns, page_id_attr)
            return menus

        # 遍历分组提取菜单项
        for group in groups:
            # 获取分组名称
            group_label = find_by_patterns(group, group_label_patterns)
            group_name = group_label.get_text(strip=True) if group_label else "未分组"

            # 获取菜单项
            items = find_by_patterns(group, item_patterns, find_all=True)
            for item in items:
                self._add_menu_item(menus, item, group_name, item_text_patterns, item_icon_patterns, page_id_attr)

        return menus

    def _add_menu_item(self, menus, item, group_name, text_patterns, icon_patterns, page_id_attr):
        """添加菜单项到列表"""
        # 获取菜单文本
        item_text = find_by_patterns(item, text_patterns)
        menu_name = item_text.get_text(strip=True) if item_text else ""
        if not menu_name:
            # 尝试直接获取item的文本（排除子元素）
            menu_name = item.get_text(strip=True)

        if not menu_name:
            return

        # 提取SVG图标代码
        icon_desc = ""
        icon_svg = ""
        if icon_patterns:
            item_icon = find_by_patterns(item, icon_patterns)
            if item_icon:
                svg = item_icon.find('svg')
                if svg:
                    icon_svg = str(svg)
                    icon_desc = self._infer_icon_from_svg(svg)

        # 获取页面标识
        page_id = item.get(page_id_attr, '') or item.get('data-view', '') or item.get('href', '')
        href = item.get('href', '')
        is_active = 'is-active' in item.get('class', []) or 'active' in item.get('class', [])

        menus.append(MenuItem(
            group=group_name,
            name=menu_name,
            icon=icon_desc,
            icon_svg=icon_svg,
            page_id=page_id,
            href=href,
            is_active=is_active
        ))

    def _extract_sidebar_info(self) -> SidebarInfo:
        """提取侧边栏信息（使用可配置模式）"""
        has_toggle = False
        toggle_button_id = ""
        user_info = UserInfo(avatar_text="", name="", role="")

        sidebar_config = self.config.get('sidebar', {})
        container_patterns = sidebar_config.get('container', ['aside.sider', 'div.sidebar'])

        sider = find_by_patterns(self.soup, container_patterns)

        if sider:
            # 折叠按钮
            toggle_patterns = sidebar_config.get('toggle_btn', ['button.sider__toggle-btn', 'button.sidebar-toggle'])
            toggle_btn = find_by_patterns(sider, toggle_patterns)
            if toggle_btn:
                has_toggle = True
                toggle_button_id = toggle_btn.get('id', 'sider-toggle-btn')

            # 用户信息
            user_patterns = sidebar_config.get('user_container', ['div.sider__user', 'div.user-info'])
            user_elem = find_by_patterns(sider, user_patterns)
            if user_elem:
                avatar_patterns = sidebar_config.get('avatar', ['div.sider__avatar', 'div.avatar'])
                avatar = find_by_patterns(user_elem, avatar_patterns)
                avatar_text = avatar.get_text(strip=True) if avatar else ""

                name_patterns = sidebar_config.get('user_name', ['div.sider__user-name', 'div.user-name'])
                name_elem = find_by_patterns(user_elem, name_patterns)
                name = name_elem.get_text(strip=True) if name_elem else ""

                role_patterns = sidebar_config.get('user_role', ['div.sider__user-role', 'div.user-role'])
                role_elem = find_by_patterns(user_elem, role_patterns)
                role = role_elem.get_text(strip=True) if role_elem else ""

                user_info = UserInfo(avatar_text=avatar_text, name=name, role=role)

        return SidebarInfo(has_toggle=has_toggle, toggle_button_id=toggle_button_id, user_info=user_info)

    def _extract_page_tabs(self) -> List[PageTab]:
        """提取页面标签栏（新增）"""
        tabs = []

        tabs_bar = self.soup.find('div', class_='page-tabs-bar')
        if not tabs_bar:
            return tabs

        page_tabs_container = tabs_bar.find('div', class_='page-tabs')
        if not page_tabs_container:
            return tabs

        tab_elems = page_tabs_container.find_all('div', class_='page-tab')
        for tab in tab_elems:
            tab_name = tab.get_text(strip=True)
            # 移除关闭按钮的SVG内容
            close_svg = tab.find('svg', class_='page-tab__close')
            if close_svg:
                close_svg_text = close_svg.get_text(strip=True)
                tab_name = tab_name.replace(close_svg_text, '').strip()

            is_active = 'page-tab--active' in tab.get('class', [])
            has_close = close_svg is not None

            tabs.append(PageTab(name=tab_name, is_active=is_active, has_close=has_close))

        return tabs

    def _infer_icon_from_svg(self, svg) -> str:
        """从SVG精确推断图标类型（优化版）"""
        svg_str = str(svg)

        # 更精确的图标识别
        icon_patterns = {
            '工作台图标': ['rect x="3" y="3"', 'width="7" height="9"', 'rect x="14" y="3"'],
            '收件箱图标': ['M22 12h-6', 'M9 12h6', 'inbox'],
            '文档图标': ['M9 12h6m-6 4h6', 'M7 2h5.586', 'document'],
            '编辑图标': ['M11 5H6a2 2 0 00-2 2v11', 'M11.828 15H9', 'edit'],
            '功能图标': ['rect x="3" y="4" width="18" height="16"', 'M7 8h10'],
            '日历图标': ['rect x="3" y="4" width="18" height="18"', 'M16 2v4M8 2v4', 'calendar'],
            '银行卡图标': ['rect x="2" y="5" width="20" height="14"', 'M2 10h20', 'payment'],
            '下载图标': ['M4 16v2a2 2 0 002 2h12', 'M8 12l4 4 4-4m-4-4v8', 'download', 'upload'],
            '验证图标': ['M9 12l2 2 4-4m6 2a9 9 0 11-18 0', 'check', 'verify'],
            '警告图标': ['circle cx="12" cy="12" r="10"', 'M12 8v4M12 16h.01', 'warning'],
            '时钟图标': ['circle cx="12" cy="12" r="10"', 'M12 6v6l4 2', 'clock', 'time'],
            '禁止图标': ['circle cx="12" cy="12" r="10"', 'M4.5 4.5l15 15', 'forbidden', 'ban'],
            '消息图标': ['M21 15a4 4 0 01-4 4H7', 'M21 11.5a8.38', 'message'],
            '用户图标': ['M17 21v-2a4 4 0 00-4-4H5', 'circle cx="9" cy="7" r="4"', 'user', 'avatar'],
            '搜索图标': ['circle cx="11" cy="11" r="8"', 'M21 21l-4.35-4.35', 'search'],
            '设置图标': ['circle cx="12" cy="12" r="3"', 'gear', 'settings'],
            '文件夹图标': ['M22 19a2 2 0 01-2 2H4a2', 'folder'],
        }

        for icon_name, patterns in icon_patterns.items():
            for pattern in patterns:
                if pattern in svg_str:
                    return icon_name

        # 检查SVG标题或aria-label
        aria_label = svg.get('aria-label', '')
        if aria_label:
            return f"{aria_label}图标"

        return "功能图标"

    def _extract_all_page_views(self) -> List[PageView]:
        """提取所有页面视图（使用可配置模式）"""
        page_views = []

        view_config = self.config.get('page_view', {})
        view_patterns = view_config.get('container', ['div.view', 'div.page-view', 'div.main-wrap', 'div[data-view]', 'div[data-page]'])

        view_containers = find_by_patterns(self.soup, view_patterns, find_all=True)

        # 如果没有通过配置找到，尝试通过属性查找
        if not view_containers:
            data_view_elements = self.soup.find_all(attrs={'data-view': True})
            view_containers.extend(data_view_elements)
            data_page_elements = self.soup.find_all(attrs={'data-page': True})
            view_containers.extend(data_page_elements)

        # 过滤无效的视图容器（如 nav-item）
        invalid_view_patterns = ['nav-item', 'nav-', 'menu-', 'sidebar', 'sider']

        for container in view_containers:
            view_id = container.get('id', '')
            if not view_id:
                classes = container.get('class', [])
                if isinstance(classes, list) and classes:
                    view_id = classes[0]

            # 过滤无效的视图ID
            if not view_id or any(pattern in view_id for pattern in invalid_view_patterns):
                continue

            # 检查容器是否包含实际内容（表格、表单、按钮等）
            has_content = container.find('table') or container.find('button') or container.find('form') or container.find('input')
            if not has_content and not container.find('div', class_=lambda x: x and ('stat' in x or 'card' in x or 'overview' in x) if x else False):
                continue

            view_name = self._infer_page_name(view_id, container)

            # 提取子标签（如工作台的不同视图切换）
            sub_pills = self._extract_sub_pills(container)

            # 提取筛选条件
            filters = self._extract_filter_fields(container)

            # 提取表格信息（优化版，区分主表和明细表）
            tables = self._extract_tables(container)

            # 提取按钮（优化版，增加位置信息）
            buttons = self._extract_buttons(container)

            # 提取统计卡片
            stat_cards = self._extract_stat_cards(container)

            # 提取消息通知卡片（新增）
            message_cards = self._extract_message_cards(container)

            # 提取用户工作进度卡片（新增）
            buyer_cards = self._extract_buyer_cards(container)

            # 提取状态筛选Tab（新增）
            status_tabs = self._extract_status_tabs(container)

            # 提取进度条组件（新增）
            progress_items = self._extract_progress_items(container)

            # 提取弹窗面板（新增）
            drawer_panels = self._extract_drawer_panels(container)

            page_views.append(PageView(
                view_id=view_id,
                name=view_name,
                filters=filters,
                tables=tables,
                buttons=buttons,
                stat_cards=stat_cards,
                message_cards=message_cards,
                buyer_cards=buyer_cards,
                sub_pills=sub_pills,
                status_tabs=status_tabs,
                progress_items=progress_items,
                drawer_panels=drawer_panels
            ))

        # 如果没有找到明确的视图容器
        if not page_views:
            tables = self.soup.find_all('table')
            if tables:
                filters = self._extract_filter_fields(self.soup)
                tables_info = self._extract_tables(self.soup)
                buttons = self._extract_buttons(self.soup)
                stat_cards = self._extract_stat_cards(self.soup)
                message_cards = self._extract_message_cards(self.soup)
                buyer_cards = self._extract_buyer_cards(self.soup)
                status_tabs = self._extract_status_tabs(self.soup)
                progress_items = self._extract_progress_items(self.soup)
                drawer_panels = self._extract_drawer_panels(self.soup)

                page_views.append(PageView(
                    view_id='main-content',
                    name='主页面',
                    filters=filters,
                    tables=tables_info,
                    buttons=buttons,
                    stat_cards=stat_cards,
                    message_cards=message_cards,
                    buyer_cards=buyer_cards,
                    sub_pills=[],
                    status_tabs=status_tabs,
                    progress_items=progress_items,
                    drawer_panels=drawer_panels
                ))

        return page_views

    def _extract_sub_pills(self, container) -> List[SubPill]:
        """提取子标签（新增）"""
        pills = []

        sub_pills_container = container.find('div', class_='sub-pills')
        if sub_pills_container:
            pill_elems = sub_pills_container.find_all('button', class_='sub-pill')
            for pill in pill_elems:
                pill_name = pill.get_text(strip=True)
                pill_id = pill.get('id', '')
                is_active = 'sub-pill--active' in pill.get('class', [])
                target_panel = pill.get('data-workbench', '')

                pills.append(SubPill(
                    name=pill_name,
                    pill_id=pill_id,
                    is_active=is_active,
                    target_panel=target_panel
                ))

        return pills

    def _infer_page_name(self, view_id: str, container) -> str:
        """推断页面名称（通用方法）"""
        # 优先从页面内容中获取标题
        title_elem = container.find(['h1', 'h2', 'h3'])
        if title_elem:
            return title_elem.get_text(strip=True)

        # 从页面标题标签获取
        page_title = container.find('title')
        if page_title:
            return page_title.get_text(strip=True)

        # 从data属性获取
        if container.get('data-title'):
            return container.get('data-title')
        if container.get('aria-label'):
            return container.get('aria-label')

        # 根据view_id推断通用名称
        if view_id:
            # 移除常见前缀，生成可读名称
            clean_id = view_id.replace('view-', '').replace('-view', '').replace('page-', '')
            # 将分隔符转为空格并首字母大写
            words = clean_id.replace('-', ' ').replace('_', ' ').split()
            if words:
                return ' '.join(word.capitalize() for word in words)
            return view_id

        return '未命名页面'

    def _extract_filter_fields(self, container) -> List[FilterField]:
        """提取筛选条件（使用可配置模式）"""
        filters = []

        filter_config = self.config.get('filter', {})
        item_patterns = filter_config.get('item', ['span.pr-filter-item', 'div.filter-item', 'div.search-field'])
        label_patterns = filter_config.get('label', ['span.pr-filter-item__label', 'label'])

        filter_items = find_by_patterns(container, item_patterns, find_all=True)

        for item in filter_items:
            label_elem = find_by_patterns(item, label_patterns)
            field_name = label_elem.get_text(strip=True) if label_elem else ""

            if not field_name:
                continue

            filter_id = item.get('data-filter-id', '') or item.get('id', '')

            select_elem = item.find('select')
            input_elem = item.find('input')

            if select_elem:
                options = []
                default_value = ""
                for opt in select_elem.find_all('option'):
                    opt_text = opt.get_text(strip=True)
                    if opt_text:
                        options.append(opt_text)
                    if opt.get('selected'):
                        default_value = opt_text

                filters.append(FilterField(
                    name=field_name,
                    type='select',
                    options=options,
                    placeholder='',
                    filter_id=filter_id,
                    default_value=default_value
                ))

            elif input_elem:
                input_type = input_elem.get('type', 'text')
                placeholder = input_elem.get('placeholder', '')
                default_value = input_elem.get('value', '')

                filters.append(FilterField(
                    name=field_name,
                    type=input_type,
                    options=[],
                    placeholder=placeholder,
                    filter_id=filter_id,
                    default_value=default_value
                ))

            else:
                filters.append(FilterField(
                    name=field_name,
                    type='unknown',
                    options=[],
                    placeholder='',
                    filter_id=filter_id,
                    default_value=''
                ))

        return filters

    def _extract_tables(self, container) -> List[TableInfo]:
        """提取表格信息（优化版，区分主表和明细表）"""
        tables_info = []

        tables = container.find_all('table')
        for idx, table in enumerate(tables):
            table_class = ' '.join(table.get('class', []))

            # 判断是否主表（通常第一个表格是主表，或有特定class）
            is_main_table = idx == 0
            if 'detail' in table_class.lower() or 'sub' in table_class.lower():
                is_main_table = False
            if 'main' in table_class.lower():
                is_main_table = True

            # 提取列信息
            columns = []
            has_checkbox = False

            thead = table.find('thead')
            tbody = table.find('tbody')

            if thead:
                header_cells = thead.find_all('th')
                col_names = []
                for th in header_cells:
                    col_name = th.get_text(strip=True)
                    col_names.append(col_name)

                # 检查是否有checkbox列
                if col_names and col_names[0] in ['', '全选', '选择', '□']:
                    has_checkbox = True

                # 推断数据类型
                col_types = []
                if tbody:
                    first_data_row = tbody.find('tr')
                    if first_data_row:
                        data_cells = first_data_row.find_all('td')
                        for i, td in enumerate(data_cells):
                            col_types.append(self._infer_cell_type(td, col_names[i] if i < len(col_names) else ''))
                    else:
                        col_types = ['text'] * len(col_names)
                else:
                    col_types = ['text'] * len(col_names)

                for i, col_name in enumerate(col_names):
                    if col_name in ['', '全选', '选择', '□']:
                        continue

                    data_type = col_types[i] if i < len(col_types) else 'text'
                    columns.append(TableColumn(
                        name=col_name,
                        data_type=data_type,
                        sortable=False,
                        table_index=idx,
                        is_detail=not is_main_table
                    ))

            tables_info.append(TableInfo(
                table_index=idx,
                table_class=table_class,
                is_main_table=is_main_table,
                columns=columns,
                has_checkbox=has_checkbox
            ))

        return tables_info

    def _infer_cell_type(self, cell, col_name: str = '') -> str:
        """从单元格内容和列名推断数据类型（优化版）"""
        # 先基于列名推断（更准确）
        col_name_lower = col_name.lower()
        if any(kw in col_name_lower for kw in ['单号', '编号', '编码', '账号']):
            return 'link'
        if any(kw in col_name_lower for kw in ['日期', '时间', '创建时间', '审核时间']):
            return 'date'
        if any(kw in col_name_lower for kw in ['数量', '金额', '单价', '总价', '合计']):
            return 'number'
        if any(kw in col_name_lower for kw in ['价格', '金额', '单价']) and '¥' in cell.get_text():
            return 'currency'
        if any(kw in col_name_lower for kw in ['税率', '百分比', '占比', '不合格率']):
            return 'percentage'
        if any(kw in col_name_lower for kw in ['状态', '进度', '审核状态', '确认状态']):
            return 'badge'
        if any(kw in col_name_lower for kw in ['图片', '照片', '缩略图', '头像']):
            return 'image'

        # 基于class推断
        cell_classes = cell.get('class', [])
        if isinstance(cell_classes, str):
            cell_classes = [cell_classes]

        if any('num' in str(cls).lower() for cls in cell_classes):
            return 'number'
        if any('thumb' in str(cls).lower() or 'img' in str(cls).lower() for cls in cell_classes):
            return 'image'
        if any('badge' in str(cls).lower() or 'tag' in str(cls).lower() for cls in cell_classes):
            return 'badge'

        # 基于内容推断
        cell_text = cell.get_text(strip=True)

        if not cell_text or cell_text in ['—', '-', '']:
            return 'empty'

        # 日期格式
        if re.match(r'\d{4}-\d{2}-\d{2}', cell_text) or re.match(r'\d{2}:\d{2}', cell_text):
            return 'date'

        # 数字格式
        if re.match(r'^[\d,.\-¥￥%]+$', cell_text) and cell_text:
            if '%' in cell_text:
                return 'percentage'
            if '¥' in cell_text or '￥' in cell_text:
                return 'currency'
            if re.match(r'^\d+[,.]?\d*$', cell_text):
                return 'number'

        # 链接元素
        link = cell.find('a') or cell.find('span', class_='pr-num-link')
        if link:
            return 'link'

        # 图片元素
        img = cell.find('img')
        if img:
            return 'image'

        # Badge/标签
        badge = cell.find('span', class_=lambda x: x and ('badge' in x or 'tag' in x) if x else False)
        if badge:
            return 'badge'

        # 进度条
        progress = cell.find('div', class_=lambda x: x and 'progress' in x if x else False)
        if progress:
            return 'progress'

        return 'text'

    def _extract_buttons(self, container) -> List[ActionButton]:
        """提取按钮（优化版，增加位置信息）"""
        buttons = []

        button_elements = container.find_all('button')
        for btn in button_elements:
            btn_text = btn.get_text(strip=True)
            if not btn_text:
                btn_text = btn.get('aria-label', '')
            if not btn_text:
                btn_text = btn.get('title', '')

            if not btn_text:
                continue

            btn_id = btn.get('id', '')

            # 推断按钮位置
            location = 'unknown'
            parent = btn.parent
            if parent:
                parent_class = ' '.join(parent.get('class', []))
                if 'toolbar' in parent_class.lower():
                    location = 'toolbar'
                elif 'filter' in parent_class.lower():
                    location = 'filter'
                elif 'msg-card' in parent_class.lower():
                    location = 'message'
                elif 'buyer-card' in parent_class.lower():
                    location = 'buyer'
                elif 'stat-card' in parent_class.lower():
                    location = 'stat'
                elif 'modal' in parent_class.lower() or 'drawer' in parent_class.lower():
                    location = 'modal'

            category = self._infer_button_category(btn_text, btn)

            btn_classes = btn.get('class', [])
            if isinstance(btn_classes, str):
                btn_classes = [btn_classes]

            style = 'default'
            if 'primary' in btn_classes or 'btn-primary' in btn_classes:
                style = 'primary'
            elif 'danger' in btn_classes:
                style = 'danger'
            elif 'warning' in btn_classes:
                style = 'warning'

            # 提取按钮图标
            icon = ""
            svg = btn.find('svg')
            if svg:
                icon = self._infer_icon_from_svg(svg)

            buttons.append(ActionButton(
                name=btn_text,
                category=category,
                style=style,
                button_id=btn_id,
                icon=icon,
                location=location
            ))

        return buttons

    def _infer_button_category(self, text: str, btn) -> str:
        """推断按钮分类"""
        text_lower = text.lower()

        if any(kw in text_lower for kw in ['搜索', '查询', '筛选', '查找', '检索']):
            return 'search'
        if any(kw in text_lower for kw in ['导出', '下载', '下载单据']):
            return 'export'
        if any(kw in text_lower for kw in ['编辑', '修改', '更新', '修改交期']):
            return 'edit'
        if any(kw in text_lower for kw in ['删除', '移除', '作废', '取消作废']):
            return 'delete'
        if any(kw in text_lower for kw in ['新增', '添加', '创建', '新建', '添加行']):
            return 'create'
        if any(kw in text_lower for kw in ['确认', '提交', '审核', '批准', '反审核', '提交审核', '取消确认']):
            return 'confirm'
        if any(kw in text_lower for kw in ['重置', '清空']):
            return 'reset'
        if any(kw in text_lower for kw in ['拆单', '智能拆单', '退回', '处理', '分配', '下推', '推送', '刷新', '打印', '预约', '申请付款']):
            return 'action'
        if any(kw in text_lower for kw in ['查看', '详情', '日志', '记录', '查看详情', '查看照片', '查看质检']):
            return 'view'

        return 'other'

    def _extract_stat_cards(self, container) -> List[StatCard]:
        """提取统计卡片（使用可配置模式）"""
        cards = []

        stat_config = self.config.get('stat_card', {})
        card_patterns = stat_config.get('container', ['div.stat-card', 'div.wb-overview', 'div.stat-item'])
        title_patterns = stat_config.get('title', ['div.stat-card__title', 'div.stat-title', 'span.stat-label'])
        value_patterns = stat_config.get('value', ['div.stat-card__num', 'div.stat-num', 'span.stat-value'])
        sub_patterns = stat_config.get('subtitle', ['div.stat-card__sub', 'div.stat-sub'])
        icon_patterns = stat_config.get('icon', ['div.stat-card__icon', 'div.stat-icon'])

        stat_cards = find_by_patterns(container, card_patterns, find_all=True)

        for card in stat_cards:
            title_elem = find_by_patterns(card, title_patterns)
            title = title_elem.get_text(strip=True) if title_elem else ""

            value_elem = find_by_patterns(card, value_patterns)
            value = value_elem.get_text(strip=True) if value_elem else ""

            sub_elem = find_by_patterns(card, sub_patterns)
            subtitle = sub_elem.get_text(strip=True) if sub_elem else ""

            # 如果使用wb-overview结构，需要特殊处理
            if 'wb-overview' in card.get('class', []):
                # wb-overview通常有多个子元素
                spans = card.find_all('span')
                if len(spans) >= 2:
                    title = spans[0].get_text(strip=True) if spans[0] else ""
                    value = spans[1].get_text(strip=True) if spans[1] else ""

            if not title:
                continue

            # 提取SVG图标代码（新增）
            icon_elem = find_by_patterns(card, icon_patterns)
            icon_svg = ""
            if icon_elem:
                svg = icon_elem.find('svg')
                if svg:
                    icon_svg = str(svg)

            card_classes = card.get('class', [])
            if isinstance(card_classes, str):
                card_classes = [card_classes]

            color_type = 'default'
            color_patterns = stat_config.get('color_classes', {})
            for cls in card_classes:
                for color_name, color_patterns_list in color_patterns.items():
                    if any(pattern in cls for pattern in color_patterns_list):
                        color_type = color_name
                        break

            cards.append(StatCard(
                title=title,
                value=value,
                subtitle=subtitle,
                color_type=color_type,
                icon_svg=icon_svg
            ))

        return cards

    def _extract_message_cards(self, container) -> List[MessageCard]:
        """提取消息通知卡片（新增）"""
        cards = []

        msg_cards = container.find_all('div', class_='msg-card')
        for card in msg_cards:
            # 未读标记点
            dot_elem = card.find('div', class_='msg-card__dot')
            dot_visible = dot_elem is not None

            # 标题
            headline_elem = card.find('div', class_='msg-card__headline')
            headline = headline_elem.get_text(strip=True) if headline_elem else ""

            # 正文
            body_elem = card.find('div', class_='msg-card__body')
            content = ""
            if body_elem:
                text_elem = body_elem.find('p', class_='msg-card__text')
                if text_elem:
                    content = text_elem.get_text(strip=True)

            # 元数据
            time = ""
            participants = 0
            comments = 0
            meta_elem = card.find('div', class_='msg-card__meta')
            if meta_elem:
                spans = meta_elem.find_all('span')
                for span in spans:
                    span_text = span.get_text(strip=True)
                    # 时间通常是第一个span，格式如"10:32"
                    if re.match(r'\d{1,2}:\d{2}', span_text):
                        time = span_text
                    # 参与人数和评论数
                    try:
                        num = int(span_text)
                        # 根据图标判断类型
                        icon = span.find('svg')
                        if icon:
                            icon_str = str(icon)
                            if 'circle cx="9" cy="7"' in icon_str or 'user' in icon_str.lower():
                                participants = num
                            elif 'path d="M21 15' in icon_str or 'message' in icon_str.lower():
                                comments = num
                    except:
                        pass

            # 操作按钮
            action_button = ""
            action_button_style = ""
            btn_elem = card.find('button')
            if btn_elem:
                action_button = btn_elem.get_text(strip=True)
                btn_classes = btn_elem.get('class', [])
                if 'btn-primary' in btn_classes or 'primary' in btn_classes:
                    action_button_style = 'primary'
                elif 'btn-default' in btn_classes:
                    action_button_style = 'default'

            cards.append(MessageCard(
                dot_visible=dot_visible,
                headline=headline,
                content=content,
                time=time,
                participants=participants,
                comments=comments,
                action_button=action_button,
                action_button_style=action_button_style
            ))

        return cards

    def _extract_buyer_cards(self, container) -> List[BuyerCard]:
        """提取用户工作进度卡片（新增）"""
        cards = []

        buyer_cards = container.find_all('div', class_='buyer-card')
        for card in buyer_cards:
            # 头像
            avatar_elem = card.find('div', class_='avatar')
            avatar = ""
            if avatar_elem:
                # 检查是否有图片
                img = avatar_elem.find('img')
                if img:
                    avatar = img.get('src', '')
                else:
                    avatar = avatar_elem.get_text(strip=True)

            # 姓名
            name_elem = card.find('div', class_='buyer-card__name')
            name = name_elem.get_text(strip=True) if name_elem else ""

            # 标签
            tag = ""
            tag_color = ""
            tag_elem = card.find('span', class_=lambda x: x and 'tag' in x if x else False)
            if tag_elem:
                tag = tag_elem.get_text(strip=True)
                tag_classes = tag_elem.get('class', [])
                if 'tag-blue' in tag_classes:
                    tag_color = 'blue'
                elif 'tag-orange' in tag_classes:
                    tag_color = 'orange'
                elif 'tag-green' in tag_classes:
                    tag_color = 'green'
                elif 'tag-red' in tag_classes:
                    tag_color = 'red'

            # 统计数据
            stats = {}
            overdue_count = 0
            stats_elem = card.find('div', class_='buyer-card__stats')
            if stats_elem:
                spans = stats_elem.find_all('span')
                for span in spans:
                    span_text = span.get_text(strip=True)
                    # 解析统计项，如"待审核 12个"
                    match = re.match(r'(.+?)\s+(\d+)个', span_text)
                    if match:
                        stat_name = match.group(1)
                        stat_value = match.group(2) + '个'
                        stats[stat_name] = stat_value

                        if '逾期' in stat_name:
                            overdue_count = int(match.group(2))
                    else:
                        # 检查是否有overdue标记
                        overdue_span = span.find('span', class_='overdue')
                        if overdue_span:
                            overdue_text = overdue_span.get_text(strip=True)
                            try:
                                overdue_count = int(overdue_text)
                            except:
                                pass

            # 操作按钮
            action_buttons = []
            btn_elems = card.find_all('button')
            for btn in btn_elems:
                btn_text = btn.get_text(strip=True)
                if btn_text:
                    action_buttons.append(btn_text)

            cards.append(BuyerCard(
                avatar=avatar,
                name=name,
                tag=tag,
                tag_color=tag_color,
                stats=stats,
                overdue_count=overdue_count,
                action_buttons=action_buttons
            ))

        return cards

    def _extract_status_tabs(self, container) -> List[StatusTab]:
        """提取状态筛选Tab（新增）"""
        tabs = []

        # 查找状态筛选组
        status_groups = container.find_all('div', class_='pr-status-group')
        for group in status_groups:
            chips = group.find_all('span', class_='pr-status-chip')
            for chip in chips:
                # 获取状态名称和数量
                chip_text = chip.get_text(strip=True)
                # 解析格式如"未确认 0"或"待确认 0"
                match = re.match(r'(.+?)\s+(\d+)', chip_text)
                if match:
                    name = match.group(1)
                    try:
                        count = int(match.group(2))
                    except:
                        count = 0
                else:
                    name = chip_text
                    count = 0

                # 获取颜色类型
                chip_classes = chip.get('class', [])
                color_type = 'default'
                for cls in chip_classes:
                    if 'pr-status-chip--orange' in cls:
                        color_type = 'orange'
                    elif 'pr-status-chip--green' in cls:
                        color_type = 'green'
                    elif 'pr-status-chip--red' in cls:
                        color_type = 'red'
                    elif 'pr-status-chip--pink' in cls:
                        color_type = 'pink'

                # 是否激活
                is_active = 'is-active' in chip_classes

                # 筛选键
                filter_key = chip.get('data-paa-status-filter', '') or chip.get('data-pr-status-filter', '') or chip.get('data-por-status-filter', '')

                tabs.append(StatusTab(
                    name=name,
                    count=count,
                    color_type=color_type,
                    is_active=is_active,
                    filter_key=filter_key
                ))

        return tabs

    def _extract_progress_items(self, container) -> List[ProgressItem]:
        """提取进度条组件（新增）"""
        items = []

        progress_items = container.find_all('div', class_='progress-item')
        for item in progress_items:
            # 状态点颜色
            dot_elem = item.find('span', class_='status-dot')
            dot_color = ''
            if dot_elem:
                dot_classes = dot_elem.get('class', [])
                for cls in dot_classes:
                    if 'status-dot--blue' in cls:
                        dot_color = 'blue'
                    elif 'status-dot--orange' in cls:
                        dot_color = 'orange'
                    elif 'status-dot--green' in cls:
                        dot_color = 'green'
                    elif 'status-dot--red' in cls:
                        dot_color = 'red'

            # 名称
            name_elem = item.find('div', class_='progress-item__name')
            name = name_elem.get_text(strip=True) if name_elem else ""

            # 详情
            detail_elem = item.find('div', class_='progress-item__detail')
            detail = detail_elem.get_text(strip=True) if detail_elem else ""

            # 状态标签
            status_elem = item.find('div', class_='status-pill')
            status_label = status_elem.get_text(strip=True) if status_elem else ""
            status_label_color = ''
            if status_elem:
                status_classes = status_elem.get('class', [])
                for cls in status_classes:
                    if 'status-pill--blue' in cls:
                        status_label_color = 'blue'
                    elif 'status-pill--orange' in cls:
                        status_label_color = 'orange'
                    elif 'status-pill--green' in cls:
                        status_label_color = 'green'
                    elif 'status-pill--red' in cls:
                        status_label_color = 'red'

            # 日期
            date_elem = item.find('div', class_='progress-item__date')
            date = date_elem.get_text(strip=True) if date_elem else ""

            items.append(ProgressItem(
                status_dot_color=dot_color,
                name=name,
                detail=detail,
                status_label=status_label,
                status_label_color=status_label_color,
                date=date
            ))

        return items

    def _extract_drawer_panels(self, container) -> List[DrawerPanel]:
        """提取弹窗/抽屉面板（新增）"""
        panels = []

        # 查找所有弹窗面板
        drawer_panels = container.find_all('div', class_='drawer-panel')
        for panel in drawer_panels:
            panel_id = panel.get('id', '')

            # 标题
            title_elem = panel.find('span', id=lambda x: x and 'title' in x if x else False)
            title = title_elem.get_text(strip=True) if title_elem else ""
            if not title_elem:
                # 尝试从drawer-panel__title获取
                title_container = panel.find('div', class_='drawer-panel__title')
                if title_container:
                    title = title_container.get_text(strip=True)

            # 标题图标
            title_icon = ""
            icon_elem = panel.find('div', class_='drawer-panel__title-icon')
            if icon_elem:
                svg = icon_elem.find('svg')
                if svg:
                    title_icon = self._infer_icon_from_svg(svg)

            # 状态badge元素ID
            status_badge_id = ""
            badge_elem = panel.find('span', class_='pr-badge', id=True)
            if badge_elem:
                status_badge_id = badge_elem.get('id', '')

            # 单号元素ID
            no_element_id = ""
            no_elem = panel.find('span', class_=lambda x: x and 'no' in x if x else False, id=True)
            if no_elem:
                no_element_id = no_elem.get('id', '')

            # 锚点导航
            anchor_links = []
            anchor_bar = panel.find('div', class_='drawer-anchor-bar')
            if anchor_bar:
                links = anchor_bar.find_all('a', class_='drawer-anchor-link')
                for link in links:
                    link_name = link.get_text(strip=True)
                    anchor_key = link.get('data-anchor', '')
                    is_active = 'is-active' in link.get('class', [])
                    anchor_links.append(DrawerAnchorLink(
                        name=link_name,
                        anchor_key=anchor_key,
                        is_active=is_active
                    ))

            # 表单字段
            form_fields = []
            info_items = panel.find_all('div', class_='drawer-info-item')
            for item in info_items:
                label_elem = item.find('span', class_='drawer-info-label')
                field_name = label_elem.get_text(strip=True) if label_elem else ""
                # 检查是否必填
                is_required = item.find('span', class_='req') is not None

                # 检查字段类型
                select_elem = item.find('select', class_='drawer-info-select')
                textarea_elem = item.find('textarea', class_='drawer-info-textarea')
                input_elem = item.find('input', class_='drawer-info-input')

                field_type = 'unknown'
                options = []
                placeholder = ''
                field_id = ''

                if select_elem:
                    field_type = 'select'
                    field_id = select_elem.get('id', '')
                    for opt in select_elem.find_all('option'):
                        opt_text = opt.get_text(strip=True)
                        if opt_text and opt_text != '请选择':
                            options.append(opt_text)
                elif textarea_elem:
                    field_type = 'textarea'
                    field_id = textarea_elem.get('id', '')
                    placeholder = textarea_elem.get('placeholder', '')
                elif input_elem:
                    field_type = input_elem.get('type', 'input')
                    field_id = input_elem.get('id', '')
                    placeholder = input_elem.get('placeholder', '')

                # 是否占整行
                is_full_width = 'drawer-info-item--full' in item.get('class', [])

                if field_name:
                    form_fields.append(DrawerFormField(
                        name=field_name,
                        type=field_type,
                        is_required=is_required,
                        options=options,
                        placeholder=placeholder,
                        field_id=field_id,
                        is_full_width=is_full_width
                    ))

            # 统计信息
            statistics = []
            stat_elems = panel.find_all('span', class_='por-demand-stat-inline__item')
            for stat in stat_elems:
                stat_text = stat.get_text(strip=True)
                match = re.match(r'(.+?)(\d+)', stat_text)
                if match:
                    stat_name = match.group(1)
                    stat_value = match.group(2)
                    # 颜色类型
                    stat_classes = stat.get('class', [])
                    color_type = 'default'
                    for cls in stat_classes:
                        if 'por-demand-stat-inline__item--total' in cls:
                            color_type = 'total'
                        elif 'por-demand-stat-inline__item--split' in cls:
                            color_type = 'split'
                        elif 'por-demand-stat-inline__item--unsplit' in cls:
                            color_type = 'unsplit'
                    statistics.append(DrawerStatistics(
                        name=stat_name,
                        value=stat_value,
                        color_type=color_type
                    ))

            # 弹窗内按钮
            inner_buttons = []
            footer = panel.find('div', class_='drawer-panel__footer')
            if footer:
                btns = footer.find_all('button')
                for btn in btns:
                    btn_text = btn.get_text(strip=True)
                    if btn_text:
                        btn_id = btn.get('id', '')
                        btn_classes = btn.get('class', [])
                        style = 'default'
                        if 'scm-btn--primary' in btn_classes or 'pr-btn--primary' in btn_classes:
                            style = 'primary'
                        elif 'scm-btn--danger' in btn_classes:
                            style = 'danger'
                        inner_buttons.append(ActionButton(
                            name=btn_text,
                            category=self._infer_button_category(btn_text, btn),
                            style=style,
                            button_id=btn_id,
                            icon='',
                            location='modal_footer'
                        ))
            # 工具栏按钮（添加行、批量导入等）
            toolbar_right = panel.find('div', class_='por-detail-toolbar-right')
            if toolbar_right:
                btns = toolbar_right.find_all('button')
                for btn in btns:
                    btn_text = btn.get_text(strip=True)
                    if btn_text:
                        btn_id = btn.get('id', '')
                        inner_buttons.append(ActionButton(
                            name=btn_text,
                            category=self._infer_button_category(btn_text, btn),
                            style='outline',
                            button_id=btn_id,
                            icon='',
                            location='modal_toolbar'
                        ))

            # 是否有搜索框
            has_search_box = panel.find('input', class_='por-detail-search__input') is not None
            search_placeholder = ''
            search_input = panel.find('input', class_='por-detail-search__input')
            if search_input:
                search_placeholder = search_input.get('placeholder', '')

            # 是否有操作日志时间线
            has_timeline = panel.find('div', class_='drawer-timeline') is not None

            panels.append(DrawerPanel(
                panel_id=panel_id,
                title=title,
                title_icon=title_icon,
                status_badge_id=status_badge_id,
                no_element_id=no_element_id,
                anchor_links=anchor_links,
                form_fields=form_fields,
                statistics=statistics,
                inner_buttons=inner_buttons,
                has_search_box=has_search_box,
                search_placeholder=search_placeholder,
                has_timeline=has_timeline
            ))

        return panels

    def to_markdown(self, analysis: PrototypeAnalysis) -> str:
        """转换为Markdown格式（优化版）"""
        md_lines = []

        # 标题
        md_lines.append(f"# 原型分析报告")
        md_lines.append("")
        md_lines.append(f"**分析时间**: {analysis.analysis_time}")
        md_lines.append(f"**HTML来源**: {self.url}")
        md_lines.append("")

        # 系统概览
        md_lines.append("## 系统概览")
        md_lines.append("")
        md_lines.append(f"| 属性 | 值 |")
        md_lines.append(f"|-----|-----|")
        md_lines.append(f"| 系统名称 | {analysis.system_name} |")
        md_lines.append(f"| 页面标题 | {analysis.title} |")
        md_lines.append(f"| 菜单数量 | {len(analysis.menus)} |")
        md_lines.append(f"| 页面视图数量 | {len(analysis.page_views)} |")
        md_lines.append(f"| 筛选字段总数 | {analysis.total_filters} |")
        md_lines.append(f"| 表格列总数 | {analysis.total_columns} |")
        md_lines.append(f"| 操作按钮总数 | {analysis.total_buttons} |")
        md_lines.append("")

        # 侧边栏信息（新增）
        md_lines.append("## 侧边栏信息")
        md_lines.append("")
        md_lines.append(f"| 属性 | 值 |")
        md_lines.append(f"|-----|-----|")
        md_lines.append(f"| 是否有折叠按钮 | {analysis.sidebar.has_toggle} |")
        md_lines.append(f"| 折叠按钮ID | {analysis.sidebar.toggle_button_id or '-'} |")
        md_lines.append(f"| 用户头像文字 | {analysis.sidebar.user_info.avatar_text or '-'} |")
        md_lines.append(f"| 用户姓名 | {analysis.sidebar.user_info.name or '-'} |")
        md_lines.append(f"| 用户角色 | {analysis.sidebar.user_info.role or '-'} |")
        md_lines.append("")

        # 页面标签栏（新增）
        if analysis.page_tabs:
            md_lines.append("## 页面标签栏")
            md_lines.append("")
            md_lines.append(f"| 标签名称 | 是否激活 | 是否有关闭按钮 |")
            md_lines.append(f"|---------|---------|---------------|")
            for tab in analysis.page_tabs:
                md_lines.append(f"| {tab.name} | {tab.is_active} | {tab.has_close} |")
            md_lines.append("")

        # 菜单结构
        md_lines.append("## 菜单结构")
        md_lines.append("")

        menu_groups = {}
        for menu in analysis.menus:
            if menu.group not in menu_groups:
                menu_groups[menu.group] = []
            menu_groups[menu.group].append(menu)

        for group_name, group_menus in menu_groups.items():
            md_lines.append(f"### {group_name}")
            md_lines.append("")
            md_lines.append(f"| 菜单名称 | 图标描述 | 页面标识 | 是否激活 |")
            md_lines.append(f"|---------|---------|----------|---------|")
            for menu in group_menus:
                md_lines.append(f"| {menu.name} | {menu.icon} | {menu.page_id or '-'} | {menu.is_active} |")
            md_lines.append("")

        # 页面详情
        md_lines.append("## 页面详情")
        md_lines.append("")

        for page_view in analysis.page_views:
            md_lines.append(f"### 页面：{page_view.name}")
            md_lines.append(f"- 视图ID: `{page_view.view_id}`")
            md_lines.append("")

            # 子标签（新增）
            if page_view.sub_pills:
                md_lines.append("#### 子标签切换")
                md_lines.append("")
                md_lines.append(f"| 标签名称 | 标签ID | 是否激活 | 目标面板 |")
                md_lines.append(f"|---------|--------|---------|---------|")
                for pill in page_view.sub_pills:
                    md_lines.append(f"| {pill.name} | {pill.pill_id} | {pill.is_active} | {pill.target_panel} |")
                md_lines.append("")

            # 统计卡片
            if page_view.stat_cards:
                md_lines.append("#### 统计卡片")
                md_lines.append("")
                md_lines.append(f"| 卡片标题 | 数值 | 说明 | 颜色类型 |")
                md_lines.append(f"|---------|------|------|---------|")
                for card in page_view.stat_cards:
                    md_lines.append(f"| {card.title} | {card.value} | {card.subtitle} | {card.color_type} |")
                md_lines.append("")

            # 消息通知卡片（新增）
            if page_view.message_cards:
                md_lines.append("#### 消息通知")
                md_lines.append("")
                md_lines.append(f"| 标题 | 正文 | 时间 | 参与人数 | 评论数 | 操作按钮 |")
                md_lines.append(f"|-----|------|------|---------|-------|---------|")
                for card in page_view.message_cards:
                    md_lines.append(f"| {card.headline} | {card.content[:50]}... | {card.time} | {card.participants} | {card.comments} | {card.action_button} |")
                md_lines.append("")

            # 用户工作进度卡片（新增）
            if page_view.buyer_cards:
                md_lines.append("#### 用户工作进度概览")
                md_lines.append("")
                md_lines.append(f"| 姓名 | 标签 | 统计数据 | 已逾期 | 操作按钮 |")
                md_lines.append(f"|-----|------|---------|-------|---------|")
                for card in page_view.buyer_cards:
                    stats_str = '; '.join([f"{k}: {v}" for k, v in card.stats.items()])
                    buttons_str = ', '.join(card.action_buttons)
                    md_lines.append(f"| {card.name} | {card.tag}({card.tag_color}) | {stats_str} | {card.overdue_count}个 | {buttons_str} |")
                md_lines.append("")

            # 状态筛选Tab（新增）
            if page_view.status_tabs:
                md_lines.append("#### 状态筛选Tab")
                md_lines.append("")
                md_lines.append(f"| 状态名称 | 数量 | 颜色类型 | 是否激活 | 筛选键 |")
                md_lines.append(f"|---------|------|---------|---------|--------|")
                for tab in page_view.status_tabs:
                    md_lines.append(f"| {tab.name} | {tab.count} | {tab.color_type} | {tab.is_active} | {tab.filter_key or '-'} |")
                md_lines.append("")

            # 进度条组件（新增）
            if page_view.progress_items:
                md_lines.append("#### 进度条组件")
                md_lines.append("")
                md_lines.append(f"| 名称 | 详情 | 状态标签 | 状态颜色 | 日期 |")
                md_lines.append(f"|-----|------|---------|---------|------|")
                for item in page_view.progress_items:
                    md_lines.append(f"| {item.name} | {item.detail} | {item.status_label} | {item.status_label_color} | {item.date} |")
                md_lines.append("")

            # 弹窗面板（新增）
            if page_view.drawer_panels:
                md_lines.append("#### 弹窗/抽屉面板")
                md_lines.append("")
                for panel in page_view.drawer_panels:
                    md_lines.append(f"**弹窗ID**: `{panel.panel_id}`")
                    md_lines.append("")
                    md_lines.append(f"- **标题**: {panel.title} ({panel.title_icon})")
                    md_lines.append(f"- **是否有搜索框**: {panel.has_search_box}")
                    if panel.has_search_box:
                        md_lines.append(f"- **搜索框占位符**: {panel.search_placeholder}")
                    md_lines.append(f"- **是否有操作日志时间线**: {panel.has_timeline}")
                    md_lines.append("")

                    # 锚点导航
                    if panel.anchor_links:
                        md_lines.append(f"- **锚点导航**: {', '.join([link.name for link in panel.anchor_links])}")
                        md_lines.append("")

                    # 表单字段
                    if panel.form_fields:
                        md_lines.append("**弹窗内表单字段**:")
                        md_lines.append("")
                        md_lines.append(f"| 字段名 | 类型 | 是否必填 | 选项 | 占位符 |")
                        md_lines.append(f"|-------|------|---------|------|--------|")
                        for field in panel.form_fields:
                            required_str = "✅" if field.is_required else "-"
                            options_str = ', '.join(field.options[:5]) if field.options else "-"
                            md_lines.append(f"| {field.name} | {field.type} | {required_str} | {options_str} | {field.placeholder or '-'} |")
                        md_lines.append("")

                    # 统计信息
                    if panel.statistics:
                        md_lines.append("**弹窗内统计信息**:")
                        md_lines.append("")
                        stats_str = ' | '.join([f"{s.name}{s.value}" for s in panel.statistics])
                        md_lines.append(f"| {stats_str} |")
                        md_lines.append("")

                    # 弹窗内按钮
                    if panel.inner_buttons:
                        md_lines.append("**弹窗内按钮**:")
                        md_lines.append("")
                        md_lines.append(f"| 按钮名称 | 分类 | 样式 | 位置 |")
                        md_lines.append(f"|---------|------|------|------|")
                        for btn in panel.inner_buttons:
                            md_lines.append(f"| {btn.name} | {btn.category} | {btn.style} | {btn.location} |")
                        md_lines.append("")

                    md_lines.append("---")
                    md_lines.append("")

            # 筛选条件
            if page_view.filters:
                md_lines.append("#### 筛选条件")
                md_lines.append("")
                md_lines.append(f"| 字段名 | 类型 | 选项/占位符 | 默认值 | 筛选器ID |")
                md_lines.append(f"|-------|------|------------|-------|----------|")
                for filter_field in page_view.filters:
                    if filter_field.type == 'select':
                        options_str = ', '.join(filter_field.options[:10])
                        if len(filter_field.options) > 10:
                            options_str += '...'
                        md_lines.append(f"| {filter_field.name} | select | {options_str} | {filter_field.default_value or '全部'} | {filter_field.filter_id} |")
                    elif filter_field.type in ['text', 'input']:
                        md_lines.append(f"| {filter_field.name} | {filter_field.type} | {filter_field.placeholder} | {filter_field.default_value or '-'} | {filter_field.filter_id} |")
                    else:
                        md_lines.append(f"| {filter_field.name} | {filter_field.type} | - | {filter_field.default_value or '-'} | {filter_field.filter_id} |")
                md_lines.append("")

            # 操作按钮
            if page_view.buttons:
                md_lines.append("#### 操作按钮")
                md_lines.append("")
                md_lines.append(f"| 按钮名称 | 分类 | 样式 | 位置 | 按钮ID |")
                md_lines.append(f"|---------|------|------|------|--------|")
                for btn in page_view.buttons:
                    md_lines.append(f"| {btn.name} | {btn.category} | {btn.style} | {btn.location} | {btn.button_id or '-'} |")
                md_lines.append("")

            # 表格信息（优化版，区分主表和明细表）
            if page_view.tables:
                for table_info in page_view.tables:
                    table_label = "主表" if table_info.is_main_table else "明细子表"
                    md_lines.append(f"#### {table_label}（表格索引: {table_info.table_index})")
                    md_lines.append("")
                    if table_info.columns:
                        md_lines.append(f"| 字段名 | 数据类型 | 是否明细列 |")
                        md_lines.append(f"|-------|---------|----------|")
                        for col in table_info.columns:
                            md_lines.append(f"| {col.name} | {col.data_type} | {col.is_detail} |")
                        md_lines.append("")
                    md_lines.append(f"- 是否有勾选列: {table_info.has_checkbox}")
                    md_lines.append("")

            md_lines.append("---")
            md_lines.append("")

        # 技术实现建议
        md_lines.append("## 技术实现建议")
        md_lines.append("")
        md_lines.append("### 前端路由规划")
        md_lines.append("")
        md_lines.append("```typescript")
        md_lines.append("const routes = [")
        for menu in analysis.menus:
            if menu.page_id:
                route_path = menu.page_id.replace('-', '/')
                md_lines.append(f"  {{ path: '/{route_path}', name: '{menu.name}', component: () => import('@/views/{menu.page_id}/index.vue') }},")
        md_lines.append("];")
        md_lines.append("```")
        md_lines.append("")

        md_lines.append("### API接口规划")
        md_lines.append("")
        md_lines.append("```yaml")
        md_lines.append("# 建议的API接口结构")
        for page_view in analysis.page_views[:5]:
            md_lines.append(f"{page_view.view_id}:")
            api_name = page_view.view_id.replace('view-', '').replace('-view', '').replace('page-', '')
            md_lines.append(f"  list: GET /api/{api_name}/list")
            md_lines.append(f"  detail: GET /api/{api_name}/:id")
            md_lines.append(f"  create: POST /api/{api_name}")
            md_lines.append(f"  update: PUT /api/{api_name}/:id")
            md_lines.append(f"  delete: DELETE /api/{api_name}/:id")
        md_lines.append("```")
        md_lines.append("")

        md_lines.append("### 数据库表设计建议")
        md_lines.append("")
        md_lines.append("```sql")
        md_lines.append("-- 基于筛选条件和表格列推断的数据表结构")
        for page_view in analysis.page_views[:3]:
            main_table = None
            for t in page_view.tables:
                if t.is_main_table:
                    main_table = t
                    break
            if main_table and main_table.columns:
                table_name = page_view.view_id.replace('view-', '').replace('-view', '').replace('page-', '').replace('-', '_')
                md_lines.append(f"-- {page_view.name}表")
                md_lines.append(f"CREATE TABLE {table_name} (")
                md_lines.append(f"    id VARCHAR(36) PRIMARY KEY,")
                for col in main_table.columns[:15]:
                    col_name = col.name.lower().replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
                    if col.data_type == 'number':
                        md_lines.append(f"    {col_name} DECIMAL(10,2),")
                    elif col.data_type == 'date':
                        md_lines.append(f"    {col_name} DATE,")
                    elif col.data_type in ['link', 'currency']:
                        md_lines.append(f"    {col_name} VARCHAR(100),")
                    else:
                        md_lines.append(f"    {col_name} VARCHAR(200),")
                md_lines.append(f"    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
                md_lines.append(f"    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                md_lines.append(f");")
                md_lines.append("")
        md_lines.append("```")
        md_lines.append("")

        md_lines.append("---")
        md_lines.append("*生成工具: bie-zheng-luan-prototype技能 v3.0.0*")
        md_lines.append("*注意: 本分析基于HTML结构，实际业务逻辑需与产品经理确认*")

        return "\n".join(md_lines)

    def to_json(self, analysis: PrototypeAnalysis) -> str:
        """转换为JSON格式"""
        return json.dumps(asdict(analysis), ensure_ascii=False, indent=2)


def main():
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
# -*- coding: utf-8 -*-
"""
Shared application metadata constants.
"""

APP_NAME = '纸研社'
APP_VERSION = 'v1.5.3'

MODULE_PAPER_WRITE = '论文写作'
MODULE_AI_DIAGRAM = 'AI图表'
MODULE_AI_REDUCE = '降AI检测'
MODULE_PLAGIARISM = '降查重率'
MODULE_POLISH = '学术润色'
MODULE_CORRECTION = '智能纠错'
MODULE_HISTORY = '历史记录'

MODULE_FILTER_OPTIONS = (
    '全部',
    MODULE_PAPER_WRITE,
    MODULE_AI_DIAGRAM,
    MODULE_AI_REDUCE,
    MODULE_POLISH,
    MODULE_CORRECTION,
    MODULE_PLAGIARISM,
)

SOURCE_KIND_LABELS = {
    'manual': '手动输入',
    'import': '导入文件',
    'docx_import': '导入 DOCX',
    'paper_selection': '论文写作页选区',
    'paper_section': '论文写作页当前章节',
}

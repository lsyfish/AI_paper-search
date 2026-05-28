# -*- coding: utf-8 -*-
"""
AI 论文助手页面。
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from modules.prompt_center import PromptCenter, PromptCenterError
from modules.ui_components import COLORS, FONTS, CardFrame, ModernButton
from modules.workspace_state import WorkspaceStateMixin
from pages.home_support import ensure_model_configured


MODE_OPTIONS = [
    ('full', '完整论文', '从配置确认到成稿的完整工作流'),
    ('plan', '规划论文', '苏格拉底式引导，收敛研究问题'),
    ('outline-only', '仅生成大纲', '结构、章节、字数和证据映射'),
    ('lit-review', '文献综述', '检索策略、纳排标准和综述结构'),
    ('abstract-only', '仅生成摘要', '中文/英文/双语摘要与关键词'),
    ('revision', '修订论文', '根据评审意见修订正文'),
    ('revision-coach', '修订指导', '拆解评审意见和路线图'),
    ('citation-check', '检查引用', '审计引用、DOI 和格式风险'),
    ('format-convert', '格式转换', 'Markdown/LaTeX/DOCX/PDF 方案'),
    ('disclosure', 'AI 声明', '生成投稿用 AI 使用声明'),
]

MODE_SCENE_MAP = {
    'full': 'academic_paper.full',
    'plan': 'academic_paper.plan',
    'outline-only': 'academic_paper.outline',
    'lit-review': 'academic_paper.lit_review',
    'abstract-only': 'academic_paper.abstract',
    'revision': 'academic_paper.revision',
    'revision-coach': 'academic_paper.revision_coach',
    'citation-check': 'academic_paper.citation_check',
    'format-convert': 'academic_paper.format_convert',
    'disclosure': 'academic_paper.disclosure',
}

PAPER_TYPE_OPTIONS = [
    ('imrad', '实证研究论文'),
    ('literature_review', '文献综述论文'),
    ('case_study', '案例研究论文'),
    ('theoretical', '理论研究论文'),
    ('conference', '会议论文'),
    ('policy_brief', '政策简报'),
]

DISCIPLINE_OPTIONS = [
    ('education', '教育学'),
    ('management', '管理学'),
    ('economics', '经济学'),
    ('psychology', '心理学'),
    ('sociology', '社会学'),
    ('computer_science', '计算机科学'),
    ('engineering', '工程学'),
    ('medicine', '医学'),
    ('law', '法学'),
    ('humanities', '人文学科'),
    ('other', '其他'),
]

CITATION_FORMAT_OPTIONS = [
    ('APA 7', 'APA 7'),
    ('GB/T 7714', 'GB/T 7714'),
    ('Chicago', 'Chicago'),
    ('MLA 9', 'MLA 9'),
    ('IEEE', 'IEEE'),
    ('Vancouver', 'Vancouver'),
]

OUTPUT_FORMAT_OPTIONS = [
    ('markdown', 'Markdown'),
    ('latex', 'LaTeX'),
    ('docx', 'DOCX'),
    ('pdf', 'PDF'),
]

MODE_FIELD_LABELS = {
    'full': ('已有材料', '可粘贴文献、数据、研究想法或 deep-research 输出'),
    'plan': ('已有材料', '可粘贴文献、数据、研究想法或导师要求'),
    'outline-only': ('补充要求', '可说明章节数量、研究方法、学校/期刊要求'),
    'lit-review': ('检索范围', '数据库、年份、语言、纳排标准或已读文献'),
    'abstract-only': ('论文全文', '粘贴需要生成摘要的论文正文'),
    'revision': ('论文原文', '粘贴需要修订的论文草稿'),
    'revision-coach': ('评审意见', '粘贴审稿意见、导师批注或修改要求'),
    'citation-check': ('论文与参考文献', '粘贴正文引用和参考文献列表'),
    'format-convert': ('论文文本', '粘贴需要转换格式的论文正文'),
    'disclosure': ('AI 使用说明', '说明使用了哪些 AI 工具、用于哪些环节'),
}

MODE_SECONDARY_LABELS = {
    'revision': ('评审意见', '粘贴审稿意见或导师批注'),
    'revision-coach': ('论文原文', '可选：粘贴论文原文帮助定位修改'),
    'disclosure': ('论文摘要/方法', '可选：粘贴摘要、方法或致谢部分'),
}


class AcademicPaperPage(WorkspaceStateMixin):
    """迁移 academic-paper 技能后的桌面工作台。"""

    PAGE_STATE_ID = 'academic_paper'
    MODULE_NAME = 'AI论文助手'

    def __init__(
        self,
        parent,
        config_mgr,
        api_client,
        history_mgr,
        set_status,
        navigate_page=None,
        app_bridge=None,
    ):
        self.config = config_mgr
        self.api = api_client
        self.history = history_mgr
        self.set_status = set_status
        self.navigate_page = navigate_page
        self.app_bridge = app_bridge
        self.prompt_center = PromptCenter(config_mgr)
        self.frame = tk.Frame(parent, bg=COLORS['bg_main'])

        self._init_workspace_state_support()
        self._mode = 'full'
        self._is_processing = False
        self._conversation = []
        self._last_result = ''
        self._mode_buttons = {}
        self._value_vars = {}

        self._build()
        self.restore_saved_workspace_state()
        self._enable_workspace_state_autosave()
        self._refresh_mode_view()

    def _build(self):
        self.frame.grid_columnconfigure(0, weight=0, minsize=350)
        self.frame.grid_columnconfigure(1, weight=1, minsize=390)
        self.frame.grid_columnconfigure(2, weight=1, minsize=430)
        self.frame.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_sidebar()
        self._build_workspace()

    def _build_header(self):
        header_card = CardFrame(self.frame, padding=18)
        header_card.grid(row=0, column=0, columnspan=3, sticky='ew', padx=22, pady=(18, 12))
        header = header_card.inner
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text='AI 论文助手',
            font=(FONTS['hero'][0], 26, 'bold'),
            fg=COLORS['text_main'],
            bg=COLORS['card_bg'],
        ).grid(row=0, column=0, sticky='w')
        tk.Label(
            header,
            text='从选题规划、文献综述、成稿修订到投稿声明，一张桌面里跑完整 academic-paper 工作流。',
            font=FONTS['small'],
            fg=COLORS['text_sub'],
            bg=COLORS['card_bg'],
        ).grid(row=1, column=0, sticky='w', pady=(4, 0))

        chips = tk.Frame(header, bg=COLORS['card_bg'])
        chips.grid(row=2, column=0, sticky='w', pady=(12, 0))
        for text in ('12-agent', '10 modes', '引用合规', '写作模板内置'):
            self._build_chip(chips, text).pack(side=tk.LEFT, padx=(0, 8))

        self.status_label = tk.Label(
            header,
            text='就绪',
            font=FONTS['body_bold'],
            fg='#FFFFFF',
            bg=COLORS['success'],
            padx=14,
            pady=7,
        )
        self.status_label.grid(row=0, column=1, rowspan=3, sticky='ne', padx=(18, 0))

    @staticmethod
    def _build_chip(parent, text):
        return tk.Label(
            parent,
            text=text,
            font=FONTS['tiny'],
            fg=COLORS['text_main'],
            bg=COLORS['surface_alt'],
            padx=10,
            pady=5,
        )

    def _build_sidebar(self):
        sidebar = tk.Frame(self.frame, bg=COLORS['bg_main'])
        sidebar.grid(row=1, column=0, sticky='nsew', padx=(22, 10), pady=(0, 18))

        mode_card = CardFrame(sidebar, padding=16)
        mode_card.pack(fill=tk.X)
        self._section_title(mode_card.inner, '工作模式', '选择本轮 academic-paper 代理链路')

        grid = tk.Frame(mode_card.inner, bg=COLORS['card_bg'])
        grid.pack(fill=tk.X, pady=(12, 0))
        for index, (mode, label, _desc) in enumerate(MODE_OPTIONS):
            btn = tk.Button(
                grid,
                text=f'{label}\n{_desc}',
                font=FONTS['small'],
                justify=tk.LEFT,
                anchor='w',
                relief=tk.FLAT,
                bd=0,
                padx=12,
                pady=9,
                highlightthickness=1,
                cursor='hand2',
                command=lambda value=mode: self._switch_mode(value),
            )
            btn.grid(row=index, column=0, sticky='ew', pady=(0, 7))
            grid.grid_columnconfigure(0, weight=1)
            self._mode_buttons[mode] = btn

        config_card = CardFrame(sidebar, padding=16)
        config_card.pack(fill=tk.X, pady=(12, 0))
        self._section_title(config_card.inner, '论文配置', '用于填充提示词变量，可随时调整')

        self.topic_var = tk.StringVar()
        self.word_count_var = tk.StringVar(value='8000')
        self.venue_var = tk.StringVar()
        self.paper_type_var = tk.StringVar(value=PAPER_TYPE_OPTIONS[0][1])
        self.discipline_var = tk.StringVar(value=DISCIPLINE_OPTIONS[0][1])
        self.citation_format_var = tk.StringVar(value=CITATION_FORMAT_OPTIONS[0][1])
        self.output_format_var = tk.StringVar(value=OUTPUT_FORMAT_OPTIONS[0][1])

        self._build_entry(config_card.inner, '主题/研究问题', self.topic_var)
        self._paper_type_row = self._build_combo(config_card.inner, '论文类型', self.paper_type_var, PAPER_TYPE_OPTIONS)
        self._discipline_row = self._build_combo(config_card.inner, '学科方向', self.discipline_var, DISCIPLINE_OPTIONS)
        self._citation_row = self._build_combo(config_card.inner, '引用格式', self.citation_format_var, CITATION_FORMAT_OPTIONS)
        self._output_row = self._build_combo(config_card.inner, '输出格式', self.output_format_var, OUTPUT_FORMAT_OPTIONS)
        self._word_row = self._build_entry(config_card.inner, '目标字数', self.word_count_var)
        self._venue_row = self._build_entry(config_card.inner, '投稿期刊/会议', self.venue_var)

        material_card = CardFrame(sidebar, padding=16)
        material_card.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self.primary_label = tk.Label(material_card.inner, font=FONTS['body_bold'], fg=COLORS['text_main'], bg=COLORS['card_bg'])
        self.primary_label.pack(anchor='w')
        self.primary_hint = tk.Label(material_card.inner, font=FONTS['tiny'], fg=COLORS['text_sub'], bg=COLORS['card_bg'], justify='left', anchor='w', wraplength=270)
        self.primary_hint.pack(fill=tk.X, pady=(2, 8))
        self.primary_text = self._build_text(material_card.inner, height=7)
        self.primary_text.pack(fill=tk.BOTH, expand=True)

        self.secondary_frame = tk.Frame(material_card.inner, bg=COLORS['card_bg'])
        self.secondary_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self.secondary_label = tk.Label(self.secondary_frame, font=FONTS['body_bold'], fg=COLORS['text_main'], bg=COLORS['card_bg'])
        self.secondary_label.pack(anchor='w')
        self.secondary_hint = tk.Label(self.secondary_frame, font=FONTS['tiny'], fg=COLORS['text_sub'], bg=COLORS['card_bg'], justify='left', anchor='w', wraplength=270)
        self.secondary_hint.pack(fill=tk.X, pady=(2, 8))
        self.secondary_text = self._build_text(self.secondary_frame, height=5)
        self.secondary_text.pack(fill=tk.BOTH, expand=True)

        for var in (
            self.topic_var, self.word_count_var, self.venue_var, self.paper_type_var,
            self.discipline_var, self.citation_format_var, self.output_format_var,
        ):
            var.trace_add('write', lambda *_args: self._schedule_workspace_state_save())
        self.primary_text.bind('<<Modified>>', self._handle_text_modified, add='+')
        self.secondary_text.bind('<<Modified>>', self._handle_text_modified, add='+')

    def _build_workspace(self):
        conversation_card = CardFrame(self.frame, padding=18)
        conversation_card.grid(row=1, column=1, sticky='nsew', padx=(10, 10), pady=(0, 18))
        conversation_card.inner.grid_columnconfigure(0, weight=1)
        conversation_card.inner.grid_rowconfigure(4, weight=1)

        composer_heading = tk.Frame(conversation_card.inner, bg=COLORS['card_bg'])
        composer_heading.grid(row=0, column=0, sticky='ew')
        self._section_title(composer_heading, '对话与输入', '输入区固定在工作台中部，Ctrl+Enter 发送')

        self.input_text = self._build_text(conversation_card.inner, height=8)
        self.input_text.grid(row=1, column=0, sticky='ew', pady=(10, 0))
        self.input_text.bind('<Control-Return>', lambda _event: self._send_message())

        action_row = tk.Frame(conversation_card.inner, bg=COLORS['card_bg'])
        action_row.grid(row=2, column=0, sticky='ew', pady=(10, 14))
        action_row.grid_columnconfigure(0, weight=1)
        quick_row = tk.Frame(action_row, bg=COLORS['card_bg'])
        quick_row.grid(row=0, column=0, sticky='w')
        for label, text in (
            ('确认配置', '请根据当前信息生成 Paper Configuration Record，并指出还缺哪些关键信息。'),
            ('下一步', '请基于当前对话推进下一阶段，并说明本阶段产出与检查点。'),
            ('风险检查', '请检查当前方案的引用、数据、方法和写作风险。'),
        ):
            btn = tk.Button(
                quick_row,
                text=label,
                font=FONTS['small'],
                fg=COLORS['text_main'],
                bg=COLORS['surface_alt'],
                activebackground=COLORS['primary_light'],
                relief=tk.FLAT,
                bd=0,
                padx=12,
                pady=6,
                cursor='hand2',
                command=lambda payload=text: self._insert_quick_prompt(payload),
            )
            btn.pack(side=tk.LEFT, padx=(0, 8))
        self.send_button = ModernButton(action_row, '发送到代理链', style='primary', command=self._send_message)
        self.send_button.grid(row=0, column=1, sticky='e')

        chat_heading = tk.Frame(conversation_card.inner, bg=COLORS['card_bg'])
        chat_heading.grid(row=3, column=0, sticky='ew')
        self._section_title(chat_heading, '对话记录', '保留最近工作上下文')
        self.chat_text = self._build_text(conversation_card.inner, height=12)
        self.chat_text.grid(row=4, column=0, sticky='nsew', pady=(10, 0))
        self.chat_text.configure(state=tk.DISABLED)

        result_card = CardFrame(self.frame, padding=18)
        result_card.grid(row=1, column=2, sticky='nsew', padx=(10, 22), pady=(0, 18))
        result_card.inner.grid_columnconfigure(0, weight=1)
        result_card.inner.grid_rowconfigure(1, weight=2)
        result_card.inner.grid_rowconfigure(4, weight=3)

        title_row = tk.Frame(result_card.inner, bg=COLORS['card_bg'])
        title_row.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        title_row.grid_columnconfigure(0, weight=1)
        self.mode_title_label = tk.Label(
            title_row,
            text='产出稿',
            font=(FONTS['title'][0], 20, 'bold'),
            fg=COLORS['text_main'],
            bg=COLORS['card_bg'],
        )
        self.mode_title_label.grid(row=0, column=0, sticky='w')
        self.mode_desc_label = tk.Label(
            title_row,
            text='',
            font=FONTS['small'],
            fg=COLORS['text_sub'],
            bg=COLORS['card_bg'],
        )
        self.mode_desc_label.grid(row=1, column=0, sticky='w', pady=(3, 0))

        self.copy_button = ModernButton(title_row, '复制结果', style='secondary', command=self._copy_result)
        self.copy_button.grid(row=0, column=1, rowspan=2, sticky='e', padx=(10, 0))
        self.save_button = ModernButton(title_row, '保存历史', style='secondary', command=self._save_current_result)
        self.save_button.grid(row=0, column=2, rowspan=2, sticky='e', padx=(8, 0))
        self.export_button = ModernButton(title_row, '导出文件', style='secondary', command=self._export_result)
        self.export_button.grid(row=0, column=3, rowspan=2, sticky='e', padx=(8, 0))
        self.clear_button = ModernButton(title_row, '清空', style='secondary', command=self._clear_workspace)
        self.clear_button.grid(row=0, column=4, rowspan=2, sticky='e', padx=(8, 0))

        self.result_text = self._build_text(result_card.inner, height=9)
        self.result_text.grid(row=1, column=0, sticky='nsew')

        # ── 草稿区中间栏 ──────────────────────────────────────────
        mid_bar = tk.Frame(result_card.inner, bg=COLORS['card_bg'])
        mid_bar.grid(row=2, column=0, sticky='ew', pady=(10, 6))
        mid_bar.grid_columnconfigure(0, weight=1)
        tk.Label(
            mid_bar,
            text='论文草稿',
            font=FONTS['body_bold'],
            fg=COLORS['text_main'],
            bg=COLORS['card_bg'],
        ).grid(row=0, column=0, sticky='w')
        tk.Label(
            mid_bar,
            text='可手动追加产出稿内容，完成后写入论文写作页',
            font=FONTS['tiny'],
            fg=COLORS['text_sub'],
            bg=COLORS['card_bg'],
        ).grid(row=1, column=0, sticky='w', pady=(2, 0))

        draft_btn_frame = tk.Frame(mid_bar, bg=COLORS['card_bg'])
        draft_btn_frame.grid(row=0, column=1, rowspan=2, sticky='e')
        ModernButton(
            draft_btn_frame, '↓ 追加到草稿', style='secondary',
            command=self._append_result_to_draft,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ModernButton(
            draft_btn_frame, '写入论文写作', style='primary',
            command=self._send_draft_to_paper_write,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ModernButton(
            draft_btn_frame, '清空草稿', style='secondary',
            command=self._clear_draft,
        ).pack(side=tk.LEFT)

        tk.Frame(result_card.inner, bg=COLORS['divider'], height=1).grid(
            row=3, column=0, sticky='ew', pady=(0, 6)
        )

        self.draft_text = self._build_text(result_card.inner, height=11)
        self.draft_text.grid(row=4, column=0, sticky='nsew')

    @staticmethod
    def _section_title(parent, title, subtitle=''):
        tk.Label(
            parent,
            text=title,
            font=FONTS['body_bold'],
            fg=COLORS['text_main'],
            bg=COLORS['card_bg'],
        ).pack(anchor='w')
        if subtitle:
            tk.Label(
                parent,
                text=subtitle,
                font=FONTS['tiny'],
                fg=COLORS['text_sub'],
                bg=COLORS['card_bg'],
                justify='left',
                anchor='w',
            ).pack(anchor='w', pady=(2, 0))

    @staticmethod
    def _build_text(parent, height=5):
        text = tk.Text(
            parent,
            height=height,
            wrap=tk.WORD,
            font=FONTS['body'],
            fg=COLORS['text_main'],
            bg=COLORS['input_bg'],
            insertbackground=COLORS['text_main'],
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=10,
            highlightthickness=1,
            highlightbackground=COLORS['input_border'],
            highlightcolor=COLORS['primary'],
        )
        return text

    @staticmethod
    def _build_entry(parent, label, variable):
        row = tk.Frame(parent, bg=COLORS['card_bg'])
        row.pack(fill=tk.X, pady=(10, 0))
        tk.Label(row, text=label, font=FONTS['small'], fg=COLORS['text_sub'], bg=COLORS['card_bg']).pack(anchor='w')
        entry = tk.Entry(
            row,
            textvariable=variable,
            font=FONTS['body'],
            fg=COLORS['text_main'],
            bg=COLORS['input_bg'],
            insertbackground=COLORS['text_main'],
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=COLORS['input_border'],
            highlightcolor=COLORS['primary'],
        )
        entry.pack(fill=tk.X, pady=(5, 0), ipady=7)
        return row

    @staticmethod
    def _build_combo(parent, label, variable, options):
        row = tk.Frame(parent, bg=COLORS['card_bg'])
        row.pack(fill=tk.X, pady=(10, 0))
        tk.Label(row, text=label, font=FONTS['small'], fg=COLORS['text_sub'], bg=COLORS['card_bg']).pack(anchor='w')
        combo = ttk.Combobox(
            row,
            textvariable=variable,
            values=[label for _value, label in options],
            state='readonly',
            font=FONTS['body'],
        )
        combo.pack(fill=tk.X, pady=(5, 0), ipady=4)
        return row

    def _handle_text_modified(self, event):
        widget = event.widget
        try:
            widget.edit_modified(False)
        except tk.TclError:
            pass
        self._schedule_workspace_state_save()

    def _switch_mode(self, mode):
        if self._is_processing:
            return
        self._mode = mode
        self._refresh_mode_view()
        self._append_chat('系统', f'已切换到「{self._mode_label(mode)}」模式。')
        self._schedule_workspace_state_save()

    def _refresh_mode_view(self):
        for mode, button in self._mode_buttons.items():
            active = mode == self._mode
            button.configure(
                bg=COLORS['primary'] if active else COLORS['surface_alt'],
                fg='#FFFFFF' if active else COLORS['text_main'],
                activebackground=COLORS['primary'] if active else COLORS['primary_light'],
                activeforeground='#FFFFFF' if active else COLORS['text_main'],
                highlightbackground=COLORS['primary'] if active else COLORS['card_border'],
            )
        label, desc = self._mode_label(self._mode), self._mode_description(self._mode)
        self.mode_title_label.configure(text=label)
        self.mode_desc_label.configure(text=desc)

        primary_label, primary_hint = MODE_FIELD_LABELS.get(self._mode, ('材料', ''))
        self.primary_label.configure(text=primary_label)
        self.primary_hint.configure(text=primary_hint)

        secondary = MODE_SECONDARY_LABELS.get(self._mode)
        if secondary:
            self.secondary_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
            self.secondary_label.configure(text=secondary[0])
            self.secondary_hint.configure(text=secondary[1])
        else:
            self.secondary_frame.pack_forget()

        self._set_row_visible(self._paper_type_row, self._mode in {'full', 'outline-only'})
        self._set_row_visible(self._discipline_row, self._mode in {'full'})
        self._set_row_visible(self._citation_row, self._mode in {'full', 'citation-check', 'format-convert'})
        self._set_row_visible(self._output_row, self._mode in {'full', 'format-convert'})
        self._set_row_visible(self._word_row, self._mode in {'full'})
        self._set_row_visible(self._venue_row, self._mode == 'disclosure')

    @staticmethod
    def _set_row_visible(row, visible):
        if visible:
            if not row.winfo_ismapped():
                row.pack(fill=tk.X, pady=(10, 0))
        else:
            if row.winfo_ismapped():
                row.pack_forget()

    @staticmethod
    def _mode_label(mode):
        for item_mode, label, _desc in MODE_OPTIONS:
            if item_mode == mode:
                return label
        return mode

    @staticmethod
    def _mode_description(mode):
        for item_mode, _label, desc in MODE_OPTIONS:
            if item_mode == mode:
                return desc
        return ''

    def _text_value(self, widget):
        return widget.get('1.0', tk.END).strip()

    def _set_text_value(self, widget, value, readonly=False):
        state = str(widget.cget('state'))
        if state == tk.DISABLED:
            widget.configure(state=tk.NORMAL)
        widget.delete('1.0', tk.END)
        widget.insert('1.0', str(value or ''))
        if readonly:
            widget.configure(state=tk.DISABLED)

    def _insert_quick_prompt(self, text):
        self.input_text.insert(tk.END, (('\n' if self._text_value(self.input_text) else '') + text))
        self.input_text.focus_set()

    def _append_chat(self, speaker, content):
        line = f'{speaker}：{content.strip()}\n\n'
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END, line)
        self.chat_text.see(tk.END)
        self.chat_text.configure(state=tk.DISABLED)

    def _conversation_text(self, pending_user_input=''):
        lines = []
        for item in self._conversation[-12:]:
            lines.append(f'{item.get("role", "")}: {item.get("content", "")}')
        if pending_user_input:
            lines.append(f'user: {pending_user_input}')
        return '\n\n'.join(lines)

    def _collect_scene_values(self, user_input):
        primary = self._text_value(self.primary_text)
        secondary = self._text_value(self.secondary_text)
        values = {
            'topic': self.topic_var.get().strip(),
            'paper_type': self.paper_type_var.get().strip(),
            'discipline': self.discipline_var.get().strip(),
            'citation_format': self.citation_format_var.get().strip(),
            'output_format': self.output_format_var.get().strip(),
            'word_count': self.word_count_var.get().strip(),
            'conversation': self._conversation_text(user_input),
            'materials': primary,
            'scope': primary,
            'full_text': primary,
            'paper_text': primary,
            'review_comments': secondary,
            'venue': self.venue_var.get().strip(),
            'ai_usage': primary,
            'language': 'bilingual',
        }
        if self._mode == 'revision':
            values['paper_text'] = primary
            values['review_comments'] = secondary
        elif self._mode == 'revision-coach':
            values['review_comments'] = primary
            values['paper_text'] = secondary
        elif self._mode == 'disclosure':
            values['ai_usage'] = primary
            values['paper_text'] = secondary
        return values

    def _send_message(self):
        if self._is_processing:
            return
        if not ensure_model_configured(self.config, self.frame, self.app_bridge):
            return
        user_input = self._text_value(self.input_text)
        if not user_input:
            messagebox.showinfo('AI 论文助手', '请输入你的问题或指令。', parent=self.frame)
            return

        self._set_text_value(self.input_text, '')
        self._conversation.append({'role': 'user', 'content': user_input})
        self._append_chat('你', user_input)
        self._set_processing(True, '处理中...')

        thread = threading.Thread(target=self._run_request, args=(user_input,), daemon=True)
        thread.start()

    def _run_request(self, user_input):
        try:
            scene_id = MODE_SCENE_MAP.get(self._mode, 'academic_paper.full')
            values = self._collect_scene_values(user_input)
            rendered = self.prompt_center.render_scene(scene_id, values)
            prompt = (
                f'{rendered.get("prompt", "")}\n\n'
                f'## 用户最新输入\n{user_input}\n\n'
                '请直接给出本轮产出。'
            )
            result = self.api.call_sync(
                prompt,
                rendered.get('system', ''),
                temperature=0.35,
                max_tokens=3500,
                usage_context={
                    'page_id': self.PAGE_STATE_ID,
                    'scene_id': scene_id,
                    'action': self._mode,
                    'mode': self._mode,
                },
            )
            self.frame.after(0, lambda: self._handle_response(user_input, result))
        except Exception as exc:
            self.frame.after(0, lambda: self._handle_error(exc))

    def _handle_response(self, user_input, result):
        text = str(result or '').strip()
        self._last_result = text
        self._conversation.append({'role': 'assistant', 'content': text})
        self._append_chat('AI 论文助手', text[:1200] + ('...' if len(text) > 1200 else ''))
        self._set_text_value(self.result_text, text)
        self._set_processing(False, '完成')
        self._save_history(user_input, text)
        self.save_workspace_state_now(save_to_disk=False)

    def _handle_error(self, exc):
        self._set_processing(False, '错误', error=True)
        message = str(exc)
        self._append_chat('系统', f'请求失败：{message}')
        self._set_text_value(self.result_text, f'请求失败：{message}')

    def _set_processing(self, active, status, error=False):
        self._is_processing = bool(active)
        self.send_button.configure(state=tk.DISABLED if active else tk.NORMAL)
        color = COLORS['warning'] if active else (COLORS['error'] if error else COLORS['success'])
        self.status_label.configure(text=status, bg=color, fg='#FFFFFF')
        self.set_status(f'AI论文助手：{status}', color)

    def _copy_result(self):
        text = self._text_value(self.result_text)
        if not text:
            return
        self.frame.clipboard_clear()
        self.frame.clipboard_append(text)
        self.set_status('已复制 AI 论文助手结果', COLORS['success'])

    def _export_result(self):
        text = self._text_value(self.result_text)
        if not text:
            messagebox.showinfo('导出文件', '当前没有可导出的结果。', parent=self.frame)
            return

        topic = self.topic_var.get().strip()
        default_name = (topic[:30] if topic else '论文助手结果').replace('/', '_').replace('\\', '_')

        path = filedialog.asksaveasfilename(
            parent=self.frame,
            title='导出结果',
            initialfile=default_name,
            defaultextension='.txt',
            filetypes=[
                ('Word 文档', '*.docx'),
                ('纯文本', '*.txt'),
                ('Markdown', '*.md'),
            ],
        )
        if not path:
            return

        try:
            if path.lower().endswith('.docx'):
                self._export_as_docx(text, path)
            else:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(text)
            self.set_status(f'已导出到 {path}', COLORS['success'])
        except Exception as exc:
            messagebox.showerror('导出失败', str(exc), parent=self.frame)

    def _export_as_docx(self, text: str, path: str) -> None:
        import docx
        from docx.shared import Cm, Pt

        doc = docx.Document()
        for section in doc.sections:
            section.top_margin = Cm(2.54)
            section.bottom_margin = Cm(2.54)
            section.left_margin = Cm(3.17)
            section.right_margin = Cm(3.17)

        topic = self.topic_var.get().strip()
        if topic:
            heading = doc.add_heading(topic, level=0)
            heading.runs[0].font.size = Pt(16)

        for para in text.split('\n'):
            stripped = para.strip()
            if not stripped:
                doc.add_paragraph('')
                continue
            # Treat lines starting with # as headings
            if stripped.startswith('###'):
                p = doc.add_heading(stripped.lstrip('#').strip(), level=3)
            elif stripped.startswith('##'):
                p = doc.add_heading(stripped.lstrip('#').strip(), level=2)
            elif stripped.startswith('#'):
                p = doc.add_heading(stripped.lstrip('#').strip(), level=1)
            else:
                p = doc.add_paragraph(stripped)
                p.runs[0].font.size = Pt(12) if p.runs else None

        doc.save(path)

    def _save_current_result(self):
        text = self._text_value(self.result_text)
        if not text:
            messagebox.showinfo('AI 论文助手', '当前没有可保存的结果。', parent=self.frame)
            return
        self._save_history('手动保存', text, force=True)
        self.set_status('AI 论文助手结果已保存到历史记录', COLORS['success'])

    def _save_history(self, input_text, output_text, force=False):
        if not self.history:
            return
        if not force and self.config and not self.config.get_setting('auto_save_history', True):
            return
        try:
            self.history.add(
                self._mode_label(self._mode),
                input_text,
                output_text,
                self.MODULE_NAME,
                extra={
                    'mode': self._mode,
                    'scene_id': MODE_SCENE_MAP.get(self._mode, ''),
                    'topic': self.topic_var.get().strip(),
                },
                page_state_id=self.PAGE_STATE_ID,
                workspace_state=self.capture_workspace_state_snapshot(save_to_disk=False),
            )
        except Exception:
            pass

    def _append_result_to_draft(self):
        text = self._text_value(self.result_text)
        if not text:
            return
        current = self._text_value(self.draft_text)
        separator = '\n\n' if current else ''
        self._set_text_value(self.draft_text, current + separator + text)
        self.set_status('已将产出稿内容追加到论文草稿', COLORS['success'])
        self.save_workspace_state_now(save_to_disk=False)

    def _send_draft_to_paper_write(self):
        text = self._text_value(self.draft_text)
        if not text:
            self.set_status('论文草稿为空，请先追加产出稿内容', COLORS['warning'])
            return
        if not self.app_bridge:
            self.set_status('无法连接到论文写作页', COLORS['error'])
            return
        topic = self.topic_var.get().strip() or '论文正文'
        outcome = self.app_bridge.apply_result_to_paper_write(
            text,
            target_mode='body',
            write_mode='replace',
            section_hint=topic,
        )
        if outcome.get('ok'):
            self.set_status(f'已将论文草稿写入论文写作页「{topic}」章节', COLORS['success'])
            if self.navigate_page:
                self.navigate_page('paper_write')
        else:
            self.set_status(f'写入失败：{outcome.get("message", "")}', COLORS['error'])

    def _clear_draft(self):
        if not self._text_value(self.draft_text):
            return
        if messagebox.askyesno('清空草稿', '确定清空论文草稿区内容吗？', parent=self.frame):
            self._set_text_value(self.draft_text, '')
            self.save_workspace_state_now(save_to_disk=False)

    def _clear_workspace(self):
        if not messagebox.askyesno('AI 论文助手', '确定清空当前对话、材料和结果吗？', parent=self.frame):
            return
        self._conversation = []
        self._last_result = ''
        for widget in (self.primary_text, self.secondary_text, self.result_text, self.input_text, self.draft_text):
            self._set_text_value(widget, '')
        self._set_text_value(self.chat_text, '', readonly=True)
        self.save_workspace_state_now(save_to_disk=True)

    def export_workspace_state(self):
        return {
            'mode': self._mode,
            'topic': self.topic_var.get(),
            'paper_type': self.paper_type_var.get(),
            'discipline': self.discipline_var.get(),
            'citation_format': self.citation_format_var.get(),
            'output_format': self.output_format_var.get(),
            'word_count': self.word_count_var.get(),
            'venue': self.venue_var.get(),
            'primary_text': self._text_value(self.primary_text),
            'secondary_text': self._text_value(self.secondary_text),
            'input_text': self._text_value(self.input_text),
            'result_text': self._text_value(self.result_text),
            'draft_text': self._text_value(self.draft_text),
            'conversation': list(self._conversation[-40:]),
        }

    def restore_workspace_state(self, state):
        state = dict(state or {})
        self._mode = str(state.get('mode') or 'full')
        if self._mode not in MODE_SCENE_MAP:
            self._mode = 'full'
        self.topic_var.set(str(state.get('topic') or ''))
        self.paper_type_var.set(str(state.get('paper_type') or PAPER_TYPE_OPTIONS[0][1]))
        self.discipline_var.set(str(state.get('discipline') or DISCIPLINE_OPTIONS[0][1]))
        self.citation_format_var.set(str(state.get('citation_format') or CITATION_FORMAT_OPTIONS[0][1]))
        self.output_format_var.set(str(state.get('output_format') or OUTPUT_FORMAT_OPTIONS[0][1]))
        self.word_count_var.set(str(state.get('word_count') or '8000'))
        self.venue_var.set(str(state.get('venue') or ''))
        self._set_text_value(self.primary_text, state.get('primary_text', ''))
        self._set_text_value(self.secondary_text, state.get('secondary_text', ''))
        self._set_text_value(self.input_text, state.get('input_text', ''))
        self._set_text_value(self.result_text, state.get('result_text', ''))
        self._last_result = self._text_value(self.result_text)
        self._set_text_value(self.draft_text, state.get('draft_text', ''))
        self._conversation = [item for item in state.get('conversation', []) if isinstance(item, dict)]
        chat_lines = []
        for item in self._conversation[-20:]:
            speaker = '你' if item.get('role') == 'user' else 'AI 论文助手'
            chat_lines.append(f'{speaker}：{item.get("content", "")}')
        self._set_text_value(self.chat_text, '\n\n'.join(chat_lines), readonly=True)

    def on_show(self):
        pending_mode = ''
        if self.config:
            pending_mode = str(self.config.get_setting('academic_paper_pending_mode', '') or '').strip()
        if pending_mode in MODE_SCENE_MAP:
            self._mode = pending_mode
            self.config.set_setting('academic_paper_pending_mode', '')
            self._refresh_mode_view()

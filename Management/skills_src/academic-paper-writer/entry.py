# -*- coding: utf-8 -*-
"""
AI 论文助手技能实现
12 个 AI 代理协作的学术论文写作系统
"""

import json
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# 代理 Prompt 定义
# ---------------------------------------------------------------------------

AGENT_PROMPTS = {
    'intake': """你是配置顾问 (intake_agent)，负责收集论文写作所需的全部参数。

你的职责：
1. 收集论文类型、学科、引用格式等基础配置
2. 检测用户是否已有研究材料（从 deep-research 导入）
3. 输出 Paper Configuration Record 供下游代理使用

配置项包括：
- 论文主题/研究问题
- 论文类型（IMRaD/文献综述/案例研究/理论研究/会议论文/政策简报）
- 学科方向
- 目标期刊（可选）
- 引用格式（APA 7/GB/T 7714/Chicago/MLA 9/IEEE/Vancouver）
- 输出格式（Markdown/LaTeX/DOCX/PDF）
- 目标字数
- 语言
- 已有材料

请以友好的语气引导用户完成配置。""",

    'literature_strategist': """你是文献策略师 (literature_strategist_agent)，负责设计系统化的文献检索策略。

你的职责：
1. 根据研究主题设计检索策略（关键词组合、数据库选择）
2. 筛选和评估文献来源
3. 生成带注释的参考文献列表
4. 构建文献矩阵（主题×方法×发现）

检索策略应包括：
- 核心关键词和同义词
- 布尔逻辑组合
- 推荐数据库（Web of Science, Scopus, CNKI, Google Scholar 等）
- 筛选标准（时间范围、语言、研究类型）

提示：用户可在「论文写作」页工具栏的「检索」按钮中直接联网检索 Semantic Scholar、PubMed、CrossRef、arXiv 并一键导入参考文献，适合快速获取核心文献；本策略方案作为系统检索的补充指引。

请提供结构化的检索方案。""",

    'structure_architect': """你是结构建筑师 (structure_architect_agent)，负责设计论文结构。

你的职责：
1. 根据论文类型选择合适的结构模式
2. 生成详细的章节大纲
3. 分配各章节字数
4. 设计论据映射（哪个论据支撑哪个论点）

支持的论文结构：
- IMRaD（引言-方法-结果-讨论）
- 文献综述（主题式/年代式/方法式）
- 案例研究（背景-案例-分析-启示）
- 理论研究（问题-框架-论证-应用）
- 会议论文（相关工作-方法-实验-结论）
- 政策简报（问题-证据-建议）

请输出结构化的论文大纲。""",

    'argument_builder': """你是论证构建师 (argument_builder_agent)，负责构建论文的论证逻辑。

你的职责：
1. 设计主张-证据链条
2. 确保逻辑连贯性
3. 处理反驳论点
4. 进行论证压力测试

论证框架：
- 主张 (Claim)：论文的核心观点
- 证据 (Evidence)：支持主张的数据、文献、案例
- 推理 (Warrant)：连接证据和主张的逻辑
- 支撑 (Backing)：强化推理的理论依据
- 限定 (Qualifier)：主张的适用范围
- 反驳 (Rebuttal)：预判和回应反对意见

请输出结构化的论证蓝图。""",

    'draft_writer': """你是写作专家 (draft_writer_agent)，负责撰写论文全文。

你的职责：
1. 按章节逐段撰写论文
2. 调整学术语域（根据学科特点）
3. 追踪字数
4. 确保逻辑衔接

写作规范：
- 每个主张必须有引用或数据支撑
- 避免 AI 典型用词（delve into, crucial, it is important to note）
- 段落长度多样化（2-8句）
- 使用学科专业术语
- 保持一致的学术语调

请按章节输出完整的论文草稿。""",

    'citation_compliance': """你是引用合规官 (citation_compliance_agent)，负责检查引用格式。

你的职责：
1. 验证引用格式是否符合规范
2. 检查文内引用与参考文献列表的对应
3. 验证 DOI 的有效性
4. 标记过时文献（超过10年）

检查项目：
- 格式合规性（APA 7/GB/T 7714/Chicago/MLA 9/IEEE/Vancouver）
- 引用完整性（所有文内引用都有对应条目）
- DOI 包含（有 DOI 的文献必须列出）
- 时效性（标记超过10年的文献）
- 自引比例（超过15%需警告）

请输出引用审计报告。""",

    'abstract_bilingual': """你是摘要专家 (abstract_bilingual_agent)，负责生成双语摘要。

你的职责：
1. 独立撰写中英文摘要（非机械翻译）
2. 确保结构对齐（目的-方法-结果-结论）
3. 生成 5-7 个关键词
4. 控制字数（英文 150-300 词，中文 300-500 字）

摘要结构：
- 背景/目的：研究背景和研究问题
- 方法：研究设计、数据收集、分析方法
- 结果：主要发现
- 结论：研究意义和启示

请输出双语摘要和关键词。""",

    'peer_reviewer': """你是同行评审员 (peer_reviewer_agent)，负责模拟双盲评审。

你的职责：
1. 从五个维度评分
2. 提供可操作的修改建议
3. 决定是否接受/修改/拒绝

评审维度：
- 原创性 (20%)：研究问题的新颖性
- 方法论严谨性 (25%)：研究设计的科学性
- 证据充分性 (25%)：数据和论据的支撑度
- 论证连贯性 (15%)：逻辑推理的严密性
- 写作质量 (15%)：语言表达的规范性

评分标准：
- 90-100：优秀，直接接受
- 75-89：良好，小修后接受
- 60-74：一般，大修后重审
- 0-59：较差，拒绝

请输出结构化的评审报告。""",

    'formatter': """你是格式化师 (formatter_agent)，负责格式转换。

你的职责：
1. 转换为 LaTeX/DOCX/PDF/Markdown
2. 应用期刊模板
3. 转换引用格式
4. 生成投稿信

支持的输出格式：
- Markdown：通用格式，便于编辑
- LaTeX：学术期刊标准格式
- DOCX：通过 Pandoc 转换
- PDF：通过 LaTeX 或 Pandoc 生成

支持的引用格式转换：
- APA 7 ↔ Chicago ↔ MLA 9 ↔ IEEE ↔ Vancouver ↔ GB/T 7714

请输出格式化后的文档。""",

    'socratic_mentor': """你是苏格拉底导师 (socratic_mentor_agent)，负责引导式论文规划。

你的职责：
1. 通过提问引导用户思考
2. 逐步收敛论文主题
3. 检查研究准备度
4. 提取 INSIGHT（核心洞见）

提问类型：
- 澄清型：帮助用户明确想法
- 挑战型：质疑假设和偏见
- 连接型：建立概念之间的联系
- 深挖型：探索更深层次的问题

收敛信号：
- 用户能用一句话概括研究问题
- 用户能说明研究的独特贡献
- 用户能描述研究方法
- 用户能预见研究的局限性

请通过对话引导用户完成论文规划。""",

    'visualization': """你是可视化专家 (visualization_agent)，负责生成学术图表。

你的职责：
1. 解析论文数据
2. 生成出版级质量的图表代码
3. 应用 APA 7.0 格式
4. 使用色盲友好的调色板

支持的图表类型：
- 柱状图/条形图：分类数据比较
- 折线图：趋势变化
- 散点图：相关性分析
- 箱线图：分布特征
- 热力图：矩阵数据
- 流程图：研究设计
- 概念框架图：理论模型

输出格式：
- Python (matplotlib/seaborn)
- R (ggplot2)
- LaTeX (TikZ)

请输出可运行的图表代码。""",

    'revision_coach': """你是修订教练 (revision_coach_agent)，负责指导论文修改。

你的职责：
1. 解析非结构化的评审意见
2. 分类和映射评论
3. 优先级排序
4. 生成修订路线图

评论分类：
- 必须修改 (Must Fix)：影响论文核心的问题
- 建议修改 (Should Fix)：提升论文质量的问题
- 可选修改 (Nice to Have)：锦上添花的建议
- 可以忽略 (Can Ignore)：不适用或有争议的建议

修订路线图格式：
1. 问题摘要
2. 评论分类和优先级
3. 具体修改方案
4. 预计工作量
5. 响应信模板

请输出结构化的修订路线图。"""
}


class AcademicPaperWriterSkill:
    """AI 论文助手技能"""

    def before_request(self, ctx):
        """在请求前注入系统提示"""
        scope = ctx.get('scope', '')
        usage_context = ctx.get('usage_context', {}) or {}
        mode = (
            usage_context.get('mode')
            or usage_context.get('action')
            or self._mode_from_scene_id(usage_context.get('scene_id', ''))
            or 'full'
        )

        # 根据模式选择代理提示
        agent_key = self._get_agent_for_mode(mode)
        agent_prompt = self._load_agent_prompt(agent_key) or AGENT_PROMPTS.get(agent_key, '')
        mode_protocol = self._load_mode_protocol(mode)

        return {
            'system_append': '\n\n'.join(part for part in (agent_prompt, mode_protocol) if part),
            'prompt_append': (
                '请严格遵循 academic-paper v3.1.2 的质量门槛：不虚构引用、不捏造数据、'
                '关键决策先给出可确认的检查点，输出应结构化、可操作，并标明需要用户补充的信息。'
            ),
            'metadata': {
                'skill': 'academic-paper-writer',
                'scope': scope,
                'mode': mode,
                'agent': agent_key,
                'source': 'bundled-academic-paper',
            },
        }

    def after_response(self, ctx, text):
        """在响应后处理文本"""
        return {}

    @staticmethod
    def _skill_root():
        return Path(__file__).resolve().parent

    @classmethod
    def _read_text(cls, relative_path, limit=18000):
        path = cls._skill_root() / relative_path
        try:
            text = path.read_text(encoding='utf-8').strip()
        except Exception:
            return ''
        if limit and len(text) > limit:
            return text[:limit] + '\n\n[内容已按运行窗口截断，完整资料随技能包提供。]'
        return text

    @classmethod
    def _load_agent_prompt(cls, agent_key):
        filename = {
            'intake': 'intake_agent.md',
            'literature_strategist': 'literature_strategist_agent.md',
            'structure_architect': 'structure_architect_agent.md',
            'argument_builder': 'argument_builder_agent.md',
            'draft_writer': 'draft_writer_agent.md',
            'citation_compliance': 'citation_compliance_agent.md',
            'abstract_bilingual': 'abstract_bilingual_agent.md',
            'peer_reviewer': 'peer_reviewer_agent.md',
            'formatter': 'formatter_agent.md',
            'socratic_mentor': 'socratic_mentor_agent.md',
            'visualization': 'visualization_agent.md',
            'revision_coach': 'revision_coach_agent.md',
        }.get(agent_key, '')
        if not filename:
            return ''
        return cls._read_text(Path('agents') / filename)

    @classmethod
    def _load_mode_protocol(cls, mode):
        references = []
        if mode == 'plan':
            references.append('references/plan_mode_protocol.md')
        elif mode in {'full', 'outline-only', 'lit-review'}:
            references.extend([
                'references/workflow_phase_details.md',
                'references/writing_quality_check.md',
                'references/failure_paths.md',
            ])
        elif mode in {'revision', 'revision-coach'}:
            references.extend([
                'agents/revision_coach_agent.md',
                'templates/revision_tracking_template.md',
            ])
        elif mode == 'citation-check':
            references.extend([
                'references/citation_format_switcher.md',
                'references/apa7_extended_guide.md',
            ])
        elif mode == 'format-convert':
            references.extend([
                'references/latex_template_reference.md',
                'references/citation_format_switcher.md',
            ])
        elif mode == 'disclosure':
            references.extend([
                'references/disclosure_mode_protocol.md',
                'references/venue_disclosure_policies.md',
            ])
        parts = [cls._read_text(path, limit=9000) for path in references]
        return '\n\n'.join(part for part in parts if part)

    @staticmethod
    def _mode_from_scene_id(scene_id):
        scene_map = {
            'academic_paper.full': 'full',
            'academic_paper.plan': 'plan',
            'academic_paper.outline': 'outline-only',
            'academic_paper.lit_review': 'lit-review',
            'academic_paper.abstract': 'abstract-only',
            'academic_paper.revision': 'revision',
            'academic_paper.revision_coach': 'revision-coach',
            'academic_paper.citation_check': 'citation-check',
            'academic_paper.format_convert': 'format-convert',
            'academic_paper.disclosure': 'disclosure',
        }
        return scene_map.get(str(scene_id or '').strip(), '')

    def run_action(self, action_id, inputs, host):
        """执行特定动作"""
        action_map = {
            'full_paper': self._run_full_paper,
            'plan_paper': self._run_plan_paper,
            'outline_only': self._run_outline_only,
            'literature_review': self._run_literature_review,
            'abstract_only': self._run_abstract_only,
            'revision': self._run_revision,
            'revision_coach': self._run_revision_coach,
            'citation_check': self._run_citation_check,
            'format_convert': self._run_format_convert,
            'disclosure': self._run_disclosure,
        }

        handler = action_map.get(action_id)
        if not handler:
            return {'error': f'unknown action: {action_id}'}

        return handler(inputs, host)

    def _get_agent_for_mode(self, mode):
        """根据模式获取对应的代理"""
        mode_agent_map = {
            'full': 'intake',
            'plan': 'socratic_mentor',
            'outline-only': 'structure_architect',
            'lit-review': 'literature_strategist',
            'abstract-only': 'abstract_bilingual',
            'revision': 'peer_reviewer',
            'revision-coach': 'revision_coach',
            'citation-check': 'citation_compliance',
            'format-convert': 'formatter',
            'disclosure': 'formatter',
        }
        return mode_agent_map.get(mode, 'intake')

    def _run_full_paper(self, inputs, host):
        """运行完整论文写作流程"""
        topic = inputs.get('topic', '')
        paper_type = inputs.get('paper_type', 'imrad')
        discipline = inputs.get('discipline', 'education')
        citation_format = inputs.get('citation_format', 'APA 7')
        word_count = inputs.get('word_count', 8000)

        prompt = f"""请作为学术论文写作助手，帮助用户完成以下论文的写作：

论文主题：{topic}
论文类型：{paper_type}
学科方向：{discipline}
引用格式：{citation_format}
目标字数：{word_count}

请按照以下流程进行：
1. 确认论文配置
2. 设计文献检索策略
3. 生成论文大纲
4. 构建论证逻辑
5. 撰写全文
6. 检查引用格式
7. 生成双语摘要
8. 进行同行评审
9. 格式化输出

请开始第一步：确认论文配置。"""

        result = host.call_llm(prompt, system=AGENT_PROMPTS['intake'])
        return {
            'action_id': 'full_paper',
            'result': result,
        }

    def _run_plan_paper(self, inputs, host):
        """运行论文规划流程"""
        topic = inputs.get('topic', '')
        materials = inputs.get('materials', '')

        prompt = f"""请作为苏格拉底导师，引导用户规划以下论文：

论文主题：{topic}
已有材料：{materials or '暂无'}

请通过提问引导用户：
1. 明确研究问题
2. 评估研究准备度
3. 设计论文结构
4. 提取核心洞见

请开始第一个问题。"""

        result = host.call_llm(prompt, system=AGENT_PROMPTS['socratic_mentor'])
        return {
            'action_id': 'plan_paper',
            'result': result,
        }

    def _run_outline_only(self, inputs, host):
        """运行仅生成大纲"""
        topic = inputs.get('topic', '')
        paper_type = inputs.get('paper_type', 'imrad')

        prompt = f"""请作为结构建筑师，为以下论文生成详细大纲：

论文主题：{topic}
论文类型：{paper_type}

请输出：
1. 论文结构选择及理由
2. 详细的章节大纲（至少3级）
3. 各章节字数分配
4. 论据映射（哪个论据支撑哪个论点）

请生成结构化的大纲。"""

        result = host.call_llm(prompt, system=AGENT_PROMPTS['structure_architect'])
        return {
            'action_id': 'outline_only',
            'result': result,
        }

    def _run_literature_review(self, inputs, host):
        """运行文献综述"""
        topic = inputs.get('topic', '')
        scope = inputs.get('scope', '')

        prompt = f"""请作为文献策略师，为以下主题设计文献检索策略：

研究主题：{topic}
检索范围：{scope or '不限'}

请输出：
1. 检索策略（关键词、布尔逻辑、数据库）
2. 筛选标准
3. 带注释的参考文献列表
4. 文献矩阵（主题×方法×发现）

请提供系统化的检索方案。"""

        result = host.call_llm(prompt, system=AGENT_PROMPTS['literature_strategist'])
        return {
            'action_id': 'literature_review',
            'result': result,
        }

    def _run_abstract_only(self, inputs, host):
        """运行仅生成摘要"""
        full_text = inputs.get('full_text', '')
        language = inputs.get('language', 'bilingual')

        prompt = f"""请作为摘要专家，为以下论文生成摘要：

论文全文：
{full_text[:3000]}...

摘要语言：{language}

请输出：
1. 中文摘要（300-500字）
2. 英文摘要（150-300词）
3. 中文关键词（5-7个）
4. 英文关键词（5-7个）

摘要应独立撰写，非机械翻译。"""

        result = host.call_llm(prompt, system=AGENT_PROMPTS['abstract_bilingual'])
        return {
            'action_id': 'abstract_only',
            'result': result,
        }

    def _run_revision(self, inputs, host):
        """运行论文修订"""
        review_comments = inputs.get('review_comments', '')
        paper_text = inputs.get('paper_text', '')

        prompt = f"""请根据评审意见修订论文草稿。

评审意见：
{review_comments or '未提供，请先做自评审并提出修订重点。'}

论文原文：
{paper_text[:6000]}

请输出：
1. 修订策略摘要
2. 分条修改后的文本或局部重写建议
3. 需要作者确认或补充的事实/数据
4. 回复评审意见的草稿"""

        result = host.call_llm(prompt, system=self._load_agent_prompt('peer_reviewer') or AGENT_PROMPTS['peer_reviewer'])
        return {
            'action_id': 'revision',
            'result': result,
        }

    def _run_revision_coach(self, inputs, host):
        """运行修订指导"""
        review_comments = inputs.get('review_comments', '')
        paper_text = inputs.get('paper_text', '')

        prompt = f"""请作为修订教练，解析以下评审意见：

评审意见：
{review_comments}

论文原文：
{paper_text[:2000] if paper_text else '未提供'}...

请输出：
1. 评论分类和优先级
2. 具体修改方案
3. 预计工作量
4. 响应信模板

请生成结构化的修订路线图。"""

        result = host.call_llm(prompt, system=AGENT_PROMPTS['revision_coach'])
        return {
            'action_id': 'revision_coach',
            'result': result,
        }

    def _run_citation_check(self, inputs, host):
        """运行引用检查"""
        paper_text = inputs.get('paper_text', '')
        citation_format = inputs.get('citation_format', 'APA 7')
        prompt = f"""请检查以下论文文本的引用合规性。

引用格式：{citation_format}

论文文本：
{paper_text[:8000]}

请输出引用审计报告，列出文内引用、参考文献、DOI、过时文献和疑似虚构引用风险。"""
        result = host.call_llm(prompt, system=self._load_agent_prompt('citation_compliance') or AGENT_PROMPTS['citation_compliance'])
        return {'action_id': 'citation_check', 'result': result}

    def _run_format_convert(self, inputs, host):
        """运行格式转换"""
        paper_text = inputs.get('paper_text', '')
        output_format = inputs.get('output_format', 'markdown')
        citation_format = inputs.get('citation_format', 'APA 7')
        prompt = f"""请将以下论文整理为目标投稿/编辑格式。

目标格式：{output_format}
引用格式：{citation_format}

论文文本：
{paper_text[:10000]}

请输出转换后的文档骨架、格式说明和需要本地工具进一步处理的文件清单。"""
        result = host.call_llm(prompt, system=self._load_agent_prompt('formatter') or AGENT_PROMPTS['formatter'])
        return {'action_id': 'format_convert', 'result': result}

    def _run_disclosure(self, inputs, host):
        """运行 AI 使用声明"""
        paper_text = inputs.get('paper_text', '')
        venue = inputs.get('venue', '')
        ai_usage = inputs.get('ai_usage', '')
        prompt = f"""请生成投稿所需的 AI 使用声明。

投稿 venue：{venue or '未指定'}
AI 使用说明：{ai_usage}

论文摘要或相关文本：
{paper_text[:4000]}

请输出可直接放入论文或投稿系统的声明，并说明建议放置位置。"""
        result = host.call_llm(prompt, system=self._load_agent_prompt('formatter') or AGENT_PROMPTS['formatter'])
        return {'action_id': 'disclosure', 'result': result}

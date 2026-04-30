class OutlineOptimizerSkill:
    def before_request(self, ctx):
        return {
            'system_append': (
                '生成论文大纲时，必须明确研究背景、研究问题、研究方法、核心发现与结论去向。'
                '输出结构需保持层级清晰，避免出现泛化标题。'
            ),
            'prompt_append': (
                '补充要求：一级标题要覆盖研究缘起、理论或方法框架、实证或分析路径、结果讨论、结论。'
                '二级标题要体现章节内部递进关系。'
            ),
            'metadata': {
                'skill': 'outline-optimizer',
                'scope': ctx.get('scope', ''),
            },
        }

    def after_response(self, ctx, text):
        return {}

    def run_action(self, action_id, inputs, host):
        if action_id != 'outline_check':
            return {'error': f'unknown action: {action_id}'}
        prompt = (
            '请以论文大纲审校助手的身份，检查以下大纲是否缺少研究问题、方法路径、章节递进和结论收束。'
            '请直接输出：1. 主要问题 2. 修改建议 3. 一个优化后的简版大纲。\n\n'
            f"研究主题：\n{inputs.get('topic', '')}\n\n"
            f"现有大纲：\n{inputs.get('outline', '')}"
        )
        result = host.call_llm(prompt, system='你是一名严谨的论文结构编辑。')
        return {
            'action_id': action_id,
            'result': result,
        }

class AbstractFocusEnhancerSkill:
    def before_request(self, ctx):
        return {
            'system_append': (
                '生成论文摘要时，必须覆盖研究目的、研究方法、结果与结论四个要素。'
                '摘要语言要凝练，避免空泛评价与背景堆砌。'
            ),
            'prompt_append': (
                '补充要求：优先保留关键数据、方法名称和结论方向。'
                '不要把摘要写成引言或结论摘要。'
            ),
            'metadata': {
                'skill': 'abstract-focus-enhancer',
                'scope': ctx.get('scope', ''),
            },
        }

    def after_response(self, ctx, text):
        return {}

    def run_action(self, action_id, inputs, host):
        if action_id != 'abstract_review':
            return {'error': f'unknown action: {action_id}'}
        prompt = (
            '请审校以下论文摘要，判断是否完整覆盖研究目的、方法、结果和结论。'
            '请输出：1. 缺失项 2. 冗余项 3. 修订建议。\n\n'
            f"学科方向：{inputs.get('discipline', '')}\n\n"
            f"摘要正文：\n{inputs.get('abstract_text', '')}"
        )
        result = host.call_llm(prompt, system='你是一名学术摘要编辑。')
        return {
            'action_id': action_id,
            'result': result,
        }

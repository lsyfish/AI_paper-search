class AcademicTonePolisherSkill:
    def before_request(self, ctx):
        return {
            'system_append': (
                '输出需要保持正式、克制、可验证的学术书面语。'
                '避免口语化表达、主观夸饰和论证跳跃。'
            ),
            'prompt_append': (
                '补充要求：术语前后一致，段落之间要有清晰衔接，'
                '不要使用宣传式、评价式或空泛结论。'
            ),
            'metadata': {
                'skill': 'academic-tone-polisher',
                'scope': ctx.get('scope', ''),
            },
        }

    def after_response(self, ctx, text):
        return {}

    def run_action(self, action_id, inputs, host):
        if action_id != 'tone_review':
            return {'error': f'unknown action: {action_id}'}
        prompt = (
            '请检查以下学术段落在语气、逻辑衔接或术语一致性方面的问题。'
            '请输出：1. 发现的问题 2. 修改建议 3. 一版修订示例。\n\n'
            f"检查重点：{inputs.get('focus', '')}\n\n"
            f"正文内容：\n{inputs.get('text', '')}"
        )
        result = host.call_llm(prompt, system='你是一名学术语言编辑。')
        return {
            'action_id': action_id,
            'result': result,
        }

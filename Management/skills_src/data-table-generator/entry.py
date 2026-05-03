class DataTableGeneratorSkill:
    def before_request(self, ctx):
        return {
            'system_append': (
                '在生成学术表格时，请遵循三线表格式（仅保留顶线、栏目线和底线）。'
                '表格内容应简洁明了，数值保留适当位数，单位统一标注。'
            ),
            'prompt_append': (
                '补充要求：表格标题应简明扼要，位于表格上方；'
                '注释说明位于表格下方，使用小号字体。'
            ),
            'metadata': {
                'skill': 'data-table-generator',
                'scope': ctx.get('scope', ''),
            },
        }

    def after_response(self, ctx, text):
        return {}

    def run_action(self, action_id, inputs, host):
        if action_id != 'generate_table':
            return {'error': f'unknown action: {action_id}'}

        table_type = inputs.get('table_type', 'descriptive')
        caption = inputs.get('caption', '')
        add_notes = inputs.get('add_notes', True)

        table_type_names = {
            'descriptive': '描述性统计表',
            'comparison': '对比分析表',
            'correlation': '相关性矩阵',
            'frequency': '频数分布表'
        }

        prompt = (
            f'请根据以下原始数据生成一个规范的学术{table_type_names.get(table_type, "表格")}。\n\n'
            f'要求：\n'
            f'1. 使用三线表格式（Markdown 表格）\n'
            f'2. 数值保留 2-3 位小数（根据实际情况）\n'
            f'3. 列标题清晰，单位统一标注\n'
            f'4. 数据对齐整齐\n'
        )

        if caption:
            prompt += f'5. 表格标题：{caption}\n'

        if add_notes:
            prompt += '6. 在表格下方添加必要的注释说明（如显著性标记、数据来源等）\n'

        prompt += f'\n原始数据：\n{inputs.get("data", "")}'

        result = host.call_llm(prompt, system='你是一名数据分析和学术写作专家，擅长制作规范的学术表格。')

        return {
            'action_id': action_id,
            'table_type': table_type,
            'result': result,
        }

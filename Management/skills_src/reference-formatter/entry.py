class ReferenceFormatterSkill:
    def before_request(self, ctx):
        return {
            'system_append': (
                '在处理参考文献时，请严格遵循指定的引用格式标准。'
                '确保作者姓名、出版年份、标题、期刊名称等要素完整且格式正确。'
            ),
            'prompt_append': (
                '补充要求：参考文献应按字母顺序或引用顺序排列，'
                '格式统一，标点符号使用规范。'
            ),
            'metadata': {
                'skill': 'reference-formatter',
                'scope': ctx.get('scope', ''),
            },
        }

    def after_response(self, ctx, text):
        return {}

    def run_action(self, action_id, inputs, host):
        if action_id == 'format_references':
            format_style = inputs.get('format_style', 'gb7714')
            check_duplicates = inputs.get('check_duplicates', True)

            format_names = {
                'gb7714': 'GB/T 7714（国标）',
                'apa': 'APA 7th',
                'mla': 'MLA 9th',
                'chicago': 'Chicago'
            }

            prompt = (
                f'请将以下参考文献列表转换为 {format_names.get(format_style, format_style)} 格式。\n'
                f'要求：\n'
                f'1. 严格遵循 {format_names.get(format_style, format_style)} 格式规范\n'
                f'2. 统一标点符号和字体样式\n'
                f'3. 按字母顺序或引用顺序排列\n'
            )

            if check_duplicates:
                prompt += '4. 检查并标记重复的文献条目\n'

            prompt += f'\n参考文献列表：\n{inputs.get("references", "")}'

            result = host.call_llm(prompt, system='你是一名专业的学术文献编辑，精通各种引用格式标准。')
            return {
                'action_id': action_id,
                'format_style': format_style,
                'result': result,
            }

        elif action_id == 'extract_doi':
            prompt = (
                '请从以下文本中提取所有 DOI 编号。\n'
                '要求：\n'
                '1. 识别所有符合 DOI 格式的编号（如 10.xxxx/xxxxx）\n'
                '2. 每行一个 DOI\n'
                '3. 去除重复项\n'
                '4. 如果没有找到 DOI，请说明\n\n'
                f'文本内容：\n{inputs.get("text", "")}'
            )

            result = host.call_llm(prompt, system='你是一名文献信息提取专家。')
            return {
                'action_id': action_id,
                'result': result,
            }

        return {'error': f'unknown action: {action_id}'}

class ResearchMethodAdvisorSkill:
    def before_request(self, ctx):
        return {
            'system_append': (
                '在讨论研究方法时，需要明确说明方法的适用场景、优势和局限性。'
                '推荐的方法应与研究问题和学科特点相匹配。'
            ),
            'prompt_append': (
                '补充要求：说明数据收集方式、样本选择策略、'
                '分析工具和预期的研究产出形式。'
            ),
            'metadata': {
                'skill': 'research-method-advisor',
                'scope': ctx.get('scope', ''),
            },
        }

    def after_response(self, ctx, text):
        return {}

    def run_action(self, action_id, inputs, host):
        if action_id != 'suggest_method':
            return {'error': f'unknown action: {action_id}'}

        discipline = inputs.get('discipline', 'education')
        research_type = inputs.get('research_type', 'mixed')

        discipline_names = {
            'education': '教育学',
            'psychology': '心理学',
            'sociology': '社会学',
            'management': '管理学',
            'computer_science': '计算机科学',
            'other': '其他'
        }

        research_type_names = {
            'quantitative': '定量研究',
            'qualitative': '定性研究',
            'mixed': '混合研究',
            'unsure': '不确定'
        }

        prompt = (
            f'作为{discipline_names.get(discipline, discipline)}领域的研究方法专家，'
            f'请针对以下研究问题提供详细的研究方法建议。\n\n'
            f'研究问题：\n{inputs.get("research_question", "")}\n\n'
            f'学科领域：{discipline_names.get(discipline, discipline)}\n'
        )

        if research_type != 'unsure':
            prompt += f'研究类型偏好：{research_type_names.get(research_type, research_type)}\n'

        prompt += (
            '\n请提供以下内容：\n'
            '1. 推荐的研究方法（如实验研究、调查研究、案例研究、行动研究等）\n'
            '2. 研究设计要点（如实验设计、抽样方法、变量控制等）\n'
            '3. 数据收集方式（如问卷、访谈、观察、文献分析等）\n'
            '4. 数据分析方法（如统计分析、内容分析、话语分析等）\n'
            '5. 推荐的分析工具或软件（如 SPSS、NVivo、Python 等）\n'
            '6. 该方法的优势和可能的局限性\n'
            '7. 研究伦理注意事项（如知情同意、隐私保护等）\n'
        )

        result = host.call_llm(
            prompt,
            system='你是一名资深的研究方法论专家，精通多种学科的研究设计和方法论。'
        )

        return {
            'action_id': action_id,
            'discipline': discipline,
            'research_type': research_type,
            'result': result,
        }

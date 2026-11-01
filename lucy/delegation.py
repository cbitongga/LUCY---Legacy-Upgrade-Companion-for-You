"""Bounded requirements decomposition. Children share the entire pinned contract."""


def plan(requirements):
    answers = requirements.get('answers', {})
    groups = [
        ('scope', 'Mission & architecture', 'architect', ['motivation', 'current_stack', 'target', 'budget']),
        ('behavior', 'Behavior & compatibility', 'differential', ['compatibility', 'approved_changes']),
        ('boundaries', 'Permissions & constraints', 'guardian', ['prohibited', 'autonomy', 'security', 'deployment', 'performance', 'reliability']),
    ]
    if answers.get('security'):
        groups[2][3].remove('security')
        groups.append(('security', 'Security requirements', 'adversarial', ['security']))
    if any(answers.get(key) for key in ('deployment', 'performance', 'reliability')):
        for key in ('deployment', 'performance', 'reliability'):
            groups[2][3].remove(key)
        groups.append(('runtime', 'Runtime & resilience', 'stability', ['deployment', 'performance', 'reliability']))
    return [{'id': key, 'name': name, 'parent_id': 'orchestrator', 'role': role, 'keys': keys,
             'objective': f'Review {name.lower()} in the context of the entire migration requirements contract. Identify gaps and conflicts; propose next tasks without executing them.',
             'depends_on': [], 'status': 'pending', 'result': None,
             'reason': 'Gather missing requirements' if any(not answers.get(k) for k in keys) else 'Review supplied constraints and cross-domain conflicts'}
            for key, name, role, keys in groups]


def merge(children, provider, model):
    reports = [child['result'] for child in children]
    report = {'summary': f"Delegated review completed {len(children)} bounded assignments. Each child received the full saved requirements contract. Findings are unverified planning advice.",
              'questions': [], 'risks': [], 'next_steps': []}
    for child in children:
        for key in ('questions', 'risks', 'next_steps'):
            report[key].extend(f"{child['name']}: {text}"[:3000] for text in child['result']['report'][key])
    for key in ('questions', 'risks', 'next_steps'):
        report[key] = list(dict.fromkeys(report[key]))[:20]
    return {'report': report, 'usage': {key: sum(r['usage'][key] for r in reports) for key in ('input_tokens', 'output_tokens')},
            'provider': provider, 'model': model}

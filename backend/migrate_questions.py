"""迁移独立题库数据到 question 表（修复空选项+编码问题）"""
from app import create_app
import json

app = create_app()
app.app_context().push()

from app.extensions import db
from app.models.question import Question
from sqlalchemy import text, func

Question.query.delete()
db.session.commit()

count = 0

def make_opts(qtype_text, r):
    """创建JSON选项，判断题返回None"""
    if qtype_text == '判断题':
        return None
    raw = [r[4], r[5], r[6], r[7]]
    labels = ['A', 'B', 'C', 'D']
    opts = [f'{labels[i]}. {v}' for i, v in enumerate(raw) if v]
    return json.dumps(opts, ensure_ascii=False) if opts else None

def safe_qtype(t):
    if t == '判断题': return 3
    if t == '单选题': return 1
    if t == '多选题': return 2
    return 1

# === subject1 ===
for r in db.session.execute(text('SELECT * FROM subject1_question')).fetchall():
    qt = (r[2] or '').strip()
    diff = min(3, max(1, (r[10] or 1)))
    q = Question(type=safe_qtype(qt), difficulty=diff, train_type=1, subject=1,
                 content=r[3] or '', image=r[9], options=make_opts(qt, r),
                 answer=r[8] or '', status=3, version=1)
    db.session.add(q); count += 1

# === subject4 ===
for r in db.session.execute(text('SELECT * FROM subject4_question')).fetchall():
    qt = (r[2] or '').strip()
    diff = min(3, max(1, (r[10] or 1)))
    q = Question(type=safe_qtype(qt), difficulty=diff, train_type=1, subject=4,
                 content=r[3] or '', image=r[9], options=make_opts(qt, r),
                 answer=r[8] or '', status=3, version=1)
    db.session.add(q); count += 1

# === professional ===
for r in db.session.execute(text('SELECT * FROM professional_question')).fetchall():
    qt = (r[2] or '').strip()
    diff = min(3, max(1, (r[10] or 1)))
    q = Question(type=safe_qtype(qt), difficulty=diff, train_type=3, subject=99,
                 content=r[3] or '', image=r[9], options=make_opts(qt, r),
                 answer=r[8] or '', status=3, version=1)
    db.session.add(q); count += 1

db.session.commit()

# Show result
for subj in [1, 4, 99]:
    result = db.session.query(Question.type, func.count()).filter(
        Question.subject == subj
    ).group_by(Question.type).all()
    tm = {1: 'single', 2: 'multiple', 3: 'judge'}
    dist = {tm.get(t, str(t)): c for t, c in result}
    print(f'subject={subj}:', dist)

print(f'Total: {Question.query.count()} questions migrated')

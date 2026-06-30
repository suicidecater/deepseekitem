# -*- coding: utf-8 -*-
"""Delete multi-choice questions from subject1_question and re-sequence question_number."""

import sys
sys.path.insert(0, '.')

from app import create_app
from app.extensions import db
from app.models.question import Subject1Question

app = create_app()
app.app_context().push()

# 1. Show before cleanup
print('=' * 60)
print('subject1_question table - BEFORE cleanup')
print('=' * 60)

total_before = Subject1Question.query.count()
type_counts = {}
for q in Subject1Question.query.all():
    t = q.question_type
    type_counts[t] = type_counts.get(t, 0) + 1

print(f'Total questions: {total_before}')
for t in ['判断题', '单选题', '多选题']:
    print(f'  {t}: {type_counts.get(t, 0)}')

# 2. Delete all multi-choice questions
multi_count = type_counts.get('多选题', 0)
if multi_count > 0:
    deleted = Subject1Question.query.filter(
        Subject1Question.question_type == '多选题'
    ).delete()
    db.session.commit()
    print(f'\nDeleted {deleted} multi-choice questions')
else:
    print('\nNo multi-choice questions to delete')

# 3. Re-sequence question_number from 1
remaining = Subject1Question.query.order_by(
    Subject1Question.question_number.asc()
).all()
print(f'Remaining questions: {len(remaining)}')

for idx, q in enumerate(remaining, start=1):
    q.question_number = idx
db.session.commit()
print(f'question_number re-sequenced (1 ~ {len(remaining)})')

# 4. Verify
print('\n' + '=' * 60)
print('subject1_question table - AFTER cleanup')
print('=' * 60)
print(f'Total: {Subject1Question.query.count()}')

for t in ['判断题', '单选题', '多选题']:
    c = Subject1Question.query.filter(
        Subject1Question.question_type == t
    ).count()
    print(f'  {t}: {c}')

# Preview first 5
print('\nFirst 5 questions:')
for q in Subject1Question.query.order_by(
    Subject1Question.question_number.asc()
).limit(5).all():
    print(f'  #{q.question_number} [{q.question_type}] {q.question_text[:50]}...')

print('\nDone!')

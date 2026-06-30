"""
题库服务：三张独立题库表（科目一/科目四/专业人员）
"""
import json
import random
from datetime import datetime, timedelta

from app.extensions import db
from app.models.question import (
    Subject1Question, Subject4Question, ProfessionalQuestion,
    ErrorQuestion, StudentQuestionMemory, QuestionService as QS
)

ERROR_TYPE_MAP = {1: '概念不清', 2: '审题失误', 3: '混淆记忆', 4: '其他'}


class QuestionService:
    """题库服务类（适配三张独立表）"""

    # ========== 数据源映射 ==========

    @staticmethod
    def _get_model(source='subject1'):
        return {'subject1': Subject1Question, 'subject4': Subject4Question, 'professional': ProfessionalQuestion}.get(source, Subject1Question)

    @staticmethod
    def _source_for_subject(subject=1):
        if subject == 1: return 'subject1'
        if subject == 4: return 'subject4'
        if subject == 5: return 'professional'
        return 'subject1'

    # ========== 题目列表 ==========

    @staticmethod
    def get_question_list(page=1, page_size=20, subject=None, q_type=None, difficulty=None, know_id=None, keyword=None):
        source = QuestionService._source_for_subject(subject) if subject else 'subject1'
        model = QuestionService._get_model(source)
        query = model.query

        if q_type is not None:
            type_str = {1: '单选题', 2: '多选题', 3: '判断题'}.get(q_type)
            if type_str:
                query = query.filter(model.question_type == type_str)
        if difficulty is not None:
            query = query.filter(model.difficulty == difficulty)
        if keyword:
            query = query.filter(model.question_text.like(f'%{keyword}%'))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return [q.to_dict() for q in items], total, page, page_size

    # ========== 开始练习 ==========

    @staticmethod
    def start_practice(student_id, subject=1, count=20, types=None, difficulty=None, know_id=None, adaptive=False):
        source = QuestionService._source_for_subject(subject)
        model = QuestionService._get_model(source)
        query = model.query

        if types and isinstance(types, list):
            type_strs = []
            for t in types:
                m = {'single': '单选题', 'multiple': '多选题', 'judge': '判断题'}.get(t)
                if m: type_strs.append(m)
            if type_strs:
                query = query.filter(model.question_type.in_(type_strs))
        if difficulty is not None:
            query = query.filter(model.difficulty == difficulty)

        all_qs = query.all()

        # 艾宾浩斯自适应
        if adaptive and len(all_qs) > count:
            memories = StudentQuestionMemory.query.filter(
                StudentQuestionMemory.student_id == student_id,
                StudentQuestionMemory.source == source,
                StudentQuestionMemory.question_id.in_([q.id for q in all_qs])
            ).all()
            mem_map = {m.question_id: m.memory_strength for m in memories}
            all_qs.sort(key=lambda q: mem_map.get(q.id, 0.5))
            selected = all_qs[:int(count * 0.7)]
            random.shuffle(selected)
            remaining = [q for q in all_qs if q not in selected]
            if remaining:
                selected += random.sample(remaining, min(count - len(selected), len(remaining)))
        elif len(all_qs) < count:
            selected = all_qs
        else:
            selected = random.sample(all_qs, count)

        question_list = [q.to_practice_dict() for q in selected]

        from app.models.exam import PracticeExam
        practice = PracticeExam(
            student_id=student_id, biz_type=1, subject=subject,
            question_ids=','.join(str(q['id']) for q in question_list), status=1,
        )
        practice.save()

        return True, '练习开始', {
            'practice_id': practice.id, 'source': source,
            'questions': question_list, 'total': len(question_list), 'subject': subject,
        }

    # ========== 提交练习答案 ==========

    @staticmethod
    def answer_practice(student_id, practice_id, question_id, user_answer, source=None):
        from app.models.exam import PracticeExam
        practice = PracticeExam.query.get(practice_id)
        if not practice or practice.student_id != student_id:
            return False, '练习记录不存在', None
        # 从记录 subject 反推 source，确保路由到正确题库表
        source = source or QuestionService._source_for_subject(practice.subject)

        model = QuestionService._get_model(source)
        question = model.query.get(question_id)
        if not question:
            return False, '题目不存在', None

        is_correct = QuestionService._check_answer(user_answer, question.correct_answer, question.question_type)

        user_answers = {}
        if practice.user_answers:
            try:
                user_answers = json.loads(practice.user_answers)
            except: pass
        user_answers[str(question_id)] = {'answer': user_answer, 'correct': is_correct}
        practice.user_answers = json.dumps(user_answers, ensure_ascii=False)
        practice.update()

        if not is_correct:
            QuestionService._add_error(student_id, question_id, source)
        QuestionService._update_memory(student_id, question_id, source, is_correct)

        return True, '答题完成', {
            'questionId': question_id, 'correct': is_correct,
            'correctAnswer': question.correct_answer,
        }

    @staticmethod
    def _check_answer(user_answer, correct_answer, q_type):
        if not user_answer or not correct_answer: return False
        ua = str(user_answer).strip().upper()
        ca = str(correct_answer).strip().upper()
        if q_type in ('多选题', 'multiple'):
            u = sorted(ua.replace(',', '').replace('，', ''))
            c = sorted(ca.replace(',', '').replace('，', ''))
            return ''.join(u) == ''.join(c)
        return ua == ca

    # ========== 开始考试 ==========

    @staticmethod
    def start_exam(student_id, subject=1, count=100):
        source = QuestionService._source_for_subject(subject)
        model = QuestionService._get_model(source)

        if subject == 1:
            judge = model.query.filter(model.question_type == '判断题').all()
            single = model.query.filter(model.question_type == '单选题').all()
            selected = []
            if len(judge) >= 40 and len(single) >= 60:
                selected = random.sample(judge, 40) + random.sample(single, 60)
            else:
                all_qs = model.query.all()
                selected = random.sample(all_qs, min(100, len(all_qs)))
        else:
            judge = model.query.filter(model.question_type == '判断题').all()
            single = model.query.filter(model.question_type == '单选题').all()
            multi = model.query.filter(model.question_type == '多选题').all()
            if len(judge) >= 20 and len(single) >= 20 and len(multi) >= 10:
                selected = random.sample(judge, 20) + random.sample(single, 20) + random.sample(multi, 10)
            else:
                all_qs = model.query.all()
                selected = random.sample(all_qs, min(50, len(all_qs)))

        random.shuffle(selected)
        question_list = [q.to_practice_dict() for q in selected]

        from app.models.exam import PracticeExam
        exam = PracticeExam(
            student_id=student_id, biz_type=2, subject=subject,
            question_ids=','.join(str(q['id']) for q in question_list),
            status=1, total_time=45 * 60,
        )
        exam.save()

        return True, '考试开始', {
            'exam_id': exam.id, 'source': source,
            'questions': question_list, 'total': len(question_list),
            'subject': subject, 'duration': 45 * 60,
        }

    # ========== 考试答题缓存 ==========

    @staticmethod
    def cache_exam_answer(student_id, exam_id, question_id, user_answer):
        from app.models.exam import PracticeExam
        exam = PracticeExam.query.get(exam_id)
        if not exam or exam.student_id != student_id or exam.biz_type != 2 or exam.status != 1:
            return False, '考试记录无效', None

        user_answers = {}
        if exam.user_answers:
            try:
                user_answers = json.loads(exam.user_answers)
            except: pass
        user_answers[str(question_id)] = user_answer
        exam.user_answers = json.dumps(user_answers, ensure_ascii=False)
        exam.update()

        total = len(exam.question_ids.split(',')) if exam.question_ids else 0
        return True, '答案已缓存', {'answeredCount': len(user_answers), 'totalCount': total}

    # ========== 交卷评分 ==========

    @staticmethod
    def submit_exam(student_id, exam_id, total_time=None, source=None):
        from app.models.exam import PracticeExam
        exam = PracticeExam.query.get(exam_id)
        if not exam or exam.student_id != student_id or exam.biz_type != 2:
            return False, '考试记录不存在', None
        source = source or QuestionService._source_for_subject(exam.subject)

        user_answers = {}
        if exam.user_answers:
            try:
                user_answers = json.loads(exam.user_answers)
            except: pass

        qids = [int(x.strip()) for x in exam.question_ids.split(',') if x.strip().isdigit()] if exam.question_ids else []

        model = QuestionService._get_model(source)
        questions = model.query.filter(model.id.in_(qids)).all()
        qmap = {q.id: q for q in questions}

        correct = 0
        dim_correct = {'交通标志': 0, '交通法规': 0, '安全常识': 0, '驾驶理论': 0}
        dim_total = {'交通标志': 0, '交通法规': 0, '安全常识': 0, '驾驶理论': 0}

        for qid in qids:
            q = qmap.get(qid)
            if not q: continue
            dim = '交通标志' if q.question_type == '判断题' else ('交通法规' if q.question_type == '单选题' else ('安全常识' if q.question_type == '多选题' else '驾驶理论'))
            dim_total[dim] += 1
            ua = user_answers.get(str(qid), '')
            if QuestionService._check_answer(ua, q.correct_answer, q.question_type):
                correct += 1
                dim_correct[dim] += 1
            else:
                QuestionService._add_error(student_id, qid, source)

        total = len(qids)
        score = round((correct / total) * 100) if total > 0 else 0

        stats = []
        for d in ['交通标志', '交通法规', '安全常识', '驾驶理论']:
            r = round((dim_correct[d] / dim_total[d]) * 100) if dim_total[d] > 0 else 0
            stats.append({'name': d, 'rate': r, 'correct': dim_correct[d], 'total': dim_total[d]})

        weak = [s for s in stats if s['rate'] < 60]
        advices = [f'重点加强{w["name"]}的学习' for w in weak] + ['建议每天坚持练习']

        exam.update(
            user_answers=json.dumps(user_answers, ensure_ascii=False),
            total_time=total_time or 0, score=score,
            correct_rate=score, status=3, end_time=datetime.now(),
        )

        return True, '交卷成功', {
            'score': score, 'correctRate': score, 'correctCount': correct,
            'wrongCount': total - correct, 'totalCount': total,
            'passed': score >= 90, 'categoryStats': stats,
            'radarData': {'dimensions': [s['name'] for s in stats],
                           'current': [s['rate'] for s in stats],
                           'baseline': [90, 90, 90, 90]},
            'weakPoints': weak, 'advices': advices,
        }

    # ========== 错题本 ==========

    @staticmethod
    def _add_error(student_id, question_id, source='subject1'):
        existing = ErrorQuestion.query.filter_by(
            student_id=student_id, question_id=question_id, source=source
        ).first()
        if existing:
            existing.error_count = (existing.error_count or 0) + 1
            existing.update()
        else:
            ErrorQuestion(student_id=student_id, question_id=question_id, source=source, error_type=4, error_count=1).save()

    @staticmethod
    def get_error_book(student_id, page=1, page_size=20, subject=None):
        query = ErrorQuestion.query.filter_by(student_id=student_id)
        if subject is not None:
            source = QuestionService._source_for_subject(subject)
            query = query.filter_by(source=source)

        query = query.order_by(ErrorQuestion.update_time.desc())
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        error_list = []
        for eq in items:
            model = QuestionService._get_model(eq.source)
            q = model.query.get(eq.question_id)
            if q:
                error_list.append({
                    'id': eq.id, 'questionId': q.id, 'source': eq.source,
                    'type': {'判断题': 'judge', '单选题': 'single', '多选题': 'multiple'}.get(q.question_type, 'single'),
                    'content': q.question_text, 'answer': q.correct_answer,
                    'options': q.get_options_list(),
                    'errorType': ERROR_TYPE_MAP.get(eq.error_type, '其他'),
                    'errorCount': eq.error_count, 'difficulty': q.difficulty,
                    'image': q.image_file,
                    'updateTime': eq.update_time.strftime('%Y-%m-%d %H:%M:%S') if eq.update_time else None,
                })

        reviewed = ErrorQuestion.query.filter(
            ErrorQuestion.student_id == student_id,
            ErrorQuestion.error_type <= 3
        ).count()
        return True, 'success', {
            'list': error_list, 'total': total, 'toReview': total - reviewed,
            'reviewed': reviewed, 'mastered': 0,
        }

    # ========== 错题复习 ==========

    @staticmethod
    def review_error_question(student_id, error_id, user_answer=None):
        eq = ErrorQuestion.query.get(error_id)
        if not eq or eq.student_id != student_id:
            return False, '错题记录不存在', None

        model = QuestionService._get_model(eq.source)
        q = model.query.get(eq.question_id)
        if not q:
            return False, '题目不存在', None

        if user_answer is not None and user_answer != '':
            is_correct = QuestionService._check_answer(user_answer, q.correct_answer, q.question_type)
            if is_correct:
                # 做对直接删除错题记录
                db.session.delete(eq)
                db.session.commit()
                return True, '回答正确，已从错题本移除', {
                    'correct': True, 'correctAnswer': q.correct_answer,
                    'removed': True,
                }
            else:
                eq.error_count = (eq.error_count or 0) + 1
                eq.update()
                return True, '复习完成', {
                    'correct': False, 'correctAnswer': q.correct_answer,
                    'errorCount': eq.error_count,
                }

        return True, 'success', {
            'errorId': error_id, 'questionId': q.id, 'source': eq.source,
            'type': {'判断题': 'judge', '单选题': 'single', '多选题': 'multiple'}.get(q.question_type, 'single'),
            'content': q.question_text, 'answer': q.correct_answer,
            'options': q.get_options_list(), 'difficulty': q.difficulty,
            'image': q.image_file,
            'errorType': ERROR_TYPE_MAP.get(eq.error_type, '其他'), 'errorCount': eq.error_count,
        }

    # ========== 艾宾浩斯记忆曲线 ==========

    @staticmethod
    def _update_memory(student_id, question_id, source, is_correct):
        mem = StudentQuestionMemory.query.filter_by(
            student_id=student_id, question_id=question_id, source=source
        ).first()
        now = datetime.now()

        if mem:
            mem.review_count = (mem.review_count or 0) + 1
            if is_correct:
                mem.memory_strength = min(1.0, (mem.memory_strength or 0.5) + 0.15)
                intervals = [1, 2, 4, 7, 15]
                mem.next_review_time = now + timedelta(days=intervals[min(mem.review_count, len(intervals)-1)])
            else:
                mem.memory_strength = max(0.1, (mem.memory_strength or 0.5) - 0.2)
                mem.next_review_time = now + timedelta(days=1)
            mem.last_review_time = now
            mem.update()
        else:
            StudentQuestionMemory(
                student_id=student_id, question_id=question_id, source=source,
                memory_strength=0.85 if is_correct else 0.5, review_count=1,
                last_review_time=now,
                next_review_time=now + timedelta(days=1 if is_correct else 1),
            ).save()

    # ========== 顺序刷题（按题号顺序遍历全部题目） ==========

    @staticmethod
    def get_sequential_questions(source='subject1'):
        """返回指定题库的全部题目，按题号升序排列（不含正确答案）"""
        model = QuestionService._get_model(source)
        if not model:
            return False, '无效的题库来源', None
        questions = model.query.order_by(model.question_number).all()
        data = [{
            'id': q.id,
            'questionNumber': q.question_number,
            'questionType': q.question_type,
            'questionText': q.question_text,
            'optionA': q.option_a,
            'optionB': q.option_b,
            'optionC': q.option_c,
            'optionD': q.option_d,
            'imageFile': q.image_file,
            'difficulty': q.difficulty,
        } for q in questions]
        return True, 'success', {
            'source': source,
            'total': len(data),
            'questions': data,
        }

    @staticmethod
    def check_sequential_answer(question_id, source='subject1', user_answer=''):
        """校验单题答案（顺序刷题用），返回正确与否 + 正确答案"""
        model = QuestionService._get_model(source)
        if not model:
            return False, '无效的题库来源', None
        q = model.query.get(question_id)
        if not q:
            return False, '题目不存在', None
        is_correct = QuestionService._check_answer(user_answer, q.correct_answer, q.question_type)
        return True, 'success', {
            'correct': is_correct,
            'correctAnswer': q.correct_answer,
        }

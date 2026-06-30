"""
学员服务

所有返回数据结构与前端 Mock handlers 对齐。
"""
import json
import random
from datetime import datetime, date, timedelta

from flask import current_app
from app.extensions import db
from sqlalchemy import func
from app.models.user import Student
from app.models.exam import Evaluation, PracticeExam
from app.models.question import Subject1Question, ErrorQuestion, Subject4Question, ProfessionalQuestion
from app.models.study import StudyPlan, AiLearningPath, AiChat
from app.models.social import Message
from app.models.system_config import SystemConfig


class StudentService:
    """学员服务类"""

    # ========== 仪表盘（聚合接口） ==========

    @staticmethod
    def get_dashboard(student_id):
        """
        获取学员仪表盘数据（与前端 MOCK_DASHBOARD 结构对齐）
        """
        student = Student.query.get(student_id)
        if not student:
            return None

        # 学员档案信息
        phone = getattr(student, 'phone', '') or ''
        if phone and len(phone) >= 11:
            phone_masked = phone[:3] + '****' + phone[-4:]
        else:
            phone_masked = phone

        # 能力评估得分（四维度）— 只查当前学习方向
        cur_subject = student.study_subject or 1
        latest_eval = Evaluation.query.filter_by(
            student_id=student_id, study_subject=cur_subject
        ).first()

        profile = {
            'name': student.name or '学员',
            'phone': phone_masked,
            'carType': (student.car_type or 'C1') + ' 小型汽车',
            'school': '安达驾校',  # Mock
            'registerDate': student.create_time.strftime('%Y-%m-%d') if student.create_time else '',
            'avatar': '',
            'progress': random.randint(30, 80),
            'studySubject': student.study_subject or 1,
            'evaluationStatus': 1 if latest_eval else 0,
        }
        if latest_eval:
            ability_scores = [
                latest_eval.sign_score or random.randint(40, 95),
                latest_eval.law_score or random.randint(40, 95),
                latest_eval.safe_score or random.randint(40, 95),
                latest_eval.drive_score or random.randint(40, 95),
            ]
        else:
            ability_scores = [0, 0, 0, 0]
        ability_baseline = [90, 90, 90, 90]

        # 今日任务（来自 StudyPlan）
        today = date.today()
        today_plans = StudyPlan.query.filter_by(
            student_id=student_id, task_date=today, study_subject=cur_subject
        ).all()
        if today_plans:
            today_tasks = [
                {
                    'id': p.id,
                    'title': p.content or '学习任务',
                    'description': '',
                    'completed': p.status == 3,
                    'type': 'practice',
                }
                for p in today_plans
            ]
        else:
            # 默认Mock任务
            today_tasks = [
                {'id': 1, 'title': '交通标志专项练习', 'description': '完成20道交通标志题', 'completed': False, 'type': 'practice'},
                {'id': 2, 'title': 'AI知识点讲解 - 交通法规', 'description': '学习关键法规条目', 'completed': False, 'type': 'ai_lesson'},
                {'id': 3, 'title': '模拟考试复盘', 'description': '回顾上次考试错题', 'completed': True, 'type': 'exam_review'},
                {'id': 4, 'title': '错题回顾 - 易错题集', 'description': '重新练习近期错题', 'completed': False, 'type': 'error_review'},
            ]

        # 知识树
        knowledge_tree = {
            'name': '交通知识树', 'value': 100,
            'children': [
                {'name': '交通标志', 'value': 40},
                {'name': '交通法规', 'value': 30},
                {'name': '安全常识', 'value': 20},
                {'name': '驾驶理论', 'value': 10},
            ]
        }

        # 统计数据
        completed_questions = PracticeExam.query.filter_by(
            student_id=student_id, biz_type=1, status=2
        ).count()
        total_questions = Subject1Question.query.count() + Subject4Question.query.count() + ProfessionalQuestion.query.count() or 300
        streak_days = random.randint(1, 14)

        return {
            'profile': profile,
            'abilityScores': ability_scores,
            'abilityBaseline': ability_baseline,
            'todayTasks': today_tasks,
            'knowledgeTree': knowledge_tree,
            'completedQuestions': completed_questions,
            'totalQuestions': total_questions,
            'streakDays': streak_days,
            'todayStudyMinutes': random.randint(0, 120),
            'daysUntilExam': random.randint(1, 30),
            'subject1Progress': random.randint(0, 100),
            'subject4Progress': random.randint(0, 80),
            'transportProgress': random.randint(0, 60),
            'totalStudents': 35,
            'quickActions': [
                {'label': '开始练习', 'icon': '✏️', 'route': '/student/practice', 'color': '#1677FF'},
                {'label': '模拟考试', 'icon': '📝', 'route': '/student/exam', 'color': '#52C41A'},
                {'label': 'AI问答', 'icon': '🤖', 'route': '/student/ai-qa', 'color': '#722ED1'},
                {'label': '错题本', 'icon': '📕', 'route': '/student/error-book', 'color': '#FA8C16'},
            ],
        }

    # ========== 个人档案 ==========

    @staticmethod
    def get_profile(student_id):
        """获取学员个人档案"""
        student = Student.query.get(student_id)
        if not student:
            return None
        return student.to_dict()

    @staticmethod
    def update_profile(student_id, data):
        """更新学员个人档案"""
        student = Student.query.get(student_id)
        if not student:
            return False, '学员不存在', None

        allowed_fields = ['name', 'phone', 'car_type', 'train_type']
        update_data = {}
        for key in allowed_fields:
            if key in data and data[key] is not None:
                update_data[key] = data[key]

        if not update_data:
            return False, '没有需要更新的字段', None

        student.update(**update_data)
        return True, '更新成功', student.to_dict()

    # ========== 能力测评 ==========

    # 四维度配置（每维度每难度抽题数）
    EVAL_DIMS = ['交通标志', '交通法规', '安全常识', '驾驶理论']
    EVAL_PER_DIM = {'diff1': 10, 'diff2': 10}

    # 题库表映射
    QUESTION_TABLES = {
        1: Subject1Question,
        4: Subject4Question,
        5: ProfessionalQuestion,
    }
    SUBJECT_NAMES = {1: '科目一', 4: '科目四', 5: '专业人员'}

    @classmethod
    def _get_question_table(cls, study_subject):
        return cls.QUESTION_TABLES.get(study_subject, Subject1Question)

    @classmethod
    def start_evaluation(cls, student_id):
        """开始能力测评：根据学习方向从对应题库四维度各抽(难度1×10+难度2×10)共80题"""
        student = Student.query.get(student_id)
        if not student:
            return False, '学员不存在', None

        direction = student.study_subject or 1
        primary_model = cls._get_question_table(direction)
        fallback_model = Subject1Question  # 兜底题库

        selected = []
        for cat_name in cls.EVAL_DIMS:
            for diff_val, count in [(1, cls.EVAL_PER_DIM['diff1']), (2, cls.EVAL_PER_DIM['diff2'])]:
                # 主题库抽取
                pool = primary_model.query.filter(
                    primary_model.category == cat_name,
                    primary_model.difficulty == diff_val
                ).limit(count * 5).all()
                picked = random.sample(pool, min(count, len(pool))) if pool else []

                # 不足时从科目一补充
                shortfall = count - len(picked)
                if shortfall > 0 and primary_model != fallback_model:
                    exclude_ids = [q.id for q in picked]
                    fb_pool = fallback_model.query.filter(
                        fallback_model.category == cat_name,
                        fallback_model.difficulty == diff_val
                    ).filter(~fallback_model.id.in_(exclude_ids)).limit(shortfall * 3).all() if exclude_ids else []
                    extra = random.sample(fb_pool, min(shortfall, len(fb_pool))) if fb_pool else []
                    picked.extend(extra)

                selected.extend(picked)

        random.shuffle(selected)

        question_list = []
        for q in selected:
            question_list.append({
                'id': q.id,
                'type': {'判断题': 'judge', '单选题': 'single', '多选题': 'multiple'}.get(q.question_type, 'single'),
                'subject': direction,
                'category': q.category,
                'content': q.question_text,
                'options': q.get_options_list(),
                'difficulty': q.difficulty,
            })

        evaluation = Evaluation(student_id=student_id, study_subject=direction, total_score=0, level='入门')
        evaluation.save()

        return True, '测评开始', {
            'evaluation_id': evaluation.id,
            'questions': question_list,
            'total': len(question_list),
            'study_subject': direction,
        }

    @classmethod
    def _load_questions_by_direction(cls, qids, study_subject):
        """根据学习方向加载题目（支持跨表查询）"""
        qids = [int(q) for q in qids]
        questions = Subject1Question.query.filter(Subject1Question.id.in_(qids)).all()
        qmap = {q.id: q for q in questions}
        if len(qmap) < len(qids) and study_subject in (4, 5):
            missing = set(qids) - set(qmap.keys())
            if study_subject == 4:
                extras = Subject4Question.query.filter(Subject4Question.id.in_(list(missing))).all()
            else:
                extras = ProfessionalQuestion.query.filter(ProfessionalQuestion.id.in_(list(missing))).all()
            for q in extras:
                qmap[q.id] = q
        return qmap

    @classmethod
    def submit_evaluation(cls, student_id, answers, total_time=0):
        """提交测评答案：按维度+难度双维度判分，返回难度分层报告"""
        if not answers or not isinstance(answers, list):
            return False, '答案数据格式不正确', None

        student = Student.query.get(student_id)
        direction = student.study_subject if student else 1

        qids = [a.get('questionId') for a in answers if a.get('questionId')]
        qmap = cls._load_questions_by_direction(qids, direction)

        # 四维度 × 两难度 = 8维打分矩阵 {dim: {diff1: [正确, 总计], diff2: [正确, 总计]}}
        dims = {cat: {'diff1': [0, 0], 'diff2': [0, 0]} for cat in cls.EVAL_DIMS}

        for q in qmap.values():
            cat = q.category or cls._infer_category(q)
            if cat not in dims:
                cat = cls._infer_category(q)
            if cat not in dims:
                continue
            diff_key = 'diff1' if q.difficulty == 1 else 'diff2'
            dims[cat][diff_key][1] += 1

        source_map = {1: 'subject1', 4: 'subject4', 5: 'professional'}
        source = source_map.get(direction, 'subject1')

        for a in answers:
            q = qmap.get(a.get('questionId'))
            if not q:
                continue
            cat = q.category or cls._infer_category(q)
            if cat not in dims:
                cat = cls._infer_category(q)
            if cat not in dims:
                continue
            diff_key = 'diff1' if q.difficulty == 1 else 'diff2'
            user_ans = str(a.get('answer', '') or '').strip().upper()
            correct_ans = str(q.correct_answer or '').strip().upper()
            if user_ans == correct_ans:
                dims[cat][diff_key][0] += 1
                a['correct'] = True
            else:
                a['correct'] = False
                # 收集到错题本
                existing = ErrorQuestion.query.filter_by(
                    student_id=student_id, question_id=q.id, source=source
                ).first()
                if existing:
                    existing.error_count = (existing.error_count or 0) + 1
                    existing.update()
                else:
                    ErrorQuestion(student_id=student_id, question_id=q.id,
                                  source=source, error_type=4, error_count=1).save()

        def _rate(c, t):
            return round((c / t) * 100) if t > 0 else 0

        # 各维度总体得分
        dim_scores = {
            cat: _rate(dims[cat]['diff1'][0] + dims[cat]['diff2'][0],
                       dims[cat]['diff1'][1] + dims[cat]['diff2'][1])
            for cat in cls.EVAL_DIMS
        }
        scores = [dim_scores[cat] for cat in cls.EVAL_DIMS]
        avg = sum(scores) / 4 if scores else 0
        level = '冲刺' if avg >= 90 else ('进阶' if avg >= 75 else ('基础' if avg >= 60 else '入门'))

        # 难度分层数据
        difficulty_breakdown = {}
        for cat in cls.EVAL_DIMS:
            difficulty_breakdown[cat] = {
                'diff1Rate': _rate(dims[cat]['diff1'][0], dims[cat]['diff1'][1]),
                'diff2Rate': _rate(dims[cat]['diff2'][0], dims[cat]['diff2'][1]),
                'diff1Correct': dims[cat]['diff1'][0],
                'diff1Total': dims[cat]['diff1'][1],
                'diff2Correct': dims[cat]['diff2'][0],
                'diff2Total': dims[cat]['diff2'][1],
            }

        # 薄弱点（维度+难度交叉）
        weak = []
        for cat in cls.EVAL_DIMS:
            cat_rate = _rate(dims[cat]['diff1'][0] + dims[cat]['diff2'][0],
                             dims[cat]['diff1'][1] + dims[cat]['diff2'][1])
            d1r = difficulty_breakdown[cat]['diff1Rate']
            d2r = difficulty_breakdown[cat]['diff2Rate']
            if d1r < 60:
                weak.append({'name': f'{cat}(简单题)', 'rate': d1r})
            if d2r < 60:
                weak.append({'name': f'{cat}(中等题)', 'rate': d2r})
        weak.sort(key=lambda x: x['rate'])

        # AI建议
        overall_d1 = _rate(sum(dims[c]['diff1'][0] for c in cls.EVAL_DIMS),
                           sum(dims[c]['diff1'][1] for c in cls.EVAL_DIMS))
        overall_d2 = _rate(sum(dims[c]['diff2'][0] for c in cls.EVAL_DIMS),
                           sum(dims[c]['diff2'][1] for c in cls.EVAL_DIMS))
        advices = []
        gap = overall_d1 - overall_d2
        if gap > 15:
            advices.append(f'中等难度题正确率比简单题低{gap}个百分点，建议加强综合分析训练')
        for w in weak[:4]:
            advices.append(f'重点加强{w["name"]}的学习，当前正确率{w["rate"]}%')
        if not advices:
            advices.append('各维度表现均衡，继续保持')
        advices.append('建议每天完成20道练习，巩固薄弱环节')

        # 更新 Evaluation 记录 — 按 (student_id, study_subject) 一对一
        total_correct = sum(dims[c]['diff1'][0] + dims[c]['diff2'][0] for c in cls.EVAL_DIMS)
        total_all = sum(dims[c]['diff1'][1] + dims[c]['diff2'][1] for c in cls.EVAL_DIMS)
        eval_record = Evaluation.query.filter_by(
            student_id=student_id, study_subject=direction
        ).first()
        if eval_record:
            eval_record.update(
                total_score=_rate(total_correct, total_all),
                sign_score=dim_scores['交通标志'],
                law_score=dim_scores['交通法规'],
                safe_score=dim_scores['安全常识'],
                drive_score=dim_scores['驾驶理论'],
                level=level,
                weak_know=json.dumps(weak, ensure_ascii=False),
                simple_rate=overall_d1,
                mid_rate=overall_d2,
                diff_detail=json.dumps(difficulty_breakdown, ensure_ascii=False),
            )

        # 标记当前方向测评已完成（不再设全局 evaluation_status）

        return True, '测评提交成功', {
            'score': _rate(total_correct, total_all),
            'correctRate': _rate(total_correct, total_all),
            'correctCount': total_correct,
            'wrongCount': total_all - total_correct,
            'totalCount': total_all,
            'radarData': {
                'dimensions': cls.EVAL_DIMS,
                'current': scores,
                'baseline': [90, 90, 90, 90],
            },
            'difficultyBreakdown': difficulty_breakdown,
            'weakPoints': weak,
            'advices': advices,
            'level': level,
            'studySubject': direction,
        }

    @classmethod
    def _infer_category(cls, q):
        """兜底：通过题型推断维度（老数据兼容）"""
        if q.question_type == '判断题':
            return '交通标志'
        elif q.question_type == '多选题':
            return '驾驶理论'
        return '交通法规'

    @classmethod
    def update_study_direction(cls, student_id, study_subject):
        """更新学习方向，返回新方向是否需要测评"""
        if study_subject not in (1, 4, 5):
            return False, '学习方向无效，可选: 1=科目一/4=科目四/5=专业人员', None
        student = Student.query.get(student_id)
        if not student:
            return False, '学员不存在', None
        student.update(study_subject=study_subject)
        # 检查新方向是否有测评记录
        has_eval = Evaluation.query.filter_by(
            student_id=student_id, study_subject=study_subject
        ).first()
        direction_names = {1: '科目一', 4: '科目四', 5: '专业人员'}
        return True, f'已切换至{direction_names[study_subject]}', {
            'studySubject': study_subject,
            'directionName': direction_names[study_subject],
            'needsEvaluation': has_eval is None,
        }

    @classmethod
    def get_evaluation_status(cls, student_id):
        """获取各方向的测评状态（1=已完成/0=未测评）"""
        student = Student.query.get(student_id)
        if not student:
            return None
        status_map = {}
        for d in [1, 4, 5]:
            ev = Evaluation.query.filter_by(
                student_id=student_id, study_subject=d
            ).first()
            status_map[str(d)] = 1 if ev else 0
        return {
            'evaluationStatusMap': status_map,
            'studySubject': student.study_subject or 1,
        }

    # ========== 学习计划 ==========

    @staticmethod
    def get_study_plan(student_id, direction=None):
        """获取学习计划（与前端 Mock 结构对齐）"""
        student = Student.query.get(student_id)
        direction = direction or (student.study_subject if student else 1)
        plans = StudyPlan.query.filter_by(student_id=student_id, study_subject=direction)\
            .order_by(StudyPlan.task_date.asc()).all()

        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

        days = []
        completed_tasks = 0
        total_tasks = 0

        for i in range(7):
            d = week_start + timedelta(days=i)
            day_plans = [p for p in plans if p.task_date == d]

            tasks = []
            for p in day_plans:
                total_tasks += 1
                if p.status == 3:
                    completed_tasks += 1
                tasks.append({
                    'id': p.id,
                    'title': p.content or '学习任务',
                    'description': '',
                    'timeSlot': 'morning',
                    'type': 'practice',
                    'completed': p.status == 3,
                    'knowledgePoint': '',
                })

            # 如果没有计划数据，使用Mock
            if not tasks and d <= today:
                mock_tasks = [
                    {'id': 100 + i * 3 + 1, 'title': '交通标志专项练习', 'description': '完成15道交通标志题',
                     'timeSlot': 'morning', 'type': 'practice', 'completed': i < 3, 'knowledgePoint': '交通标志'},
                    {'id': 100 + i * 3 + 2, 'title': 'AI知识点讲解', 'description': '学习关键法规条目',
                     'timeSlot': 'afternoon', 'type': 'ai_lesson', 'completed': i < 2, 'knowledgePoint': '交通法规'},
                    {'id': 100 + i * 3 + 3, 'title': '错题复习', 'description': '复习近期错题',
                     'timeSlot': 'evening', 'type': 'error', 'completed': i < 1},
                ]
                tasks = mock_tasks
                total_tasks += 3
                completed_tasks += (3 if i < 1 else (2 if i < 2 else (1 if i < 3 else 0)))

            days.append({
                'date': d.strftime('%m/%d'),
                'dayOfWeek': day_names[i],
                'isToday': d == today,
                'tasks': tasks,
            })

        return {
            'weekStart': week_start.strftime('%m/%d'),
            'weekEnd': week_end.strftime('%m/%d'),
            'days': days,
            'totalTasks': total_tasks,
            'completedTasks': completed_tasks,
        }

    # ========== AI学习路径（缓存版） ==========

    @staticmethod
    def get_learning_path(student_id, direction=None):
        """
        获取AI学习路径（优先缓存，测评不变不重调DeepSeek）
        direction: 不传则使用当前学习方向(1/4/5)
        返回：{ evaluationSummary, plan, cached, generatedAt }
        """
        student = Student.query.get(student_id)
        if not student:
            return None

        direction = direction or student.study_subject or 1
        latest_eval = Evaluation.query.filter_by(
            student_id=student_id, study_subject=direction
        ).first()
        if not latest_eval:
            return {
                'evaluationSummary': {
                    'hasEvaluation': False,
                    'subjectName': StudentService.SUBJECT_NAMES.get(direction, '科目一'),
                },
                'plan': None,
                'cached': False,
            }

        # 检查缓存
        cached = AiLearningPath.query.filter_by(
            student_id=student_id, study_subject=direction
        ).first()

        use_cache = cached and cached.evaluation_id == latest_eval.id
        if use_cache:
            try:
                plan_data = json.loads(cached.content)
            except (json.JSONDecodeError, TypeError):
                plan_data = None
        else:
            plan_data = None

        # 构建测评摘要
        weak_points = []
        if latest_eval.weak_know:
            try:
                weak_points = json.loads(latest_eval.weak_know) if isinstance(latest_eval.weak_know, str) else latest_eval.weak_know
            except (json.JSONDecodeError, TypeError):
                pass

        # 四维度得分字典（用于生成AI诊断）
        dim_scores_dict = {
            '交通标志': latest_eval.sign_score or 0,
            '交通法规': latest_eval.law_score or 0,
            '安全常识': latest_eval.safe_score or 0,
            '驾驶理论': latest_eval.drive_score or 0,
        }
        overall_score = latest_eval.total_score or 0

        # 规则生成AI一句话诊断
        sorted_dims = sorted(dim_scores_dict.items(), key=lambda x: x[1])
        weak_dims = [d for d, s in sorted_dims if s < 70]
        strong_dims = [d for d, s in sorted_dims if s > 85]
        advice_parts = []
        # 如果有得分<40的严重薄弱
        critical = [d for d, s in sorted_dims if s < 40]
        if critical:
            advice_parts.append(f'🔴 {"和".join(critical)}严重薄弱(低于40分)，需立即重点攻克')
        elif weak_dims:
            advice_parts.append(f'🟡 {"和".join(weak_dims)}需要加强练习')
        if overall_score < 75:
            advice_parts.append(f'综合正确率{overall_score}%，建议每天保持30分钟以上练习')
        elif overall_score >= 90:
            advice_parts.append('你已具备冲刺水平，保持模拟考试节奏')
        if strong_dims:
            advice_parts.append(f'🟢 {"和".join(strong_dims)}表现优异，可适当减少练习量')
        ai_advice = '；'.join(advice_parts) if advice_parts else '各维度表现均衡，继续保持当前学习节奏'

        # 薄弱点按正确率排序（D: 优先级排序）+ 进步空间（E）
        weak_points_sorted = sorted(weak_points, key=lambda x: x.get('rate', 0))
        for w in weak_points_sorted:
            w['potentialGain'] = max(0, 90 - w.get('rate', 0))

        eval_summary = {
            'hasEvaluation': True,
            'subjectName': StudentService.SUBJECT_NAMES.get(direction, '科目一'),
            'studySubject': direction,
            'level': latest_eval.level or '入门',
            'overallScore': overall_score,
            'dimensions': dim_scores_dict,
            'dimensionsSorted': [{'name': k, 'score': v, 'potentialGain': max(0, 90 - v)}
                                 for k, v in sorted_dims],
            'radarData': {
                'dimensions': StudentService.EVAL_DIMS,
                'current': [
                    latest_eval.sign_score or 0,
                    latest_eval.law_score or 0,
                    latest_eval.safe_score or 0,
                    latest_eval.drive_score or 0,
                ],
                'baseline': [90, 90, 90, 90],
            },
            'weakPoints': weak_points_sorted,
            'aiAdvice': ai_advice,
        }

        return {
            'evaluationSummary': eval_summary,
            'plan': plan_data,
            'cached': use_cache,
            'generatedAt': cached.generated_at.strftime('%Y-%m-%d %H:%M') if cached else None,
        }

    @staticmethod
    def generate_study_plan(student_id, exam_date=None, direction=None):
        """
        AI生成个性化学习计划（增强版DeepSeek Prompt）
        direction: 不传则使用当前学习方向(1/4/5)
        传入完整测评画像，输出7天日历任务，缓存到 ai_learning_path 表
        """
        student = Student.query.get(student_id)
        if not student:
            return False, '学员不存在', None

        direction = direction or student.study_subject or 1
        latest_eval = Evaluation.query.filter_by(
            student_id=student_id, study_subject=direction
        ).first()
        if not latest_eval:
            return False, '请先完成能力基线测评', None

        # 收集完整测评画像
        direction_name = StudentService.SUBJECT_NAMES.get(direction, '科目一')
        dim_scores = [
            latest_eval.sign_score or 0,
            latest_eval.law_score or 0,
            latest_eval.safe_score or 0,
            latest_eval.drive_score or 0,
        ]
        avg_score = sum(dim_scores) / 4 if dim_scores else 0
        level = latest_eval.level or '入门'

        weak_know = []
        if latest_eval.weak_know:
            try:
                weak_know = json.loads(latest_eval.weak_know) if isinstance(latest_eval.weak_know, str) else latest_eval.weak_know
            except (json.JSONDecodeError, TypeError):
                pass

        # 构建丰富上下文给DeepSeek
        profile_lines = [
            f'学习方向：{direction_name}',
            f'能力等级：{level}',
            f'综合正确率：{int(avg_score)}%',
            f'四维度得分：交通标志{latest_eval.sign_score or 0}分、交通法规{latest_eval.law_score or 0}分、安全常识{latest_eval.safe_score or 0}分、驾驶理论{latest_eval.drive_score or 0}分',
            f'薄弱知识点：' + '；'.join([f'{w.get("name", "")}({w.get("rate", 0)}%)' for w in weak_know]) if weak_know else '无明显薄弱项',
            f'考试日期：{exam_date or "未设置"}',
        ]
        profile_text = '\n'.join(profile_lines)

        # 调用DeepSeek
        import requests
        api_key = SystemConfig.get_value('deepseek_api_key', '') or current_app.config.get('DEEPSEEK_API_KEY', '')
        if not api_key:
            return False, '管理员尚未配置AI服务，请联系管理员设置DeepSeek API Key', None

        base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')

        payload = {
            'model': current_app.config.get('DEEPSEEK_MODEL', 'deepseek-chat'),
            'messages': [{
                'role': 'system',
                'content': (
                    '你是驾考学习规划专家。平台提供以下6个功能模块，生成的学习任务必须全部关联这些功能：\n\n'
                    '【平台功能模块 - type只能从以下6种中选取】\n'
                    '1. AI交规问答 (type=ai_qa)           → AI大模型答疑解惑，适合概念理解和法规问答\n'
                    '2. 智能题库练习 (type=practice)       → 按知识点刷题练习，适合日常积累和巩固\n'
                    '3. 模拟考试 (type=exam)               → 全真模拟考试环境，适合检测真实水平\n'
                    '4. 错题本复习 (type=error_book)       → 复习历史错题集，适合查漏补缺\n'
                    '5. 专项训练 (type=special_training)   → 薄弱知识点精准突破，适合短板强化\n'
                    '6. 场景模拟 (type=scene_sim)          → 交通场景实操模拟，适合实际应用\n\n'
                    '【安排原则】\n'
                    '1. 薄弱知识点优先安排"专项训练"和"错题本复习"（第1-3天）\n'
                    '2. 得分<70的维度每天至少安排1个"智能题库练习"或"专项训练"\n'
                    '3. 得分>85的维度减少练习量，改为"场景模拟"或"AI交规问答"\n'
                    '4. 每3天安排一次"模拟考试"，并在次日安排"错题本复习"\n'
                    '5. 每天安排1次"AI交规问答"，用于答疑解惑和概念理解\n'
                    '6. 每周安排1-2次"场景模拟"，增强实际应用能力\n'
                    '7. 每天morning/afternoon/evening各1个任务，一共3个\n'
                    '8. estimatedMinutes在20-60之间\n'
                    '9. title用中文描述具体做什么，体现对应功能名称\n'
                    '10. 任务标题禁止包含"简单题"、"中等题"、"难题"、"易"、"困难"等难度描述，统一用"专项练习"、"综合练习"、"巩固训练"等中性表述\n'
                    '11. 只返回纯JSON数组，不要任何解释文字和代码块标记'
                )
            }, {
                'role': 'user',
                'content': (
                    f'{profile_text}\n\n'
                    '请根据上述6个功能模块，生成完整的7天个性化学习计划（JSON数组）。\n'
                    'JSON格式示例：[{"day":1,"date":"MM/DD","tasks":['
                    '{"timeSlot":"morning","title":"任务标题","type":"practice","completed":false,"estimatedMinutes":30}'
                    ']}]...共7天。\n'
                    'type只能是ai_qa/practice/exam/error_book/special_training/scene_sim之一。\n'
                    '只返回JSON数组，不要任何额外内容。'
                )
            }],
            'temperature': 0.5,
            'stream': False,
        }

        try:
            resp = requests.post(
                f'{base_url}/chat/completions',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json=payload, timeout=60
            )
            if resp.status_code != 200:
                return False, f'AI服务异常: {resp.status_code}', None

            ai_text = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            # 清理markdown包裹
            ai_text = ai_text.strip()
            if ai_text.startswith('```'):
                ai_text = ai_text.split('\n', 1)[-1]
                if ai_text.endswith('```'):
                    ai_text = ai_text[:-3]
            plan_days = json.loads(ai_text) if ai_text else []
            # 重写AI幻觉日期为真实日期（从今天起连续7天）
            today = date.today()
            for i, day in enumerate(plan_days):
                real_date = today + timedelta(days=i)
                day['date'] = real_date.strftime('%m/%d')
                day['day'] = i + 1
        except Exception as e:
            current_app.logger.warning(f'DeepSeek学习路径生成失败: {e}，使用基础计划')
            today = date.today()
            # 6种功能类型均匀分布的7天备选计划
            fallback_tasks = [
                # 第1天：薄弱专项训练 + 练习 + AI问答
                [
                    {'timeSlot': 'morning', 'title': '薄弱知识点专项训练', 'type': 'special_training', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'afternoon', 'title': '智能题库分类练习', 'type': 'practice', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'evening', 'title': 'AI交规答疑 - 今日薄弱点', 'type': 'ai_qa', 'completed': False, 'estimatedMinutes': 20},
                ],
                # 第2天：错题本复习 + 练习 + 场景模拟
                [
                    {'timeSlot': 'morning', 'title': '错题本集中复习', 'type': 'error_book', 'completed': False, 'estimatedMinutes': 25},
                    {'timeSlot': 'afternoon', 'title': '知识点系统练习', 'type': 'practice', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'evening', 'title': '交通场景模拟驾驶', 'type': 'scene_sim', 'completed': False, 'estimatedMinutes': 30},
                ],
                # 第3天：模拟考试 + 错题复盘 + AI问答
                [
                    {'timeSlot': 'morning', 'title': '全真模拟考试', 'type': 'exam', 'completed': False, 'estimatedMinutes': 45},
                    {'timeSlot': 'afternoon', 'title': '考试错题针对性复盘', 'type': 'error_book', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'evening', 'title': 'AI交规答疑 - 考试错题解析', 'type': 'ai_qa', 'completed': False, 'estimatedMinutes': 20},
                ],
                # 第4天：专项训练 + 练习 + AI问答
                [
                    {'timeSlot': 'morning', 'title': '高频易错专项训练', 'type': 'special_training', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'afternoon', 'title': '智能题库综合练习', 'type': 'practice', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'evening', 'title': 'AI交规问答 - 法规难点解答', 'type': 'ai_qa', 'completed': False, 'estimatedMinutes': 20},
                ],
                # 第5天：错题本 + 练习 + 场景模拟
                [
                    {'timeSlot': 'morning', 'title': '错题本二次复习', 'type': 'error_book', 'completed': False, 'estimatedMinutes': 25},
                    {'timeSlot': 'afternoon', 'title': '智能题库限时练习', 'type': 'practice', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'evening', 'title': '交通场景实操模拟', 'type': 'scene_sim', 'completed': False, 'estimatedMinutes': 30},
                ],
                # 第6天：模拟考试 + 错题复盘 + AI问答
                [
                    {'timeSlot': 'morning', 'title': '全真模拟考试（第二场）', 'type': 'exam', 'completed': False, 'estimatedMinutes': 45},
                    {'timeSlot': 'afternoon', 'title': '考试错题复盘分析', 'type': 'error_book', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'evening', 'title': 'AI交规答疑 - 考前冲刺问答', 'type': 'ai_qa', 'completed': False, 'estimatedMinutes': 20},
                ],
                # 第7天：综合回顾 + 专项训练
                [
                    {'timeSlot': 'morning', 'title': '本周综合知识回顾', 'type': 'practice', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'afternoon', 'title': '薄弱项最终冲刺训练', 'type': 'special_training', 'completed': False, 'estimatedMinutes': 30},
                    {'timeSlot': 'evening', 'title': 'AI交规总结 - 考前要点梳理', 'type': 'ai_qa', 'completed': False, 'estimatedMinutes': 20},
                ],
            ]
            plan_days = []
            for i in range(7):
                d = today + timedelta(days=i)
                plan_days.append({
                    'day': i + 1, 'date': d.strftime('%m/%d'),
                    'tasks': fallback_tasks[i],
                })

        today = date.today()

        # 1. 写入 ai_learning_path 缓存表
        plan_json = json.dumps(plan_days, ensure_ascii=False)
        cached = AiLearningPath.query.filter_by(
            student_id=student_id, study_subject=direction
        ).first()
        if cached:
            cached.update(content=plan_json, evaluation_id=latest_eval.id, generated_at=datetime.now())
        else:
            AiLearningPath(
                student_id=student_id, study_subject=direction,
                evaluation_id=latest_eval.id, content=plan_json
            ).save()

        # 2. 写入 study_plan 每日任务表（只清当前方向的旧任务）
        StudyPlan.query.filter_by(student_id=student_id, plan_type=2, study_subject=direction).delete()
        for day_data in plan_days:
            day_offset = day_data.get('day', 1) - 1
            task_date = today + timedelta(days=day_offset)
            for task in day_data.get('tasks', []):
                StudyPlan(
                    student_id=student_id, plan_type=2, study_subject=direction,
                    content=task.get('title', ''), task_date=task_date, status=1,
                ).save()

        return True, '学习计划生成成功', {
            'exam_date': exam_date,
            'weekStart': today.strftime('%m/%d'),
            'weekEnd': (today + timedelta(days=6)).strftime('%m/%d'),
            'days': plan_days,
            'totalTasks': sum(len(d.get('tasks', [])) for d in plan_days),
            'generatedAt': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }

    # ========== 学习进度 ==========

    @staticmethod
    def get_progress(student_id, direction=None):
        """获取真实学习进度（聚合6大功能模块数据）
        direction: 不传则使用当前学习方向(1/4/5)
        """
        student = Student.query.get(student_id)
        if not student:
            return None

        direction = direction or student.study_subject or 1

        # 1. 统计卡：全部真实数据
        # 学习天数（有学习记录的不同日期数）
        total_days = db.session.query(func.count(func.distinct(
            func.date(PracticeExam.create_time)
        ))).filter(
            PracticeExam.student_id == student_id
        ).scalar() or 0

        # 做题总数（所有 biz_type）
        total_questions = PracticeExam.query.filter_by(
            student_id=student_id
        ).count()

        # 练习正确率（biz_type=1）
        practices = PracticeExam.query.filter_by(
            student_id=student_id, biz_type=1, status=2
        ).all()
        accuracy = round(
            sum(float(p.correct_rate or 0) for p in practices) / len(practices), 1
        ) if practices else 0

        # 模拟考试（biz_type=2）
        exams = PracticeExam.query.filter_by(
            student_id=student_id, biz_type=2, status=2
        ).all()
        exam_count = len(exams)
        exam_best = max((int(p.total_score or 0) for p in exams), default=0)

        # 错题总数
        error_count = ErrorQuestion.query.filter_by(
            student_id=student_id
        ).count()

        # AI问答次数
        ai_chat_count = AiChat.query.filter_by(
            student_id=student_id, is_deleted=0
        ).count()

        # 2. 能力矩阵：从测评表取该方向真实分数
        latest_eval = Evaluation.query.filter_by(
            student_id=student_id, study_subject=direction
        ).first()
        if latest_eval:
            dim_scores_sorted = sorted([
                {'name': '交通标志', 'score': latest_eval.sign_score or 0},
                {'name': '交通法规', 'score': latest_eval.law_score or 0},
                {'name': '安全常识', 'score': latest_eval.safe_score or 0},
                {'name': '驾驶理论', 'score': latest_eval.drive_score or 0},
            ], key=lambda x: x['score'])
        else:
            dim_scores_sorted = [{'name': d, 'score': 0}
                                 for d in ['交通标志', '交通法规', '安全常识', '驾驶理论']]

        # 3. 本周趋势：近7天每日做题数
        week_trend = []
        today = date.today()
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            day_count = PracticeExam.query.filter(
                PracticeExam.student_id == student_id,
                func.date(PracticeExam.create_time) == d
            ).count()
            day_practices = PracticeExam.query.filter(
                PracticeExam.student_id == student_id,
                PracticeExam.biz_type == 1,
                PracticeExam.status == 2,
                func.date(PracticeExam.create_time) == d
            ).all()
            day_acc = round(
                sum(float(p.correct_rate or 0) for p in day_practices) / len(day_practices), 1
            ) if day_practices else 0
            week_trend.append({
                'date': d.strftime('%m/%d'),
                'questions': day_count,
                'accuracy': day_acc,
            })

        # 4. 6大模块完成进度（点击可跳转对应功能）
        practice_done = PracticeExam.query.filter_by(
            student_id=student_id, biz_type=1, status=2
        ).count()
        exam_done = exam_count
        error_done = error_count
        ai_done = ai_chat_count
        special_done = PracticeExam.query.filter_by(
            student_id=student_id, biz_type=3, status=2
        ).count()
        scene_done = PracticeExam.query.filter_by(
            student_id=student_id, biz_type=4, status=2
        ).count()

        module_progress = [
            {'name': '智能题库', 'type': 'practice', 'done': practice_done, 'target': 500,
             'route': '/student/practice', 'color': '#1677FF', 'icon': '📝'},
            {'name': '模拟考试', 'type': 'exam', 'done': exam_done, 'target': 10,
             'route': '/student/exam', 'color': '#FA8C16', 'icon': '📋'},
            {'name': '错题本', 'type': 'error_book', 'done': error_done, 'target': 200,
             'route': '/student/error-book', 'color': '#FF4D4F', 'icon': '📕'},
            {'name': 'AI问答', 'type': 'ai_qa', 'done': ai_done, 'target': 50,
             'route': '/student/ai-qa', 'color': '#722ED1', 'icon': '🤖'},
            {'name': '专项训练', 'type': 'special_training', 'done': special_done, 'target': 200,
             'route': '/student/special-training', 'color': '#13C2C2', 'icon': '🎯'},
            {'name': '场景模拟', 'type': 'scene_sim', 'done': scene_done, 'target': 20,
             'route': '/student/scene-sim', 'color': '#52C41A', 'icon': '🎮'},
        ]

        # 5. 热力图：近12周真实学习记录
        heatmap_cells = []
        for w in range(11, -1, -1):
            week_end_date = today - timedelta(weeks=w)
            week_start_date = week_end_date - timedelta(days=6)
            week_count = PracticeExam.query.filter(
                PracticeExam.student_id == student_id,
                func.date(PracticeExam.create_time) >= week_start_date,
                func.date(PracticeExam.create_time) <= week_end_date,
            ).count()
            minutes = week_count * 2
            if minutes > 120:
                level = 4
            elif minutes > 90:
                level = 3
            elif minutes > 60:
                level = 2
            elif minutes > 30:
                level = 1
            else:
                level = 0
            heatmap_cells.append({
                'date': week_end_date.strftime('%m/%d'),
                'minutes': minutes, 'level': level,
            })

        return {
            'stats': {
                'totalDays': total_days,
                'totalQuestions': total_questions,
                'accuracy': accuracy,
                'examCount': exam_count,
                'examBest': exam_best,
                'errorCount': error_count,
                'aiChatCount': ai_chat_count,
            },
            'dimensions': dim_scores_sorted,
            'weekTrend': week_trend,
            'moduleProgress': module_progress,
            'heatmapCells': heatmap_cells,
        }

    # ========== 评估报告 ==========

    @staticmethod
    def get_report(student_id, direction=None):
        """获取学员评估报告：包含雷达图、薄弱项、难度分层、成长曲线"""
        student = Student.query.get(student_id)
        if not student:
            return None

        direction = direction or student.study_subject or 1
        latest_eval = Evaluation.query.filter_by(
            student_id=student_id, study_subject=direction
        ).first()

        if not latest_eval:
            # 未测评：返回空报告结构
            return {
                'subjectName': StudentService.SUBJECT_NAMES.get(direction, '科目一'),
                'studySubject': direction,
                'hasEvaluation': False,
                'overallScore': 0,
                'overallLevel': '未测评',
                'radarData': None,
                'weakPoints': [],
                'difficultyBreakdown': None,
                'growthCurve': [],
                'examHistory': [],
                'aiAdvices': ['请先完成能力基线测评，系统将根据你的薄弱项给出针对性建议'],
            }

        # 基础数据
        overall_score = latest_eval.total_score or 0
        if overall_score >= 90:
            overall_level = '冲刺水平'
        elif overall_score >= 75:
            overall_level = '进阶水平'
        elif overall_score >= 60:
            overall_level = '基础水平'
        else:
            overall_level = '入门水平'

        # 四维雷达数据
        dim_scores = [
            latest_eval.sign_score or 0,
            latest_eval.law_score or 0,
            latest_eval.safe_score or 0,
            latest_eval.drive_score or 0,
        ]
        radar_data = {
            'dimensions': StudentService.EVAL_DIMS,
            'current': dim_scores,
            'baseline': [90, 90, 90, 90],
        }

        # 薄弱知识点
        weak_points = []
        if latest_eval.weak_know:
            try:
                weak_points = json.loads(latest_eval.weak_know) if isinstance(latest_eval.weak_know, str) else latest_eval.weak_know
            except (json.JSONDecodeError, TypeError):
                pass

        # 难度分层（优先从数据库真实数据，无数据时用 diff_detail 反推）
        if latest_eval.simple_rate or latest_eval.mid_rate:
            difficulty_breakdown = {
                '简单题': latest_eval.simple_rate or 0,
                '中等题': latest_eval.mid_rate or 0,
            }
        elif latest_eval.diff_detail:
            try:
                detail = json.loads(latest_eval.diff_detail) if isinstance(latest_eval.diff_detail, str) else latest_eval.diff_detail
                d1_correct = sum(detail[c]['diff1Correct'] for c in detail)
                d1_total = sum(detail[c]['diff1Total'] for c in detail)
                d2_correct = sum(detail[c]['diff2Correct'] for c in detail)
                d2_total = sum(detail[c]['diff2Total'] for c in detail)
                difficulty_breakdown = {
                    '简单题': round(d1_correct / d1_total * 100) if d1_total > 0 else 0,
                    '中等题': round(d2_correct / d2_total * 100) if d2_total > 0 else 0,
                }
            except (json.JSONDecodeError, TypeError, KeyError):
                difficulty_breakdown = {}
        else:
            difficulty_breakdown = {}

        # 成长曲线：最近20条有效测评记录
        growth_curve = []
        all_evals = Evaluation.query.filter_by(student_id=student_id)\
            .filter(Evaluation.total_score > 0)\
            .order_by(Evaluation.create_time.asc()).limit(20).all()
        for ev in all_evals:
            growth_curve.append({
                'date': ev.create_time.strftime('%m/%d') if ev.create_time else '',
                'subject': StudentService.SUBJECT_NAMES.get(ev.study_subject, ''),
                'scores': [ev.sign_score or 0, ev.law_score or 0, ev.safe_score or 0, ev.drive_score or 0],
            })

        # 考试历史：最近10条有效记录，最新在前
        exam_history = []
        recent_exams = Evaluation.query.filter_by(student_id=student_id)\
            .filter(Evaluation.total_score > 0)\
            .order_by(Evaluation.create_time.desc()).limit(10).all()
        for ev in recent_exams:
            exam_history.append({
                'date': ev.create_time.strftime('%m-%d') if ev.create_time else '',
                'score': ev.total_score,
                'passed': ev.total_score >= 90,
                'subject': StudentService.SUBJECT_NAMES.get(ev.study_subject, ''),
            })

        # AI建议（基于薄弱项动态生成）
        ai_advices = []
        for w in weak_points[:3]:
            ai_advices.append(f'重点加强{w.get("name", "薄弱项")}的学习，当前正确率{w.get("rate", 0)}%')
        if not ai_advices:
            ai_advices.append('各维度表现均衡，继续保持当前学习节奏')
        if overall_score < 90:
            ai_advices.append('建议每天完成20道专项练习，巩固薄弱环节')
            ai_advices.append('每周至少进行2次模拟考试，适应考试节奏')

        return {
            'subjectName': StudentService.SUBJECT_NAMES.get(direction, '科目一'),
            'studySubject': direction,
            'hasEvaluation': True,
            'overallScore': overall_score,
            'overallLevel': overall_level,
            'radarData': radar_data,
            'weakPoints': weak_points,
            'difficultyBreakdown': difficulty_breakdown,
            'growthCurve': growth_curve,
            'examHistory': exam_history,
            'aiAdvices': ai_advices,
        }

    # ========== 消息 ==========

    @staticmethod
    def get_messages(student_id, page=1, page_size=20):
        """获取学员消息列表（支持分页）"""
        query = Message.query.filter_by(
            receive_type=1, receive_id=student_id
        ).filter(Message.status.in_([1, 2])).order_by(Message.create_time.desc())

        total = query.count()
        messages = query.offset((page - 1) * page_size).limit(page_size).all()

        return [m.to_dict() for m in messages], total

"""
CMS API蓝图 - 题库管理（三张独立表）+ API配置

所有端点需 JWT认证 + admin角色校验。
"""
from flask import Blueprint, request, g

from app.middleware.auth import jwt_required_with_user
from app.middleware.rbac import role_required
from app.utils.response import success, error, paginated_response
from app.models.question import Subject1Question, Subject4Question, ProfessionalQuestion

cms_bp = Blueprint('cms', __name__)

# 合法的 source 值 -> 对应模型
SOURCE_MODELS = {
    'subject1': Subject1Question,
    'subject4': Subject4Question,
    'professional': ProfessionalQuestion,
}

SOURCE_LABELS = {
    'subject1': '科目一',
    'subject4': '科目四',
    'professional': '专业人员',
}


def _get_model(source):
    """根据 source 返回对应的题库模型，非法则返回 None"""
    return SOURCE_MODELS.get(source)


# ========== 题库管理：列表 ==========

@cms_bp.route('/questions/<source>', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def get_questions(source):
    """
    GET /api/cms/questions/{source}?page=1&page_size=20&type=&keyword=
    source: subject1 | subject4 | professional
    """
    Model = _get_model(source)
    if not Model:
        return error(40001, f'无效的题库来源，可选: {", ".join(SOURCE_MODELS.keys())}')

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    q_type = request.args.get('type', '').strip()
    keyword = request.args.get('keyword', '').strip()

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    query = Model.query

    if q_type:
        query = query.filter(Model.question_type == q_type)
    if keyword:
        query = query.filter(Model.question_text.contains(keyword))

    query = query.order_by(Model.question_number.asc())

    total = query.count()
    questions = query.offset((page - 1) * page_size).limit(page_size).all()

    return paginated_response(
        [q.to_dict(include_answer=True) for q in questions],
        total, page, page_size,
    )


# ========== 题库管理：单题详情 ==========

@cms_bp.route('/questions/<source>/<int:question_id>', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def get_question_detail(source, question_id):
    """GET /api/cms/questions/{source}/{id}"""
    Model = _get_model(source)
    if not Model:
        return error(40001, '无效的题库来源')

    question = Model.query.get(question_id)
    if not question:
        return error(404, '题目不存在')

    return success(question.to_dict(include_answer=True))


# ========== 题库管理：新增题目 ==========

@cms_bp.route('/questions/<source>', methods=['POST'])
@jwt_required_with_user()
@role_required('admin')
def create_question(source):
    """
    POST /api/cms/questions/{source}
    Body: {
        "questionType": "判断题",
        "questionText": "题干",
        "optionA": "A选项", "optionB": "...", "optionC": "...", "optionD": "...",
        "correctAnswer": "A",
        "imageFile": null, "difficulty": 1
    }
    """
    Model = _get_model(source)
    if not Model:
        return error(40001, '无效的题库来源')

    data = request.get_json() or {}

    required_fields = ['questionType', 'questionText', 'correctAnswer']
    for field in required_fields:
        if not data.get(field):
            return error(40001, f'缺少必填字段: {field}')

    # 自动生成题号（当前最大题号+1）
    max_num = Model.query.order_by(Model.question_number.desc()).first()
    question_number = (max_num.question_number + 1) if max_num else 1

    question = Model(
        question_number=question_number,
        question_type=data['questionType'],
        question_text=data['questionText'],
        option_a=data.get('optionA', ''),
        option_b=data.get('optionB', ''),
        option_c=data.get('optionC', ''),
        option_d=data.get('optionD', ''),
        correct_answer=data['correctAnswer'],
        image_file=data.get('imageFile', None),
        difficulty=data.get('difficulty', 1),
    )
    question.save()

    return success(question.to_dict(include_answer=True), message='题目创建成功')


# ========== 题库管理：更新题目 ==========

@cms_bp.route('/questions/<source>/<int:question_id>', methods=['PUT'])
@jwt_required_with_user()
@role_required('admin')
def update_question(source, question_id):
    """PUT /api/cms/questions/{source}/{id}"""
    Model = _get_model(source)
    if not Model:
        return error(40001, '无效的题库来源')

    question = Model.query.get(question_id)
    if not question:
        return error(404, '题目不存在')

    data = request.get_json() or {}
    updatable_fields = ['questionType', 'questionText', 'optionA', 'optionB', 'optionC', 'optionD',
                        'correctAnswer', 'imageFile', 'difficulty', 'questionNumber']

    # 字段名映射（前端 camelCase -> 数据库字段）
    field_map = {
        'questionType': 'question_type',
        'questionText': 'question_text',
        'optionA': 'option_a',
        'optionB': 'option_b',
        'optionC': 'option_c',
        'optionD': 'option_d',
        'correctAnswer': 'correct_answer',
        'imageFile': 'image_file',
        'difficulty': 'difficulty',
        'questionNumber': 'question_number',
    }

    update_data = {}
    for camel_field in updatable_fields:
        if camel_field in data:
            db_field = field_map[camel_field]
            update_data[db_field] = data[camel_field]

    if update_data:
        question.update(**update_data)

    return success(question.to_dict(include_answer=True), message='题目更新成功')


# ========== 题库管理：删除题目（物理删除） ==========

@cms_bp.route('/questions/<source>/<int:question_id>', methods=['DELETE'])
@jwt_required_with_user()
@role_required('admin')
def delete_question(source, question_id):
    """DELETE /api/cms/questions/{source}/{id}"""
    Model = _get_model(source)
    if not Model:
        return error(40001, '无效的题库来源')

    question = Model.query.get(question_id)
    if not question:
        return error(404, '题目不存在')

    question.delete()
    return success(message='题目已删除')


# ========== CMS API配置 ==========

from app.models.system_config import SystemConfig


@cms_bp.route('/api-config', methods=['GET'])
@jwt_required_with_user()
@role_required('admin')
def get_api_config():
    """GET /api/cms/api-config"""
    keys = ['deepseek_api_key', 'qq_email_address']
    configs = {}
    for key in keys:
        value = SystemConfig.get_value(key, '')
        masked = ''
        if value and len(value) > 8:
            masked = value[:4] + '****' + value[-4:]
        elif value:
            masked = value[:2] + '****'
        configs[key] = {
            'key': key,
            'value': masked,
            'is_set': bool(value),
            'has_value': bool(value),
        }

    return success({'configs': configs})


@cms_bp.route('/api-config', methods=['POST'])
@jwt_required_with_user()
@role_required('admin')
def save_api_config():
    """POST /api/cms/api-config"""
    data = request.get_json() or {}
    allowed_keys = ['deepseek_api_key', 'qq_email_address']

    updated = []
    for key in allowed_keys:
        if key in data:
            description_map = {
                'deepseek_api_key': 'DeepSeek API密钥',
                'qq_email_address': 'QQ邮箱发件地址',
            }
            SystemConfig.set_value(
                key=key,
                value=str(data[key]) if data[key] else '',
                description=description_map.get(key, ''),
                updated_by=g.user_id,
            )
            updated.append(key)

    if not updated:
        return error(40001, '未提供有效的配置项')

    return success({'updated': updated}, message='API配置保存成功')

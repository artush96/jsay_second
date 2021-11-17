from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListAPIView
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.core.models import Questions, LegalDocs, Benefit, Advices, Tariffs
from .serializers import QuestionsSerializer, LegalDocsSerializer, \
    BenefitSerializer, AdvicesSerializer, TariffsSerializer


# Get feedback questions
class QuestionsListView(ListAPIView):
    """
    @api {get} core/get_questions/ Варианты вопросов
    @apiSuccessExample {json} Success-Response:
    [
        {
            "id": 1,
            "question": "Дорого"
        },
        {
            "id": 2,
            "question": "Непонятно"
        },
        {
            "id": 3,
            "question": "Неудобно"
        },
        {
            "id": 4,
            "question": "Работает неправильно"
        }
    ]
    @apiVersion 1.0.0
    @apiHeader {String} Authorization User Bearer Token.
    @apiPermission User
    @apiName get_questions
    @apiGroup Отзывы

    @apiSuccess {Number} id ID вопроса
    @apiSuccess {String} question Название вопроса
    """
    permission_classes = [IsAuthenticated]
    serializer_class = QuestionsSerializer
    queryset = Questions.objects.all()


# Get Legal Docs
@csrf_exempt
@api_view(['GET'])
@permission_classes((AllowAny,))
def legal_docs(request):
    """
    @api {get} core/legal_docs/ Правовые документы
    @apiSuccessExample {json} Success-Response:
    {
        "policy": "Политика конфиденциальности – по сути документ, при помощи которого вы объясняете вашим
        пользователям то, как вы обрабатываете его данные. Часто встречается и другое (официальное) название
        данного документа - Политика обработки персональных данных.",
        "terms": "Условия использования, условия предоставления услуг (англ. Terms of service/use) — это правила,
        с которыми нужно согласиться перед использованием какой-либо службы, чаще всего в интернете."
    }
    @apiVersion 1.0.0
    @apiName get_questions
    @apiGroup Основные

    @apiSuccess {String} policy Политика конфиденциальности
    @apiSuccess {String} terms Условия использования
    """
    qs = LegalDocs.objects.first()
    data = LegalDocsSerializer(qs)
    return Response(data.data)


# Get Advices
class AdvicesListView(ListAPIView):
    """
    @api {get} core/advices/ Советы
    @apiSuccessExample {json} Success-Response:
    [
        {
            "title": "Лучше ЭТО сделать заранее",
            "text": "Распределяйте объем воды в течение дня и не полагайтесь на жажду.",
            "link": "https://www.nytimes.com/2000/07/11/health/personal-health.html",
            "short_link": "https://nytimes.com"
        },
        {
            "title": "Упс, вы что-то упустили...",
            "text": "Когда чувствуете жажду — организм уже слегка обезвожен.",
            "link": "https://www.nytimes.com/2000/07/11/health/personal-health-for-lifelong.html",
            "short_link": "https://nytimes.com"
        }
    ]
    @apiVersion 1.0.0
    @apiName advices
    @apiGroup Основные

    @apiSuccess {String} title Заголовок
    @apiSuccess {String} text Текст
    @apiSuccess {String} link Ссылка на источник
    @apiSuccess {String} short_link Краткая ссылка
    """
    permission_classes = [AllowAny]
    serializer_class = AdvicesSerializer
    queryset = Advices.objects.all()


# Get Benefits
class BenefitListView(ListAPIView):
    """
    @api {get} core/benefits/ О пользе воды
    @apiSuccessExample {json} Success-Response:
    [
        {
            "title": "Чувствуете, что с вами что-то не так?",
            "text": "Не хватает воды в организме: она выводит токсины из почек и печени,
            помогает усваиваться витаминам и минералам.",
            "link": "https://www.nytimes.com/2000/07/11/health/personal-health.html",
            "short_link": "https://nytimes.com"
        },
        {
            "title": "Слабость и вялость?",
            "text": "Кровь сгущается из-за обезвоживания — сердце напрягается — тело и мозг экономят энергию.",
            "link": "https://www.nytimes.com/2000/07/11/health/personal-health-for-lifelong.html",
            "short_link": "https://nytimes.com"
        }
    ]
    @apiVersion 1.0.0
    @apiHeader {String} Authorization User Bearer Token.
    @apiPermission User
    @apiName benefits
    @apiGroup Основные

    @apiSuccess {String} title Заголовок
    @apiSuccess {String} text Текст
    @apiSuccess {String} link Ссылка на источник
    @apiSuccess {String} short_link Краткая ссылка
    """
    permission_classes = [IsAuthenticated]
    serializer_class = BenefitSerializer
    queryset = Benefit.objects.all()


# Get Tariffs
class TariffsListView(ListAPIView):
    """
    @api {get} core/tariffs/ Тарифные планы
    @apiSuccessExample {json} Success-Response:
    [
        {
            "id": 1,
            "title": "Безлимит",
            "cost": 1200,
            "price_per_month": 0,
            "month": 0,
            "unlimited": true,
            "discount": 0
        },
        {
            "id": 2,
            "title": "1 месяц",
            "cost": 99,
            "price_per_month": 99,
            "month": 1,
            "unlimited": false,
            "discount": 0
        },
        {
            "id": 3,
            "title": "6 месяцев",
            "cost": 499,
            "price_per_month": 99,
            "month": 6,
            "unlimited": false,
            "discount": 16
        },
        {
            "id": 4,
            "title": "12 месяцев",
            "cost": 899,
            "price_per_month": 99,
            "month": 12,
            "unlimited": false,
            "discount": 25
        }
    ]
    @apiVersion 1.0.0
    @apiName tariffs
    @apiGroup Основные
    @apiSuccess {Number} id ID тарифа
    @apiSuccess {String} title Название тарифа
    @apiSuccess {Number} cost Фактическая цена
    @apiSuccess {Number} price_per_month Цена за месяц
    @apiSuccess {Number} month Количество месяцев
    @apiSuccess {Boolean} unlimited Безлимитный <code>True</code> - Да, <code>False</code> - Нет
    @apiSuccess {Number} discount Процент скидки
    """
    permission_classes = [AllowAny]
    serializer_class = TariffsSerializer
    queryset = Tariffs.objects.all().order_by('month')

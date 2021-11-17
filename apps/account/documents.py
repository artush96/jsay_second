# from django_elasticsearch_dsl import Document, fields
# from django_elasticsearch_dsl.registries import registry
# from .models import DailyWater
# from django.contrib.auth import get_user_model
# UserModel = get_user_model()
#
#
# @registry.register_document
# class DailyWaterDocument(Document):
#     # owner = fields.ObjectField(properties={
#     #     'id': fields.IntegerField(),
#     # })
#
#     class Index:
#         # Name of the Elasticsearch index
#         name = 'daily_water'
#
#     class Django:
#         model = DailyWater
#
#         # The fields of the model you want to be indexed in Elasticsearch
#         fields = [
#             'id',
#             'water',
#             'milliliter',
#             'done',
#             'date',
#         ]
#
#         related_models = [UserModel]
#
#     # def get_queryset(self):
#     #     return super(DailyWaterDocument, self).get_queryset().select_related(
#     #         'owner'
#     #     )
#
#     # def search(self):
#     #     s = super(DailyWaterDocument, self).search()
#     #     return s.filter('term', published=True)
#
#
# # from apps.account.documents import DailyWaterDocument
# # from itertools import groupby
#
# # s = DailyWaterDocument.search()
# # s = s.filter('term', owner__id=1)
# # qs = s.to_queryset()
# # groups = groupby(qs, key=lambda x: (x.date.strftime("%B %Y")))
# # {k: list({"day": e.date.day, "litr": e.milliliter} for e in g) for k, g in groups}
#
# # key_func = operator.itemgetter('date')
# # t_list = sorted(list(), key=key_func, reverse=True)
# # for hit in t['hits']['hits']:
# #     t_list.append(hit['_source'])
# # group_list = [{ k : list(g)} for k, g in itertools.groupby(a_list, keyfunc)]

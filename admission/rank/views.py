from dataclasses import FrozenInstanceError
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from django.db.models import Count
from django.http import JsonResponse

import json

from .serializers import (
    ProgramSerializer,
    CollegeSerializer,
    CollegeProgramSerializer,
    # AddmissionSerializer,
    CollegeProgramsListSerializer,
)
from .models import Program, College, CollegeProgram, Addmission, EntranceStudent
from .utils import getProbabilityString


class ProgramViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows BE programs to be viewed.
    """

    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    pagination_class = None


class CollegeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows colleges to be viewed.
    """

    queryset = College.objects.all()
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    serializer_class = CollegeSerializer
    pagination_class = None


class CollegeProgramViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows details of programs within a college to be viewed.
    """

    queryset = CollegeProgram.objects.all()
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_fields = (
        "college",
        "program",
        # "type",
    )
    # ordering_fields = ("cutoff",)
    serializer_class = CollegeProgramSerializer
    pagination_class = None


class CollegeProgramsListViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Api endpoint that gives list of program for given input college
    """
    queryset = CollegeProgram.objects.values("program", "program__name").distinct()
    serializer_class = CollegeProgramsListSerializer
    pagination_class = None

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("college__code",)

    # def get(self, request):
    #     self.queryset = self.queryset.filter(
    #         'college__code' == request.body.college)
    #     return Response(self.queryset)

# class RankFilter(filters.FilterSet):
#     min_rank = filters.NumberFilter(field_name="rank", lookup_expr="gte")
#     max_rank = filters.NumberFilter(field_name="rank", lookup_expr="lte")

#     class Meta:
#         model = Addmission
#         fields = [
#             "collegeprogram",
#             "collegeprogram__college",
#             "collegeprogram__program",
#             "collegeprogram__type",
#             "min_rank",
#             "max_rank",
#         ]


# class AddmissionViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     API endpoint that allows sutdents addmitted to be viewed.
#     """

#     queryset = Addmission.objects.all()

#     filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
#     filterset_class = RankFilter
#     ordering_fields = (
#         "rank",
#         "score",
#     )
#     serializer_class = AddmissionSerializer

class CalcCutoff(APIView):

    def post(self, request):
        CollegeProgramCollection = CollegeProgram.objects.all()

        for col_program in CollegeProgramCollection:
            # col_program.college =

            raw_query = "SELECT id, max(EntranceRank) as cutoff FROM `entrance_student` as `es` INNER JOIN admisssion_list_entrance_student as `ad_es` ON ad_es.EntranceStudentId=es.EntranceStudentID INNER JOIN admission_list_college_record as `ad_col` ON ad_col.AdmissionListCollegeId = ad_es.AdmissionListCollegeId WHERE ad_col.CollegeId = {} and ad_col.ProgramId = {};".format(
                col_program.college_id, col_program.program_id)
            query_result = EntranceStudent.objects.raw(raw_query)

            cutoff = query_result['id']
            return Response(cutoff)
            # cutoff = query_result.cutoff

            # col_program.cutoff = cutoff
            # col_program.save()


class Prediction(APIView):
    """
    API endpoint that predits the result based on rank provided.
    """

    parser_classes = [MultiPartParser]

    def post(self, request, format=None):
        """we expect rank, college and faculty filter from the frontend"""
        print(request.body)
        frontendData = json.loads(request.body)

        print('Hello')
        print(frontendData)
        # raise Exception(str(frontendData['college']))
        # dd(frontendData)
        if frontendData["college"] == "All" and frontendData["faculty"] == "All":
            query_result = CollegeProgram.objects.all()
        elif frontendData["college"] == "All":
            query_result = CollegeProgram.objects.filter(
                program__code__exact=frontendData["faculty"]
            )
        elif frontendData["faculty"] == "All":
            query_result = CollegeProgram.objects.filter(
                college__code__exact=frontendData["college"]
            )
        else:

            query_result = CollegeProgram.objects.filter(
                college__code__exact=frontendData["college"]
            ).filter(program__code__exact=frontendData["faculty"])

        predictionData = []
        for item in query_result:
            print(item)
            singlePrediction = {
                "college": item.college.code,
                "college_name": item.college.name,
                "program": item.program.code,
                "program_name": item.program.name,
                # "type": item.type,
                "probablity": getProbabilityString(
                    int(frontendData["rank"]),
                    item.cutoff,
                    item.seats
                ),
            }
            predictionData.append(singlePrediction)

        # return JsonResponse(predictionData, safe=False)
        return Response(json.dumps(predictionData))


# class Rank(APIView):
#     """
#     API endpoint that gives the data based on range of rank provided.
#     """

#     parser_classes = [MultiPartParser]

#     def post(self, request, format=None):
#         """we expect rank, college and faculty filter from the frontend"""

#         frontendData = request.data
#         min_rank = frontendData["min_rank"]
#         max_rank = frontendData["max_rank"]
#         college = frontendData["college"]

#         if college == "All":
#             queryset = (
#                 Addmission.objects.filter(rank__gte=min_rank, rank__lte=max_rank)
#                 .values("collegeprogram__college", "collegeprogram__college__name")
#                 .annotate(count=Count("collegeprogram__college"))
#             )

#         else:
#             queryset = (
#                 Addmission.objects.filter(
#                     collegeprogram__college__code=college,
#                     rank__gte=min_rank,
#                     rank__lte=max_rank,
#                 )
#                 .values(
#                     "collegeprogram__program",
#                     "collegeprogram__college__name",
#                     "collegeprogram__program__name",
#                 )
#                 .annotate(count=Count("collegeprogram__program"))
#             )

#         return Response(queryset)


# class Analysis(APIView):
#     """
#     API endpoint that for analysis of students data for a college/program.
#     """

#     parser_classes = [MultiPartParser]
#     # permission_classes = [permissions.IsAuthenticated]

#     def post(self, request, format=None):
#         """
#         we expect college and year from the front end currently and since we are not
#         using year for now we will respond result for one college and all faculty
#         """
#         frontendData = request.data
#         if frontendData["college"] == "All" and frontendData["faculty"] != "All":
#             lowestRank = -1
#             resposeData = []
#             resposeData = []
#             query_result = CollegeProgram.objects.filter(
#                 program__code__exact=frontendData["faculty"]
#             )

#             for college_program in query_result:
#                 """determine lowest, highest and no of seat for each faculty"""
#                 program_code = college_program.program.code
#                 cutoff = college_program.cutoff
#                 seats = college_program.seats
#                 type = college_program.type
#                 lowestRank = college_program.cutin
#                 college = college_program.college.code

#                 program_name = college_program.program.name
#                 college_name = college_program.college.CollegeName

#                 """10 ota leko xa coz tyo rank nai navako data ni raxa database maa so euta
#                 matra liyo vane tineru suru maa aauod raxa so 10 ota nikalera rank none xa ki
#                 xaina check garera garnu parne vayo aile ko laagi"""
#                 # rankSortedQuery = (
#                 #     Addmission.objects.filter(
#                 #         collegeprogram__program__code__exact=college_program.program.code
#                 #     )
#                 #     .filter(collegeprogram__type__exact=type)
#                 #     .filter(
#                 #         collegeprogram__college__code__exact=frontendData["college"]
#                 #     )
#                 #     .order_by("rank")[:10]
#                 # )
#                 # for item in rankSortedQuery:
#                 #     if item.rank != None:
#                 #         lowestRank = item.rank
#                 #         break
#                 resposeData.append(
#                     {
#                         "faculty": program_code,
#                         "type": type,
#                         "lowerLimit": lowestRank,
#                         "upperLimit": cutoff,
#                         "seats": seats,
#                         "college": college,
#                         "program_name": program_name,
#                         "college_name": college_name,
#                     }
#                 )
#             return Response(resposeData)

#         if frontendData["college"] == "All" or frontendData["faculty"] != "All":
#             print("Filter should be one college and all faculty")
#             assert False
#         else:
#             lowestRank = -1
#             resposeData = []
#             resposeData = []
#             query_result = CollegeProgram.objects.filter(
#                 college__code__exact=frontendData["college"]
#             )

#             for college_program in query_result:
#                 """determine lowest, highest and no of seat for each faculty"""
#                 program_code = college_program.program.code
#                 cutoff = college_program.cutoff
#                 seats = college_program.seats
#                 type = college_program.type
#                 program_name = college_program.program.name
#                 college_name = college_program.college.CollegeName
#                 """10 ota leko xa coz tyo rank nai navako data ni raxa database maa so euta
#                 matra liyo vane tineru suru maa aauod raxa so 10 ota nikalera rank none xa ki
#                 xaina check garera garnu parne vayo aile ko laagi"""
#                 rankSortedQuery = (
#                     Addmission.objects.filter(
#                         collegeprogram__program__code__exact=college_program.program.code
#                     )
#                     .filter(collegeprogram__type__exact=type)
#                     .filter(
#                         collegeprogram__college__code__exact=frontendData["college"]
#                     )
#                     .order_by("rank")[:10]
#                 )
#                 for item in rankSortedQuery:
#                     if item.rank is not None:
#                         lowestRank = item.rank
#                         break
#                 resposeData.append(
#                     {
#                         "faculty": program_code,
#                         "type": type,
#                         "lowerLimit": lowestRank,
#                         "upperLimit": cutoff,
#                         "seats": seats,
#                         "program_name": program_name,
#                         "college_name": college_name,
#                     }
#                 )
#             return Response(resposeData)


# class DistrictView(APIView):
#     """
#     API endpoint that gives the data based on location provided.
#     """

#     parser_classes = [MultiPartParser]

#     def post(self, request, format=None):
#         """we expect location and year from the frontend"""

#         frontendData = request.data
#         print(frontendData)

#         if frontendData["college"] == "All" and frontendData["faculty"] == "All":
#             resposeData = [
#                 {"college": "All colleges"},
#                 {"program": "All programs"}
#             ]
#             query_result = Addmission.objects.all()
#         elif frontendData["college"] == "All":
#             resposeData = [
#                 {"college": "All colleges"},
#                 {"program": Program.objects.get(code=frontendData["faculty"]).name}
#             ]
#             query_result = Addmission.objects.filter(
#                 collegeprogram__program__code__exact=frontendData["faculty"]
#             )
#         elif frontendData["faculty"] == "All":
#             resposeData = [
#                 {"college": College.objects.get(code=frontendData["college"]).CollegeName},
#                 {"program": "All programs"}
#             ]
#             query_result = Addmission.objects.filter(
#                 collegeprogram__college__code__exact=frontendData["college"]
#             )
#         else:
#             resposeData = [
#                 {"college": College.objects.get(code=frontendData["college"]).CollegeName},
#                 {"program": Program.objects.get(code=frontendData["faculty"]).name}
#             ]
#             query_result = Addmission.objects.filter(
#                 collegeprogram__college__code__exact=frontendData["college"]
#             ).filter(collegeprogram__program__code__exact=frontendData["faculty"])

#         location = query_result.values('district__code', 'district__name').annotate(
#             count=Count('district__code')).order_by('-count').exclude(district__isnull=True)

#         resposeData.append({"location": location})
#         return Response(resposeData)


# class ZoneView(APIView):
#     """
#     API endpoint that gives the data based on location provided.
#     """

#     parser_classes = [MultiPartParser]

#     def post(self, request, format=None):
#         """we expect location and year from the frontend"""

#         frontendData = request.data

#         if frontendData["college"] == "All" and frontendData["faculty"] == "All":
#             query_result = Addmission.objects.all()
#         elif frontendData["college"] == "All":
#             query_result = Addmission.objects.filter(
#                 collegeprogram__program__code__exact=frontendData["faculty"]
#             )
#         elif frontendData["faculty"] == "All":
#             query_result = Addmission.objects.filter(
#                 collegeprogram__college__code__exact=frontendData["college"]
#             )
#         else:

#             query_result = Addmission.objects.filter(
#                 collegeprogram__college__code__exact=frontendData["college"]
#             ).filter(collegeprogram__program__code__exact=frontendData["faculty"])

#         location = query_result.values('district__zone__id', 'district__zone__name').annotate(
#             count=Count('district__zone__id')).order_by('-count').exclude(district__zone__isnull=True)

#         return Response(location)

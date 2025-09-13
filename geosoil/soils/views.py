from django.shortcuts import render

from .serializers import SoilProfileSerializer , LayerSerializer, SourceSerializer ,SoilProfileSerializerCsv , LayerSerializerCsv

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework_gis.filters import GeoFilterSet
from django_filters import rest_framework as filters
from .models import SoilProfile, Layer, Source

from rest_framework_gis.filterset import GeoFilterSet
from rest_framework_gis.filters import GeometryFilter
from django_filters import filters
from rest_framework.decorators import action

from rest_framework.response import Response
from rest_framework import status
# Pytho

from rest_framework_gis.filters import DistanceToPointFilter
from django.contrib.gis.db.models import PointField

class soilProfileFilter(GeoFilterSet):
    """Filter for SoilProfile based on geographic location."""
    # location = DistanceToPointFilter(field_name='location', )
    location = GeometryFilter(field_name='location', lookup_expr='intersects')

    class Meta:
        model = SoilProfile
        fields = ['location']  

# class SoilProfileFilter(GeoFilterSet):
#     location = DistanceToPointFilter()

#     class Meta:
#         model = SoilProfile
#         fields = ['location']

# class LayerFilter(GeoFilterSet):
#     """Filter for Layer based on geographic location."""
    
#     class Meta:
#         model = Layer
#         fields = ['location']


class LayerViewSet(viewsets.ModelViewSet):
    """ViewSet for Layer model."""
    
    queryset = Layer.objects.all()
    #serializer_class = LayerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = (DistanceToPointFilter,)
    # filterset_class = LayerFilter
    
    
    def get_serializer_class(self):
        """Return the appropriate serializer class based on the action."""
        if self.action == 'create_from_csv':
            return LayerSerializerCsv
        else :
            return LayerSerializer
    @action(detail=False, methods=['get'], )
    def delete_all_layers(self, request):
        """Custom action to delete all Layer instances."""
        Layer.objects.all().delete()
        return Response({"message": "All layers deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], url_path='create-from-csv')
    def create_from_csv(self, request):
        """Custom action to create Layer from CSV."""
        serializer = LayerSerializerCsv(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# class SourceFilter(GeoFilterSet):
#     """Filter for Source based on geographic location."""
    
#     class Meta:
#         model = Source
#         fields = ['location']


class SourceViewSet(viewsets.ModelViewSet):
    """ViewSet for Source model."""
    
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    # filter_backends = (
    # filterset_class = SourceFilter
    
    
    
    


class SoilProfileViewSet(viewsets.ModelViewSet):
    """ViewSet for SoilProfile model."""
    
    queryset = SoilProfile.objects.all()
    # serializer_class = SoilProfileSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = (DistanceToPointFilter,)
    filterset_class = soilProfileFilter

    def get_serializer_class(self):
        """Return the appropriate serializer class based on the action."""
        if self.action == 'list':
            return SoilProfileSerializer
        elif self.action == 'retrieve':
            return SoilProfileSerializer
        
        elif self.action == 'create_from_csv':
            # Custom action create profile from csv
         
   
            return SoilProfileSerializerCsv
        return SoilProfileSerializer
    

    @action(detail=False, methods=['post'], url_path='create-from-csv')
    def create_from_csv(self, request):

        """Custom action to create SoilProfile from CSV."""
        serializer = SoilProfileSerializerCsv(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'], )
    def delete_all_soil_profiles(self, request):
        """Custom action to delete all SoilProfile instances."""
        SoilProfile.objects.all().delete()
        return Response({"message": "All soil profiles deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=['get'], )
    def filter_sources(self, request):
        """Custom action to filter sources based on a query parameter."""
        query = request.query_params.get('query', []).split(',')
        print(f"Query: {query}")
        
        
        if query:
            profiles = SoilProfile.objects.filter(source__name__in=query)
        else:
            profiles = SoilProfile.objects.all()
            
            
        print(f"Filtered Profiles Count: {profiles.count()}")
        serializer = SoilProfileSerializer(profiles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



def geostreet_map(request):
    """Display an OpenStreetMap using Leaflet."""

    sources = Source.objects.all()

    return render(request, "soils/map.html", {"sources": sources})


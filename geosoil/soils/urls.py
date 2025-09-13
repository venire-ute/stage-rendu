from django.urls import path , include
from . import views
from rest_framework import routers




# geosoil/soils/urls.py
from django.urls import path
from . import views
# geostreet/urls.py

router = routers.DefaultRouter()

router.register(r'soil-profiles', views.SoilProfileViewSet)
router.register(r'layers', views.LayerViewSet)
router.register(r'sources', views.SourceViewSet)

urlpatterns = [
    path('', views.geostreet_map, name='geostreet-map'),
    path("api/", include(router.urls)),
]

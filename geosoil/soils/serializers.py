from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import SoilProfile, Layer, Source , Property , ProfileProperty , LayerProperty
import pandas as pd
from pyproj import Transformer
from django.db import transaction
from dbfread import DBF
from simpledbf import Dbf5
import tempfile


from itertools import groupby
from operator import attrgetter


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = '__all__'


class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'
class ProfilePropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileProperty
        fields = '__all__'
class LayerPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = LayerProperty
        fields = '__all__'


class SoilProfileSerializer(GeoFeatureModelSerializer):
    source = SourceSerializer(read_only=True)
    class Meta:
        model = SoilProfile
        geo_field = 'location'
        fields = '__all__'

class SoilProfileSerializerCsv(serializers.ModelSerializer):
    CT = 'CT'
    LT = 'LT'
    type = (
        (CT, 'Centroid'),
        (LT, 'longitude/Latitude'),
    )
    type_location = serializers.ChoiceField(choices=type, default=LT, write_only=True)
    projection_zone = serializers.IntegerField(default=0, write_only=True)
    

    file = serializers.FileField(write_only=True)

    class Meta:
        model = SoilProfile
        fields = ['file', 'type_location', 'projection_zone', 'source']
        extra_kwargs = {
            'file': {'write_only': True},
            'type_location': {'write_only': True},
            'projection_zone': {'write_only': True},
            # 'source': {'write_only': True,'required': True},

        }

        
    def create(self, validated_data):
        file = validated_data.pop('file', None)
        source = validated_data.pop('source', None)

        if  file and source:
          
            type_file = file.name.split('.')[-1].lower()

            if type_file not in ['csv', 'tsv', 'dbf']:
                raise serializers.ValidationError("Unsupported file type. Only CSV, TSV, and DBF files are allowed.")
            
            elif type_file == 'dbf':
                with tempfile.NamedTemporaryFile(delete=False, suffix='.dbf') as tmp:
                    for chunk in file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                    dbf = Dbf5(tmp_path, codec='latin-1')
                    df = dbf.to_dataframe()
                    print(df.head(5))
                    print(df.shape)

            else:
                
                if type_file == 'csv':
                    sep = ','
                elif type_file == 'tsv':
                    sep = '\t'
                else:
                    raise serializers.ValidationError("Unsupported file type. Only CSV and TSV files are allowed.")


                df = pd.read_csv(file, sep=sep, encoding='utf-8')

            print(df.columns)
            

            if source.name == 'IRD':
     
                
                if validated_data['type_location'] == self.CT:
                    tr = Transformer.from_crs(32628, 4326, always_xy=True)
                    df[["lon", "lat"]] = df.apply(
                        lambda r: tr.transform(r["X_Centroid"], r["Y_Centroid"]),
                        axis=1, result_type="expand"
                    )
                    df['geometry'] = df.apply(
                        lambda r: Point(r['lon'], r['lat']), axis=1
                    )
                df = df.drop_duplicates(subset=["geometry"], keep="first")
                objs = [
                    SoilProfile(
                        
                        code     = f"IRD-{row.Profile_id}",
                        location = Point(row.lon, row.lat),
                        source   = source,
                        profile_id = row.Profile_id,
                        
                        # carbon   = row.Carbon,
                        # depth    = row.Profondeur
                    )
                    for row in df.itertuples()
                ]


            elif source.name == 'AFSP':
       
                objs = [
                    SoilProfile(
                        code     = f"AFSP-{row.ProfileID}",
                        location = Point(row.X_LonDD, row.Y_LatDD),
                        profile_id = row.ProfileID,
                        source   = source,
                        # carbon   = row.Carbon,
                        # depth    = row.Profondeur
                    )
                    for row in df.itertuples()
                ]

            elif source.name == 'WOSIS':
                objs = [
                    SoilProfile(
                        code     = f"WOSIS-{row.profile_id}",
                        location = Point(row.longitude, row.latitude),
                        profile_id = row.profile_id,
                        source   = source,
                        # carbon   = row.Carbon,
                        # depth    = row.Profondeur
                    )
                    for row in df.itertuples()
                ]

            else:
                raise serializers.ValidationError(f"Source {source.name} is not supported for CSV files.")
            
            
            objs.sort(key=lambda x: (x.location.wkt, x.source_id))
            objs = [next(g) for _, g in groupby(objs, key=lambda x: (x.location.wkt, x.source_id))]

            with transaction.atomic():
                SoilProfile.objects.bulk_create(
                    objs,
                    batch_size=1000,
                    update_conflicts=True,
                    update_fields=["location", "source", "profile_id"],
                    unique_fields=["location", "source"],
                )


        else:
            raise serializers.ValidationError("No file uploaded.")
        return True

class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = '__all__'

class LayerSerializerCsv(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    
    
    source = serializers.PrimaryKeyRelatedField(
        queryset=Source.objects.all(),
        write_only=True,
        required=True
    )
     

    class Meta:
        model = Layer
        fields = ["file", "source"]
        # read_only_fields = ['id', 'soil_profile_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'file': {'write_only': True},
        }

    def create(self, validated_data):
        file = validated_data.pop('file', None)
        source = validated_data.pop('source', None)

        if file and source:
            type_file = file.name.split('.')[-1].lower()

            if type_file not in ['csv', 'tsv', 'dbf']:
                raise serializers.ValidationError("Unsupported file type. Only CSV, TSV, and DBF files are allowed.")
            
            elif type_file == 'dbf':
                with tempfile.NamedTemporaryFile(delete=False, suffix='.dbf') as tmp:
                    for chunk in file.chunks():
                        tmp.write(chunk)
                    tmp_path = tmp.name

                    dbf = Dbf5(tmp_path, codec='latin-1')
                    df = dbf.to_dataframe()
                    print(df.head(5))
                    print(df.shape)

            else:
                
                if type_file == 'csv':
                    sep = ','
                elif type_file == 'tsv':
                    sep = '\t'
                else:
                    raise serializers.ValidationError("Unsupported file type. Only CSV and TSV files are allowed.")

                df = pd.read_csv(file, sep=sep, encoding='utf-8')

            print(df.columns)

            if source.name == 'IRD':
                objs = [
                    Layer(
                        soil_profile_id=row.soil_profile_id,
                        depth=row.depth,
                        thickness=row.thickness,
                        texture=row.texture,
                        organic_matter=row.organic_matter,
                        ph=row.ph,
                    )
                    for row in df.itertuples()
                ]

            with transaction.atomic():
                Layer.objects.bulk_create(objs, batch_size=1000)

        else:
            raise serializers.ValidationError("No file uploaded.")
        return True
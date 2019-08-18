from rest_framework import serializers
from treenipaivakirja.models import harjoitus


class HarjoitusSerializer(serializers.ModelSerializer):
    class Meta:
        model = harjoitus
        fields = [
            'id',
            'pvm',
            'vuorokaudenaika',
            'laji_fk',
            'kesto_h',
            'kesto_min',
            'keskisyke',
            'matka',
            'vauhti_km_h',
            'vauhti_min_km',
            'nousu',
            'kalorit',
            'tuntuma',
            'kommentti'
        ]
            
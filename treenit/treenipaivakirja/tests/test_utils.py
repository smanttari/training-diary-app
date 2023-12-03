import pandas as pd
import numpy as np
import json
import datetime

from django.test import TestCase

from treenipaivakirja.utils import (
    duration_to_string, duration_to_decimal, speed_min_per_km, 
    dataframe_to_dict, coalesce, week_number, parse_coordinates_from_gpx
)


class DurationToStringTest(TestCase):
    def test_none(self):
        h = None
        mins = None
        self.assertEqual(duration_to_string(h,mins),None)

    def test_nan(self):
        h = np.nan
        mins = np.nan
        self.assertEqual(duration_to_string(h,mins),None)

    def test_h_only(self):
        h = 15
        mins = None
        self.assertEqual(duration_to_string(h,mins),'15:00')

    def test_min_only(self):
        h = None
        mins = 25
        self.assertEqual(duration_to_string(h,mins),'00:25')

    def test_small_integers(self):
        h = 1
        mins = 1
        self.assertEqual(duration_to_string(h,mins),'01:01')

    def test_decimals(self):
        h = 1.5
        mins = 1.2
        self.assertEqual(duration_to_string(h,mins),'01:01')

    def test_min_greater_than_60(self):
        h = 1
        mins = 100
        self.assertEqual(duration_to_string(h,mins),'02:40')

    def test_min_only_and_greater_than_60(self):
        h = None
        mins = 75
        self.assertEqual(duration_to_string(h,mins),'01:15')


class DurationToDecimalTest(TestCase):
    def test_none(self):
        h = None
        mins = None
        self.assertEqual(duration_to_decimal(h,mins),0)

    def test_nan(self):
        h = np.nan
        mins = np.nan
        self.assertEqual(duration_to_decimal(h,mins),0)

    def test_h_only(self):
        h = 2
        mins = None
        self.assertEqual(duration_to_decimal(h,mins),2)

    def test_min_only(self):
        h = None
        mins = 15
        self.assertEqual(duration_to_decimal(h,mins),0.25)

    def test_min_greater_than_60(self):
        h = 1
        mins = 90
        self.assertEqual(duration_to_decimal(h,mins),2.5)


class SpeedMinPerKmTest(TestCase):
    def test_none(self):
        m = None
        s = None
        self.assertEqual(speed_min_per_km(m,s),None)
    
    def test_h_only(self):
        m = 5
        s = None
        self.assertEqual(speed_min_per_km(m,s),5)
    
    def test_min_only(self):
        m = None
        s = 30
        self.assertEqual(speed_min_per_km(m,s),0.5)

    def test_integers(self):
        m = 3
        s = 15
        self.assertEqual(speed_min_per_km(m,s),3.25)

    def test_s_greater_than_60(self):
        m = 10
        s = 72
        self.assertEqual(speed_min_per_km(m,s),11.2)


class DataFrameToDictTest(TestCase):
    def test_empty_df(self):
        df = pd.DataFrame()
        self.assertEqual(dataframe_to_dict(df),[])

    def test_df_with_no_rows(self):
        df = pd.DataFrame(columns=['A','B','C'])
        self.assertEqual(dataframe_to_dict(df),[])

    def test_df_with_rows(self):
        categories = ['A','B']
        data = {'col1': [1, 2], 'col2': [3, 4]}
        df = pd.DataFrame(data, index=categories)
        result = [{"category": "A", "series": {"col1": 1, "col2": 3}}, {"category": "B", "series": {"col1": 2, "col2": 4}}]
        self.assertEqual(dataframe_to_dict(df),result)


class CoalesceTest(TestCase):
    def test_none(self):
        x = None
        val = 'kissa'
        self.assertEqual(coalesce(x,val),'kissa')

    def test_nan(self):
        x = np.nan
        val = 'kissa'
        self.assertEqual(coalesce(x,val),'kissa')

    def test_not_none(self):
        x = 'koira'
        val = 'kissa'
        self.assertEqual(coalesce(x,val),'koira')


class WeekNumberTest(TestCase):
    def test_february(self):
        day = datetime.date(2020,2,1)
        self.assertEqual(week_number(day),5)

    def test_december_week_1(self):
        day = datetime.date(2019,12,31)
        self.assertEqual(week_number(day),52)

    def test_january_week_52(self):
        day = datetime.date(2017,1,1)
        self.assertEqual(week_number(day),1)

    def test_january_week_53(self):
        day = datetime.date(2016,1,1)
        self.assertEqual(week_number(day),1)


class GpxParseTest(TestCase):
    def test_gpx_parse(self):
        gpx = '../robot/tests/trainings/robot_test.GPX'
        coord = [
                ['60.25270667', '24.533855'], ['60.25270667', '24.533855'], 
                ['60.25270667', '24.533855'], ['60.25270667', '24.533855'], 
                ['60.25270667', '24.533855'], ['60.25271', '24.53385333'], 
                ['60.25271833', '24.53383833'], ['60.25273167', '24.53381167'], 
                ['60.25273667', '24.53378'], ['60.25274333', '24.53375'], 
                ['60.25275', '24.533715'], ['60.25276', '24.533685'], 
                ['60.25277833', '24.53363167'], ['60.25279167', '24.53358667'], 
                ['60.252805', '24.53354667'], ['60.252815', '24.53350667'], 
                ['60.25282333', '24.53346333'], ['60.25283167', '24.53342333'], 
                ['60.25283833', '24.53337667'], ['60.25284833', '24.53333667'], 
                ['60.25285833', '24.533295'], ['60.25286667', '24.53325333'], 
                ['60.25288', '24.53321667'], ['60.25289333', '24.53317833'], 
                ['60.25290667', '24.53314167'], ['60.252925', '24.53309333'], 
                ['60.25294', '24.53304'], ['60.25295833', '24.53299'], 
                ['60.25297167', '24.53294333'], ['60.25298667', '24.53288833'], 
                ['60.253', '24.53284833']
                ]
        self.assertEqual(parse_coordinates_from_gpx(gpx),coord)
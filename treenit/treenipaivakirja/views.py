import json
import logging
from datetime import datetime, timedelta
from os import path

import pandas as pd

from django.shortcuts import render,redirect
from django.forms import inlineformset_factory, formset_factory
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Max
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.debug import sensitive_variables

from treenipaivakirja.models import Harjoitus, Laji, Teho, Tehoalue, Kausi, PolarUser, PolarSport, PolarSleep, PolarRecharge, OuraUser, OuraSleep
from treenipaivakirja.forms import HarjoitusForm, LajiForm, TehoForm, TehoalueForm, UserForm, RegistrationForm, KausiForm, HarjoitusFormSet, PwChangeForm
import treenipaivakirja.utils as utils
import treenipaivakirja.transformations as tr
import treenipaivakirja.calculations as cl
import treenipaivakirja.accesslink as al
import treenipaivakirja.oura as ou


LOGGER_DEBUG = logging.getLogger(__name__)


@login_required
def index(request):
    """ 
    Front page 
    """
    user_id = request.user.id
    current_day = datetime.now().date()
    current_year = current_day.year
    current_week = utils.week_number(current_day)
    current_day_pd = pd.Timestamp(current_day)
    current_day_minus_14 = pd.Timestamp(current_day_pd - timedelta(days=14))
    current_day_minus_28 = pd.Timestamp(current_day_pd - timedelta(days=28))

    if not Harjoitus.objects.filter(user=user_id):
        hours_current_year = 0
        hours_change = 0
        hours_per_week_current_year = 0
        hours_per_week_change = 0
        feeling_current_period = 0
        feeling_change = 0
    else:
        hours_current_year = cl.hours_year_to_date(user_id)
        hours_past_year = cl.hours_past_year_to_date(user_id)
        hours_change = hours_current_year - hours_past_year

        total_hours_past_year = cl.total_hours_per_year(user_id, current_year-1)
        hours_per_week_current_year = hours_current_year / current_week
        hours_per_week_past_year = total_hours_past_year / 52
        hours_per_week_change = hours_per_week_current_year - hours_per_week_past_year

        feeling_current_period = cl.avg_feeling_per_period(user_id,current_day_minus_14,current_day)
        feeling_last_period = cl.avg_feeling_per_period(user_id,current_day_minus_28,current_day_minus_14)
        feeling_change = feeling_current_period - feeling_last_period

    return render(request,'index.html',
        context = {
            'hours_current_year': int(round(hours_current_year,0)),
            'hours_change': int(round(hours_change,0)),
            'hours_per_week_current_year': round(hours_per_week_current_year,1),
            'hours_per_week_change': round(hours_per_week_change,1),
            'feeling_current_period': round(feeling_current_period,1),
            'feeling_change': round(feeling_change,1),
            'current_day': current_day
            })


@login_required
def trainings_view(request):
    """ 
    List of trainings 
    """
    user_id = request.user.id
    current_day = datetime.now().date()
    startdate = utils.coalesce(cl.first_training_date(user_id),current_day).strftime('%d.%m.%Y')
    enddate = current_day.strftime('%d.%m.%Y') 
    sports = tr.sports_to_dict(user_id)
    sport = 'Kaikki'
    zones = tr.zone_areas_to_list(user_id)
    table_headers = ['details','Vko','Päivä','Laji','Kesto','Keskisyke','Matka (km)','Vauhti (km/h)','Tuntuma'] + zones + ['Kommentti','edit','delete']
    
    if request.method == "POST":
        if 'polar' in request.POST:
            return redirect('accesslink_trainings')
        sport = request.POST['sport']
        startdate = request.POST['startdate']
        enddate = request.POST['enddate']
        if 'lepo' in request.POST:
            restdays = True
        else:
            restdays = False
        export_columns = ['Vko','Pvm','Viikonpäivä','Kesto','Laji','Matka (km)','Vauhti (km/h)','Keskisyke','Tuntuma', 'Kommentti'] + zones
        trainings_df = tr.trainings_to_df(
            user_id=user_id, 
            columns=export_columns, 
            startdate=datetime.strptime(startdate,'%d.%m.%Y').strftime('%Y%m%d'), 
            enddate=datetime.strptime(enddate,'%d.%m.%Y').strftime('%Y%m%d'),
            sport=sport,
            restdays=restdays,
            duration_format='decimal', 
            date_format='%d.%m.%Y')

        if trainings_df is None or trainings_df.empty:
            messages.add_message(request, messages.ERROR, 'Ei harjoituksia')
        else:
            try:
                if 'export_csv' in request.POST:
                    return utils.dataframe_to_csv(trainings_df)
                if 'export_xls' in request.POST:
                    return utils.dataframe_to_excel(trainings_df)
            except Exception as e:
                messages.add_message(request, messages.ERROR, 'Lataus epäonnistui: {}'.format(str(e)))

    return render(request, 'trainings.html',
        context = {
            'sport': sport,
            'sports': sports,
            'startdate': startdate,
            'enddate': enddate,
            'table_headers': table_headers
            })


@login_required
def trainings_map(request):
    """ 
    View routes on map
    """
    user_id = request.user.id
    enddate = datetime.now().date()
    startdate = enddate - timedelta(days=28)
    sports = tr.sports_to_dict(user_id)
    sport = 'Kaikki'
    training_id = 0

    if request.GET.get('startdate'):
        startdate = datetime.strptime(request.GET['startdate'], '%d.%m.%Y')
    if request.GET.get('enddate'):
        enddate = datetime.strptime(request.GET['enddate'], '%d.%m.%Y')
    if request.GET.get('sport'):
        sport = request.GET['sport']
    if request.GET.get('training'):
        training_id = int(request.GET['training'].replace(u'\xa0', ''))
        if training_id != 0:
            training = Harjoitus.objects.get(id=training_id, user_id=user_id)
            startdate = training.pvm
            enddate = training.pvm
            sport = str(training.laji)

    routes = tr.trainings_with_route(user_id, startdate, enddate, sport, training_id, include_gpx=True)
    
    if '-1' in routes.keys():
        training_id = -1

    return render(request, 'map.html', context = {
        'sport': sport,
        'sports': sports,
        'startdate': startdate.strftime('%d.%m.%Y'),
        'enddate': enddate.strftime('%d.%m.%Y'),
        'routes': routes,
        'training_id': training_id
    })


@login_required
def reports_amounts(request):
    """ 
    Training amount reports 
    """
    user_id = request.user.id

    if not Harjoitus.objects.filter(user=user_id):
        years = []
        sport = ''
        sports = []
        hours_per_season_json = []
        hours_per_year_json = []
        kilometers_per_season_json = []
        kilometers_per_year_json = []
        hours_per_month_json = []
        hours_per_week_json = []
        hours_per_sport_json = []
        hours_per_sport_group_json = []
    else:
        trainings_df = tr.trainings_base_to_df(user_id)
        sports = tr.sports_to_list(user_id) 
        years = tr.years_to_list(user_id)
        sport = sports[0]
        
        trainings_per_season = tr.trainings_per_season_to_df(trainings_df)
        trainings_per_year = tr.trainings_per_year_to_df(trainings_df)
        trainings_per_month = tr.trainings_per_month_to_df(trainings_df,user_id)
        trainings_per_week = tr.trainings_per_week_to_df(trainings_df,user_id)

        hours_per_season_json = tr.hours_per_season_to_json(trainings_per_season)
        hours_per_year_json = tr.hours_per_year_to_json(trainings_per_year)
        hours_per_month_json = tr.hours_per_month_to_json(trainings_per_month)
        hours_per_week_json = tr.hours_per_week_to_json(trainings_per_week)
        hours_per_sport_json = tr.hours_per_sport_to_json(trainings_df)
        hours_per_sport_group_json = tr.hours_per_sport_group_to_json(trainings_df)

        kilometers_per_season_json = tr.kilometers_per_season_to_json(trainings_per_season)
        kilometers_per_year_json = tr.kilometers_per_year_to_json(trainings_per_year)

    return render(request, 'reports_amounts.html',
        context = {
            'years': years,
            'sport': sport,
            'sports': sports,
            'hours_per_season_json': hours_per_season_json,
            'hours_per_year_json': hours_per_year_json,
            'hours_per_month_json': hours_per_month_json,
            'hours_per_week_json': hours_per_week_json,
            'hours_per_sport_json': hours_per_sport_json,
            'hours_per_sport_group_json': hours_per_sport_group_json,
            'kilometers_per_season_json': kilometers_per_season_json,
            'kilometers_per_year_json': kilometers_per_year_json
            })


@login_required
def reports_sports(request):
    """ 
    Trainings reports per sport
    """
    user_id = request.user.id

    if not Harjoitus.objects.filter(user=user_id):
        sport = ''
        sports = []
        avg_per_sport = []
        amounts_per_sport = []
        avg_per_sport_table = []
        hours_per_sport = []
        kilometers_per_sport = []
    else:    
        sports = tr.sports_to_list(user_id) 
        sport = sports[0]
        trainings_df = tr.trainings_base_to_df(user_id)
        trainings_per_sport_per_year = tr.trainings_per_sport_to_df(trainings_df, 'vuosi')
        trainings_per_sport_per_season = tr.trainings_per_sport_to_df(trainings_df, 'kausi')

        hours_per_sport = {'year':{}, 'season':{}}
        kilometers_per_sport = {'year':{}, 'season':{}}
        avg_per_sport = {'year':{}, 'season':{}}
        avg_per_sport_table = {'year':{}, 'season':{}}
        amounts_per_sport = {'year':{}, 'season':{}}

        for s in sports:
            data_per_year = trainings_per_sport_per_year[trainings_per_sport_per_year['laji_nimi'].astype(str) == s]
            data_per_season = trainings_per_sport_per_season[trainings_per_sport_per_season['laji_nimi'].astype(str) == s]
            if not data_per_year.empty:
                amounts_per_sport['year'][s] = data_per_year[['vuosi','lkm','kesto (h)','matka (km)']].fillna('').to_dict(orient='records')
                avg_per_sport_table['year'][s] = data_per_year[['vuosi','kesto (h) ka.','matka (km) ka.','vauhti (km/h)','keskisyke']].rename(columns={'kesto (h) ka.':'kesto (h)','matka (km) ka.':'matka (km)'}).fillna('').to_dict(orient='records')
                data_per_year = data_per_year.set_index('vuosi')
                hours_per_sport['year'][s] = utils.dataframe_to_dict(data_per_year[['kesto (h)']])
                kilometers_per_sport['year'][s] = utils.dataframe_to_dict(data_per_year[['matka (km)']])
                avg_per_sport['year'][s] = utils.dataframe_to_dict(data_per_year[['vauhti (km/h)','keskisyke']])
            if not data_per_season.empty:
                amounts_per_sport['season'][s] = data_per_season[['kausi','lkm','kesto (h)','matka (km)']].fillna('').to_dict(orient='records')
                avg_per_sport_table['season'][s] = data_per_season[['kausi','kesto (h) ka.','matka (km) ka.','vauhti (km/h)','keskisyke']].rename(columns={'kesto (h) ka.':'kesto (h)','matka (km) ka.':'matka (km)'}).fillna('').to_dict(orient='records')
                data_per_season = data_per_season.set_index('kausi')
                hours_per_sport['season'][s] = utils.dataframe_to_dict(data_per_season[['kesto (h)']])
                kilometers_per_sport['season'][s] = utils.dataframe_to_dict(data_per_season[['matka (km)']])
                avg_per_sport['season'][s] = utils.dataframe_to_dict(data_per_season[['vauhti (km/h)','keskisyke']])

    return render(request, 'reports_sports.html',
        context = {
            'sport': sport,
            'sports': sports,
            'avg_per_sport': json.dumps(avg_per_sport),
            'amounts_per_sport': json.dumps(amounts_per_sport),
            'avg_per_sport_table': json.dumps(avg_per_sport_table),
            'hours_per_sport': json.dumps(hours_per_sport),
            'kilometers_per_sport': json.dumps(kilometers_per_sport)
            })



@login_required
def reports_zones(request):
    """ 
    Trainings reports per zone
    """
    user_id = request.user.id
    seasons = tr.seasons_to_list(user_id)
    
    if not Harjoitus.objects.filter(user=user_id):
        years = []
        hours_per_zone_json = []
    else:
        years = tr.years_to_list(user_id)
        trainings_df = tr.trainings_base_to_df(user_id)
        hours_per_zone_json = tr.hours_per_zone_to_json(trainings_df,user_id)

    return render(request, 'reports_zones.html',
        context = {
            'years': years,
            'seasons': seasons,
            'hours_per_zone_json': hours_per_zone_json
            })


@login_required
def training_add(request):
    """ 
    Inserts new training 
    """
    TehoFormset = inlineformset_factory(Harjoitus,Teho,form=TehoForm,extra=1,can_delete=True)
    required_fields = utils.get_required_fields(Teho)
    if request.method == "POST":
        harjoitus_form = HarjoitusForm(request.user,request.POST,request.FILES)
        teho_formset = TehoFormset(request.POST)
        if harjoitus_form.is_valid() and harjoitus_form.has_changed():
            instance = harjoitus_form.save(commit=False)
            instance.user = request.user
            instance.save()
            training = Harjoitus.objects.get(id=instance.id)
            teho_formset = TehoFormset(request.POST, request.FILES, instance=training)
            teho_formset.is_valid()
            for teho_form in teho_formset:
                data = teho_form.cleaned_data
                if len(data) > 0: 
                    if not data['DELETE']:
                        data['harjoitus'] = training
                        del data['DELETE']
                        teho = Teho(**data)
                        teho.save()
            messages.add_message(request, messages.SUCCESS, 'Harjoitus tallennettu.')
            return redirect('trainings')
    else:
        harjoitus_form = HarjoitusForm(request.user,initial={'pvm': datetime.now()})
        teho_formset = TehoFormset(queryset=Teho.objects.none())
        for form in teho_formset:
            form.fields['tehoalue'].queryset = Tehoalue.objects.filter(user=request.user).order_by('jarj_nro')

    return render(request, 'training_add.html',
        context = {
            'teho_formset': teho_formset,
            'harjoitus_form': harjoitus_form,
            'required_fields': required_fields
            })


@login_required
def training_modify(request,pk):
    """ 
    Modifies training information 
    """
    TehoFormset = inlineformset_factory(Harjoitus,Teho,form=TehoForm,extra=1,can_delete=True)
    required_fields = utils.get_required_fields(Teho)
    training = Harjoitus.objects.get(id=pk,user_id=request.user.id)
    if request.method == "POST":
        harjoitus_form = HarjoitusForm(request.user,request.POST,request.FILES,instance=training)
        teho_formset = TehoFormset(request.POST,request.FILES,instance=training,initial=[{'harjoitus':training.id}])
        if harjoitus_form.is_valid() and harjoitus_form.has_changed():
            harjoitus_form.save()
        if teho_formset.is_valid() and teho_formset.has_changed():
            teho_formset.save()
        messages.add_message(request, messages.SUCCESS, 'Harjoitus tallennettu.')
        return redirect('trainings')
    else:
        harjoitus_form = HarjoitusForm(request.user,instance=training)
        teho_formset = TehoFormset(instance=training, initial=[{'harjoitus':training.id}])
        for form in teho_formset:
            form.fields['tehoalue'].queryset = Tehoalue.objects.filter(user=request.user).order_by('jarj_nro')
    
    return render(request, 'training_modify.html',
        context = {
            'teho_formset': teho_formset,
            'harjoitus_form': harjoitus_form,
            'required_fields': required_fields
            })


@login_required
def training_delete(request,pk):
    """ 
    Deletes training 
    """
    training = Harjoitus.objects.get(id=pk,user_id=request.user.id)

    if request.method == "POST":
        response = request.POST['confirm']
        if response == 'no':
            return redirect('trainings')
        if response == 'yes':
            training.delete()
            messages.add_message(request, messages.SUCCESS, 'Harjoitus poistettu.')
            return redirect('trainings')

    return render(request,'training_delete.html',
        context = {
            'day': training.pvm,
            'sport': training.laji,
            'duration': training.kesto
            })


@sensitive_variables('access_token')
@login_required
def accesslink_callback(request):
    """
    Authentication to Polar Accesslink
    """
    auth_code = request.GET.get('code')
    state = request.GET.get('state')
    if auth_code is None:
        messages.add_message(request, messages.ERROR, 'Polar Accesslink Error: {}'.format(request.GET.get('error','')))
        return redirect('trainings')
    else:
        token = al.get_access_token(auth_code)
        if token.status_code != 200:
            messages.add_message(request, messages.ERROR, 'Polar Accesslink Error: {} {}'.format(token.status_code,token.json()['error']))
            return redirect('trainings')
        else:
            polar_user_id = token.json()['x_user_id']
            access_token = token.json()['access_token']
            user = al.register_user(access_token, request.user.id)
            if user.status_code != 200:
                messages.add_message(request, messages.ERROR, 'Polar Accesslink Error: {} {}'.format(user.status_code,user.reason))
                return redirect('trainings')
            else:
                polar_user = PolarUser.objects.create(
                    polar_user_id = polar_user_id,
                    access_token = access_token,
                    registration_date = datetime.strptime(user.json()['registration-date'][:19], '%Y-%m-%dT%H:%M:%S'),
                    user = User.objects.get(id=request.user.id))
    if state == 'trainings':
        return redirect('accesslink_trainings')
    else:
        return redirect('accesslink_recovery')


@sensitive_variables('access_token')
@login_required
def accesslink_trainings(request):
    """
    Fetch training data from Polar Accesslink
    """
    try:
        polar_user = PolarUser.objects.get(user=request.user.id)
    except:
        polar_auth_url = al.build_auth_url()
        return redirect(polar_auth_url)

    required_fields = utils.get_required_fields(Harjoitus)
    HarjoitusFormset = formset_factory(form=HarjoitusForm, formset=HarjoitusFormSet, extra=0, can_delete=True)

    if request.method == 'POST':
        if 'save' in request.POST:
            harjoitus_formset = HarjoitusFormset(request.POST, form_kwargs={'user': request.user})
            if harjoitus_formset.is_valid():
                for form in harjoitus_formset:
                    if form not in harjoitus_formset.deleted_forms:
                        polar_sport = form.cleaned_data['polar_sport']
                        PolarSport.objects.update_or_create(
                            polar_user_id=polar_user.polar_user_id, 
                            polar_sport=polar_sport,
                            defaults={'laji': form.cleaned_data['laji']})        
                        instance = form.save(commit=False)
                        instance.user = request.user
                        if form.cleaned_data['has_route']:
                            exercise_id = instance.polar_exercise_id
                            pvm = instance.pvm
                            filename = pvm.strftime('%Y%m%d') + '_' + polar_sport + '_' + str(exercise_id) + '.GPX'
                            gpx = al.get_exercise_gpx(polar_user, exercise_id)
                            if gpx is not None:
                                instance.reitti = ContentFile(gpx, filename)
                        instance.save()
                messages.add_message(request, messages.SUCCESS, 'Harjoitukset tallennettu.')
                al.commit_transaction(request, polar_user)
                return redirect('trainings')
            else:
                messages.add_message(request, messages.ERROR, 'Tallennus epäonnistui. Täytä puuttuvat tiedot. Tarkasta formaatit.')
        if 'discard' in request.POST:
            al.commit_transaction(request, polar_user)
            return redirect('trainings')
    else: 
        exercises_list = al.get_exercises(request, polar_user)
        if exercises_list is None:
            return redirect('trainings')     
        form_data = al.parse_exercises(polar_user, exercises_list)
        harjoitus_formset = HarjoitusFormset(data=form_data, form_kwargs={'user': request.user})
        messages.add_message(request, messages.SUCCESS, 'Harjoitusten hakeminen onnistui. Yhteensä {} harjoitusta saatavilla.'.format(len(exercises_list)))

    return render(request, 'accesslink_trainings.html',
        context = {
            'harjoitus_formset': harjoitus_formset,
            'required_fields': required_fields
            })


@sensitive_variables('access_token')
@login_required
def accesslink_recovery(request):
    """ 
    Fetch recovery data from Polar Accesslink
    """
    try:
        polar_user = PolarUser.objects.get(user=request.user.id)
        access_token = polar_user.access_token
    except:
        polar_auth_url = al.build_auth_url()
        return redirect(polar_auth_url)
    
    sleep = al.list_sleep(access_token)
    if sleep.status_code != 200:
        messages.add_message(request, messages.ERROR, 'Polar Accesslink Error: {} {}'.format(sleep.status_code,sleep.reason))
        return redirect('recovery')
    sleep_objects = al.parse_sleep_data(polar_user, sleep)
    PolarSleep.objects.bulk_create(sleep_objects, ignore_conflicts=True)

    recharge = al.list_nightly_recharge(access_token)
    if recharge.status_code != 200:
        messages.add_message(request, messages.ERROR, 'Polar Accesslink Error: {} {}'.format(recharge.status_code,recharge.reason))
        return redirect('recovery')
    recharge_objects = al.parse_recharge_data(polar_user, recharge)
    PolarRecharge.objects.bulk_create(recharge_objects, ignore_conflicts=True)
    messages.add_message(request, messages.SUCCESS, 'Datan hakeminen onnistui.')
    return redirect('recovery')


@sensitive_variables('access_token')
@login_required
def oura_recovery(request):
    """ 
    Fetch recovery data from Oura
    """
    user = User.objects.get(id=request.user.id)
    current_day = datetime.now().date().strftime('%Y-%m-%d')
    try:
        oura_user = OuraUser.objects.get(user=request.user.id)
        access_token = oura_user.access_token
        refresh_token = oura_user.refresh_token
    except:
        oura_auth_url = ou.build_auth_url()
        return redirect(oura_auth_url)
    
    last_date = OuraSleep.objects.filter(user=user.id).aggregate(Max('date'))['date__max']
    if last_date is None:
        start_date = None
    else:
        start_date = last_date.strftime('%Y-%m-%d')

    sleep = ou.sleep_summary(path='sleep', token=access_token, start_date=start_date, end_date=current_day)
    daily_sleep = ou.sleep_summary(path='daily_sleep', token=access_token, start_date=start_date, end_date=current_day)
    
    if sleep.status_code == 401:    #unauthorized
        token = ou.refresh_token(refresh_token)
        if token.status_code != 200:
            messages.add_message(request, messages.ERROR, 'Oura Error: ' + ou.error_message(token))
            return redirect('recovery')
        else:
            access_token = token.json()['access_token']
            refresh_token = token.json()['refresh_token']
            OuraUser.objects.update(
                access_token = access_token,
                refresh_token = refresh_token,
                user = user)
            sleep = ou.sleep_summary(path='sleep', token=access_token, start_date=start_date, end_date=current_day)
            daily_sleep = ou.sleep_summary(path='daily_sleep', token=access_token, start_date=start_date, end_date=current_day)
    if sleep.status_code != 200:
        messages.add_message(request, messages.ERROR, 'Oura Error: ' + ou.error_message(sleep))
    else:
        sleep_objects = ou.parse_sleep_data(user, sleep, daily_sleep)
        OuraSleep.objects.bulk_create(sleep_objects, ignore_conflicts=True)
        messages.add_message(request, messages.SUCCESS, 'Datan hakeminen onnistui.')
    return redirect('recovery')
    

@sensitive_variables('access_token')
@login_required
def oura_callback(request):
    """
    Authentication to Oura
    """
    auth_code = request.GET.get('code')
    if auth_code is None:
        error = request.GET.get('error')
        messages.add_message(request, messages.ERROR, 'Oura Error: {}'.format(error))
        return redirect('recovery')
    else:
        token = ou.get_access_token(auth_code)
        if token.status_code != 200:
            messages.add_message(request, messages.ERROR, 'Oura Error: ' + ou.error_message(token))
            return redirect('recovery')
        else:
            OuraUser.objects.create(
                access_token = token.json()['access_token'],
                refresh_token = token.json()['refresh_token'],
                user = User.objects.get(id=request.user.id))
    return redirect('oura_recovery')


@login_required
def recovery(request):
    """ 
    Recovery data
    """
    user_id = request.user.id
    current_day = datetime.now().date()

    polar_sleep_duration_json = []
    polar_sleep_score_json = []
    polar_sleep_end_date = current_day
    polar_recharge_hr_json = []
    polar_recharge_hrv_json = []
    polar_recharge_end_date = current_day
    oura_sleep_duration_json = []
    oura_sleep_score_json = []
    oura_sleep_end_date = current_day
    oura_recharge_hr_json = []
    oura_recharge_hrv_json = []

    polar_sleep_df = tr.polar_sleep_to_df(user_id)
    if not polar_sleep_df.empty:
        polar_sleep_duration_json = tr.sleep_duration_to_json(polar_sleep_df)
        polar_sleep_score_json = tr.sleep_score_to_json(polar_sleep_df)
        polar_sleep_end_date = datetime.strptime(polar_sleep_df['date'].iloc[-1],'%Y-%m-%d')

    polar_recharge_df = tr.polar_recharge_to_df(user_id)
    if not polar_recharge_df.empty:
        polar_recharge_hr_json = tr.recharge_hr_to_json(polar_recharge_df)
        polar_recharge_hrv_json = tr.recharge_hrv_to_json(polar_recharge_df)
        polar_recharge_end_date = datetime.strptime(polar_recharge_df['date'].iloc[-1],'%Y-%m-%d')

    oura_sleep_df = tr.oura_sleep_to_df(user_id)
    if not oura_sleep_df.empty:
        oura_sleep_duration_json = tr.sleep_duration_to_json(oura_sleep_df)
        oura_sleep_score_json = tr.sleep_score_to_json(oura_sleep_df)
        oura_sleep_end_date = datetime.strptime(oura_sleep_df['date'].iloc[-1],'%Y-%m-%d')
        oura_recharge_hr_json = tr.recharge_hr_to_json(oura_sleep_df)
        oura_recharge_hrv_json = tr.recharge_hrv_to_json(oura_sleep_df)

    
    end_date = max(polar_sleep_end_date, polar_recharge_end_date, oura_sleep_end_date)
    start_date = datetime.strftime(end_date - timedelta(30), '%d.%m.%Y')
    end_date = datetime.strftime(end_date, '%d.%m.%Y')

    return render(request, 'recovery.html', 
        context = {
            'start_date': start_date,
            'end_date': end_date,
            'polar_sleep_duration_json': polar_sleep_duration_json,
            'polar_sleep_score_json': polar_sleep_score_json,
            'polar_recharge_hr_json': polar_recharge_hr_json,
            'polar_recharge_hrv_json': polar_recharge_hrv_json,
            'oura_sleep_duration_json':oura_sleep_duration_json,
            'oura_sleep_score_json': oura_sleep_score_json,
            'oura_recharge_hr_json': oura_recharge_hr_json,
            'oura_recharge_hrv_json': oura_recharge_hrv_json
        })


@login_required
def settings_view(request):
    """ 
    Settings page 
    """
    user = request.user

    SeasonsFormset = inlineformset_factory(User, Kausi, form=KausiForm, extra=1, can_delete=True)
    ZonesFormset = inlineformset_factory(User, Tehoalue, form=TehoalueForm, extra=1, can_delete=True)
    SportsFormset = inlineformset_factory(User, Laji, form=LajiForm, extra=1, can_delete=True)

    zones_required_fields = utils.get_required_fields(Tehoalue)
    seasons_required_fields = utils.get_required_fields(Kausi)
    sports_required_fields = utils.get_required_fields(Laji)
    
    user_form = UserForm(instance=user)
    pw_form = PwChangeForm(user=user)
    seasons_formset = SeasonsFormset(instance=user)
    zones_formset = ZonesFormset(instance=user)
    sports_formset = SportsFormset(instance=user)

    if request.method == 'GET':
        page = request.GET.get('page','')
        if page not in ['profile','pw_reset','seasons','sports','zones']:
            page = 'profile'
    
    if request.method == 'POST':
        if 'profile_save' in request.POST:
            page = 'profile'
            user_form = UserForm(request.POST, instance=user)
            if user_form.is_valid():
                user_form.save()
                messages.add_message(request, messages.SUCCESS, 'Profiili tallennettu.')
                return redirect('settings')

        if 'pw_save' in request.POST:
            page = 'pw_reset'
            pw_form = PwChangeForm(data=request.POST, user=user)
            if pw_form.is_valid():
                pw_form.save()
                update_session_auth_hash(request, pw_form.user)
                messages.add_message(request, messages.SUCCESS, 'Salasana vaihdettu.')
                return redirect('settings')

        if 'sports_save' in request.POST:
            page = 'sports'
            sports_formset = SportsFormset(request.POST, request.FILES, instance=user)
            if sports_formset.is_valid() and sports_formset.has_changed():
                try:
                    sports_formset.save()
                    messages.add_message(request, messages.SUCCESS, 'Muutokset tallennettu.')
                    return redirect(reverse('settings') + '?page=' + page)
                except ProtectedError:
                    messages.add_message(request, messages.ERROR, 'Lajia ei voida poistaa, koska siihen on liitetty harjoituksia.')

        if 'zones_save' in request.POST:
            page = 'zones'
            zones_formset = ZonesFormset(request.POST, request.FILES, instance=user)
            if zones_formset.is_valid() and zones_formset.has_changed():
                try:
                    zones_formset.save()
                    messages.add_message(request, messages.SUCCESS, 'Muutokset tallennettu.')
                    return redirect(reverse('settings') + '?page=' + page)
                except ProtectedError:
                    messages.add_message(request, messages.ERROR, 'Tehoaluetta ei voida poistaa, koska siihen on liitetty harjoituksia.')

        if 'seasons_save' in request.POST:
            page = 'seasons'
            seasons_formset = SeasonsFormset(request.POST, request.FILES, instance=user)
            if seasons_formset.is_valid() and seasons_formset.has_changed():
                seasons_formset.save()
                messages.add_message(request, messages.SUCCESS, 'Muutokset tallennettu.')
                return redirect(reverse('settings') + '?page=' + page)

        if 'profile_del' in request.POST:
            u = User.objects.get(username = user)
            u.delete()
            messages.add_message(request, messages.SUCCESS, 'Profiili poistettu.') 
            return redirect('index')

    return render(request,'settings.html',
        context = {
            'user_form': user_form,
            'pw_form': pw_form,
            'sports_formset': sports_formset,
            'sports_required_fields': sports_required_fields,
            'seasons_formset': seasons_formset,
            'seasons_required_fields': seasons_required_fields,
            'zones_formset': zones_formset,
            'zones_required_fields': zones_required_fields,
            'page': page
            })


def register(request):
    """ User registration """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Käyttäjätili luotu.') 
            return redirect('accounts/login')
    else:
        form = RegistrationForm() 
    return render(request, 'register.html', 
        context = {'form': form})


@login_required
def trainings_data(request):
    table_columns = request.POST.getlist('columns[]')
    trainings_df = tr.trainings_to_df(request.user.id, table_columns)
    if trainings_df is None:
        trainings_list = []
    else:
        trainings_list = trainings_df.fillna('').values.tolist()
    return JsonResponse({'data': trainings_list})


@login_required
def training_details(request, pk):
    training_details = tr.zones_per_training_to_list(pk)
    route = Harjoitus.objects.get(id=pk,user_id=request.user.id).reitti
    if route.name:
        name = path.basename(route.name)
        url = route.url
    else:
        name = ''
        url = ''
    response = {
        'data': training_details, 
        'route': {'name': name, 'url': url}
    }
    return JsonResponse(response)


@login_required
def trainings_map_data(request):
    user_id = request.user.id
    data = json.loads(request.POST['data'])
    sport = data['sport']
    startdate = datetime.strptime(data['startdate'], '%d.%m.%Y')
    enddate = datetime.strptime(data['enddate'], '%d.%m.%Y')
    trainings = tr.trainings_with_route(user_id, startdate, enddate, sport, training_id=0, include_gpx=False)
    return JsonResponse({'data': trainings})
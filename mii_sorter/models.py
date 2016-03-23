import logging
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.db.models import Model, IntegerField, ForeignKey, CharField, BigIntegerField, FloatField, NullBooleanField, \
    DateTimeField, BooleanField, CASCADE
from django.utils.encoding import smart_unicode
from mii_interface.models import Report

logger = logging.getLogger(__name__)


class Movie(Model):
    title = CharField(max_length=100, db_index=True)
    year = IntegerField(null=True, default=1900, db_index=True)
    imdb_id = CharField(null=True, max_length=15)
    rating = FloatField(null=True)
    folder_path = CharField(max_length=400)
    file_size = BigIntegerField()
    seen = NullBooleanField(default=None, null=True)
    indexed = BooleanField(default=False)

    class Meta:
        index_together = [
            ['year', 'title']
        ]
        ordering = ['title']

    @property
    def abs_folder_path(self):
        try:
            return self.folder_path.format(destination_dir=settings.DESTINATION_FOLDER)
        except Exception:
            return self.folder_path

    def save(self, *args, **kwargs):
        if self.folder_path:
            self.folder_path = self.folder_path.replace(settings.DESTINATION_FOLDER, '{destination_dir}')
        if self.imdb_id and 't' in self.imdb_id:
            self.imdb_id.replace('t', '')
        return super(Movie, self).save(*args, **kwargs)


class Serie(Model):
    name = CharField(unique=True, max_length=50)

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Season(Model):
    number = IntegerField()
    serie = ForeignKey(Serie, CASCADE, related_name='seasons')

    class Meta:
        unique_together = [
            ['number', 'serie']
        ]
        ordering = ('serie__name', 'number')

    def __unicode__(self):
        return '%s S%s' % (self.serie.name, self.number)


class Episode(Model):
    number = IntegerField()
    season = ForeignKey(Season, CASCADE, related_name='episodes')
    file_path = CharField(max_length=400)
    file_size = BigIntegerField()

    class Meta:
        unique_together = [
            ['number', 'season']
        ]
        ordering = ('season__serie__name', 'season__number', 'number')

    def __unicode__(self):
        return '%s S%sE%s' % (self.season.serie.name, self.season.number, self.number)

    @property
    def abs_file_path(self):
        try:
            return self.file_path.format(destination_dir=settings.DESTINATION_FOLDER)
        except Exception:
            return self.file_path

    def save(self, *args, **kwargs):
        if self.file_path:
            self.file_path = self.file_path.replace(settings.DESTINATION_FOLDER, '{destination_dir}')
        return super(Episode, self).save(*args, **kwargs)


class WhatsNew(Model):
    date = DateTimeField(default=timezone.now)
    name = CharField(unique=True, max_length=70)
    path = CharField(max_length=400)

    class Meta:
        ordering = ['date']

    def get_displayable_date(self):
        today = timezone.now()
        day_delta = (today - self.date).days
        if day_delta == 0:
            return 'Today'
        elif day_delta == 1:
            return 'Yesterday'
        elif day_delta >= 30:
            return '%s month(s) ago' % (day_delta // 30)
        elif day_delta >= 7:
            return '%s week(s) ago' % (day_delta // 7)
        else:
            return '%s day(s) ago' % day_delta


class RegexRenaming(Model):
    old = CharField(max_length=255)
    new = CharField(max_length=255)


def get_serie_episode(name, season, episode):
    """
    Look for the same episode in the db, return the file_path of the existing one if any.
    :param string name: string
    :param int season: integer
    :param int episode: integer
    :return tuple: Tuple containing the path is serie is found (Boolean, String)
    """
    try:
        logger.info(u'Querying serie table with name=%s, season=%s and episode=%s' % (name, season, episode))
        episode = Episode.objects.get(season__number=season, number=episode, season__serie__name=name)
        if episode:
            return True, episode
    except ObjectDoesNotExist as e:
        logger.info(u'Found nothing %s' % repr(e))
        return False, None


def get_serie_season(name, season):
    """
    Look for the same season in the db, returns a boolean
    :param string name: string
    :param season: Season number in str or int
    :return bool:
    """
    try:
        logger.info(u'Querying serie table with name=%s and season=%s' % (name, season))
        season = Season.objects.get(number=season, serie__name=name)
        if season:
            return True
    except ObjectDoesNotExist as e:
        logger.info(u'Found nothing %s' % repr(e))
        return False


def insert_serie_episode(serie_name, serie_season, episode_number, serie_path, size):
    """
    Insert a serie into the sql database following Serie model.
    :param string serie_name: Name of the serie
    :param int serie_season: Season number
    :param int episode_number: Episode number
    :param string serie_path: Path of the file
    :rtype Episode: Episode of the serie
    """

    serie, created = Serie.objects.get_or_create(name=serie_name)

    season, created = Season.objects.get_or_create(number=serie_season, serie=serie)

    episode, created = Episode.objects.get_or_create(number=episode_number, season=season, file_path=serie_path,
                                                     file_size=size)

    # Add the serie to the what's new folder
    wn, created = WhatsNew.objects.get_or_create(
        name='%s S%sE%s' % (serie_name, serie_season, episode_number),
        date=timezone.now(),
        path=serie_path)
    return episode


def get_movie(title, year=None):
    """
    Look for the same movie in the db, return the file_path of the existing one if any.
    :param string title: string
    :param int year: integer
    :return tuple: Tuple containing the path is movie is found (Boolean, String)
    :rtype (bool, Movie):
    """
    try:
        logger.info(u'Querying movie table with name=%s and year=%s' % (title, year))
        if year:
            movie = Movie.objects.get(title=title, year=year)
        else:
            movie = Movie.objects.get(title=title)
        logger.info(u'Found movie')
        return True, movie
    except ObjectDoesNotExist as e:
        logger.info(u'Found nothing %s' % repr(e))
        return False, None


def insert_movie(title, year, path, size):
    """
    Insert a movie into the sql database following Movie model.
    :param string title: Title of the movie
    :param int year: Year of the movie
    :param string path: Path of the movie file
    :return Movie: Movie instance to be modified with additional data
    :rtype Movie: Movie type
    """
    movie, created = Movie.objects.get_or_create(title=title, year=year, folder_path=path, file_size=size)

    # Add the movie to the what's new folder
    wn, created = WhatsNew.objects.get_or_create(name='%s (%s)' % (title, year), date=timezone.now(), path=path)
    return movie


def insert_report(report_html, report_type=''):
    Report.objects.create(report_type=report_type, report_html=smart_unicode(report_html))
